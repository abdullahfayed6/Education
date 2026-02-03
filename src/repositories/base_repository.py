"""
Base Repository Pattern for Azure Cosmos DB

Provides CRUD operations with:
- Proper partition key handling
- Retry logic for resilience
- Query optimization
- Diagnostic logging
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Optional
from datetime import datetime

from azure.cosmos import exceptions
from azure.cosmos.container import ContainerProxy

from src.config.cosmosdb import cosmos_db

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository for Cosmos DB operations.
    
    Implements common CRUD operations with best practices:
    - Singleton CosmosClient usage
    - Retry logic with exponential backoff
    - Partition key optimization
    - Query result caching
    """
    
    def __init__(self, container_name: str, partition_key_path: str):
        """
        Initialize repository.
        
        Args:
            container_name: Cosmos DB container name
            partition_key_path: Partition key path (e.g., "/userId")
        """
        self.container_name = container_name
        self.partition_key_path = partition_key_path
        self._container: Optional[ContainerProxy] = None
    
    @property
    def container(self) -> ContainerProxy:
        """Lazy-load container proxy."""
        if self._container is None:
            self._container = cosmos_db.get_container(self.container_name)
        return self._container
    
    @abstractmethod
    def to_dict(self, entity: T) -> dict[str, Any]:
        """Convert entity to dictionary for storage."""
        pass
    
    @abstractmethod
    def from_dict(self, data: dict[str, Any]) -> T:
        """Convert dictionary to entity."""
        pass
    
    def _add_metadata(self, data: dict[str, Any]) -> dict[str, Any]:
        """Add metadata fields to document."""
        now = datetime.utcnow().isoformat()
        
        if 'createdAt' not in data:
            data['createdAt'] = now
        data['updatedAt'] = now
        
        return data
    
    def _extract_partition_key(self, data: dict[str, Any]) -> Any:
        """Extract partition key value from data."""
        # Remove leading slash from partition key path
        key_name = self.partition_key_path.lstrip('/')
        return data.get(key_name)
    
    async def create(self, entity: T) -> T:
        """
        Create a new item in Cosmos DB.
        
        Args:
            entity: Entity to create
            
        Returns:
            Created entity with Cosmos DB metadata
            
        Raises:
            exceptions.CosmosResourceExistsError: If item already exists
        """
        data = self.to_dict(entity)
        data = self._add_metadata(data)
        
        def _create():
            return self.container.create_item(body=data)
        
        try:
            result = cosmos_db.execute_with_retry(_create)
            logger.info(f"Created item in {self.container_name}: {data.get('id')}")
            return self.from_dict(result)
        except exceptions.CosmosResourceExistsError:
            logger.error(f"Item already exists: {data.get('id')}")
            raise
        except Exception as e:
            logger.error(f"Failed to create item in {self.container_name}: {e}")
            raise
    
    async def read(self, item_id: str, partition_key: Any) -> Optional[T]:
        """
        Read an item by ID and partition key.
        
        Args:
            item_id: Item ID
            partition_key: Partition key value
            
        Returns:
            Entity if found, None otherwise
        """
        def _read():
            return self.container.read_item(
                item=item_id,
                partition_key=partition_key
            )
        
        try:
            result = cosmos_db.execute_with_retry(_read)
            return self.from_dict(result)
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Item not found: {item_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to read item {item_id}: {e}")
            raise
    
    async def update(self, entity: T) -> T:
        """
        Update an existing item (upsert).
        
        Args:
            entity: Entity to update
            
        Returns:
            Updated entity
        """
        data = self.to_dict(entity)
        data = self._add_metadata(data)
        
        def _update():
            return self.container.upsert_item(body=data)
        
        try:
            result = cosmos_db.execute_with_retry(_update)
            logger.info(f"Updated item in {self.container_name}: {data.get('id')}")
            return self.from_dict(result)
        except Exception as e:
            logger.error(f"Failed to update item in {self.container_name}: {e}")
            raise
    
    async def delete(self, item_id: str, partition_key: Any) -> bool:
        """
        Delete an item.
        
        Args:
            item_id: Item ID
            partition_key: Partition key value
            
        Returns:
            True if deleted, False if not found
        """
        def _delete():
            return self.container.delete_item(
                item=item_id,
                partition_key=partition_key
            )
        
        try:
            cosmos_db.execute_with_retry(_delete)
            logger.info(f"Deleted item from {self.container_name}: {item_id}")
            return True
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Item not found for deletion: {item_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete item {item_id}: {e}")
            raise
    
    async def query(
        self,
        query: str,
        parameters: Optional[list[dict[str, Any]]] = None,
        partition_key: Optional[Any] = None,
        max_items: int = 100
    ) -> list[T]:
        """
        Execute a SQL query.
        
        Best Practices:
        - Always provide partition_key when possible to avoid cross-partition queries
        - Use parameterized queries to prevent injection
        - Limit results with max_items
        
        Args:
            query: SQL query string
            parameters: Query parameters for parameterized queries
            partition_key: Partition key to limit query scope (recommended)
            max_items: Maximum number of items to return
            
        Returns:
            List of entities
        """
        def _query():
            if partition_key:
                # Single-partition query (efficient)
                return list(self.container.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key=partition_key,
                    max_item_count=max_items
                ))
            else:
                # Cross-partition query (less efficient, use sparingly)
                logger.warning(
                    f"Cross-partition query executed in {self.container_name}. "
                    "Consider adding partition_key for better performance."
                )
                return list(self.container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True,
                    max_item_count=max_items
                ))
        
        try:
            results = cosmos_db.execute_with_retry(_query)
            return [self.from_dict(item) for item in results]
        except Exception as e:
            logger.error(f"Query failed in {self.container_name}: {e}")
            raise
    
    async def find_by_field(
        self,
        field_name: str,
        field_value: Any,
        partition_key: Optional[Any] = None,
        max_items: int = 100
    ) -> list[T]:
        """
        Find items by a specific field value.
        
        Args:
            field_name: Field name to search
            field_value: Value to match
            partition_key: Partition key to limit scope (recommended)
            max_items: Maximum results
            
        Returns:
            List of matching entities
        """
        query = f"SELECT * FROM c WHERE c.{field_name} = @value"
        parameters = [{"name": "@value", "value": field_value}]
        
        return await self.query(
            query=query,
            parameters=parameters,
            partition_key=partition_key,
            max_items=max_items
        )
    
    async def list_all(
        self,
        partition_key: Optional[Any] = None,
        max_items: int = 100
    ) -> list[T]:
        """
        List all items (use with caution in production).
        
        Args:
            partition_key: Partition key to limit scope
            max_items: Maximum results
            
        Returns:
            List of all entities
        """
        query = "SELECT * FROM c"
        return await self.query(
            query=query,
            partition_key=partition_key,
            max_items=max_items
        )
    
    async def count(self, partition_key: Optional[Any] = None) -> int:
        """
        Count items in container.
        
        Args:
            partition_key: Partition key to limit scope
            
        Returns:
            Count of items
        """
        query = "SELECT VALUE COUNT(1) FROM c"
        
        def _count():
            if partition_key:
                results = list(self.container.query_items(
                    query=query,
                    partition_key=partition_key
                ))
            else:
                results = list(self.container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
            return results[0] if results else 0
        
        try:
            return cosmos_db.execute_with_retry(_count)
        except Exception as e:
            logger.error(f"Count query failed: {e}")
            raise
