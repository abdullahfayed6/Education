"""
Azure Cosmos DB Configuration and Client Management

Implements singleton pattern for CosmosClient with:
- Connection retry logic for 429 errors
- Diagnostic logging for performance monitoring
- Support for both cloud and emulator
- Proper resource management
"""

from __future__ import annotations

import logging
import time
from typing import Optional
from threading import Lock

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.database import DatabaseProxy
from azure.cosmos.container import ContainerProxy

from src.config.settings import settings

logger = logging.getLogger(__name__)


class CosmosDBManager:
    """Singleton manager for Azure Cosmos DB client with retry logic and diagnostics."""
    
    _instance: Optional[CosmosDBManager] = None
    _lock: Lock = Lock()
    _client: Optional[CosmosClient] = None
    
    def __new__(cls) -> CosmosDBManager:
        """Ensure only one instance of CosmosDBManager exists (Singleton)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the manager (only once)."""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Cosmos DB client with proper configuration."""
        try:
            if settings.cosmos_use_emulator:
                # Use local emulator
                logger.info("Connecting to Azure Cosmos DB Emulator")
                self._client = CosmosClient(
                    url=settings.cosmos_emulator_url,
                    credential=settings.cosmos_emulator_key,
                    connection_verify=False  # Emulator uses self-signed cert
                )
            else:
                # Use cloud instance
                logger.info(f"Connecting to Azure Cosmos DB: {settings.cosmos_endpoint}")
                self._client = CosmosClient(
                    url=settings.cosmos_endpoint,
                    credential=settings.cosmos_key,
                    preferred_locations=settings.cosmos_preferred_regions,
                    enable_diagnostics_logging=True
                )
            
            logger.info("✓ Cosmos DB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cosmos DB client: {e}")
            raise
    
    @property
    def client(self) -> CosmosClient:
        """Get the Cosmos DB client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def get_database(self, database_name: str | None = None) -> DatabaseProxy:
        """
        Get database proxy.
        
        Args:
            database_name: Database name (uses default from settings if None)
            
        Returns:
            DatabaseProxy instance
        """
        db_name = database_name or settings.cosmos_database_name
        return self.client.get_database_client(db_name)
    
    def get_container(
        self, 
        container_name: str,
        database_name: str | None = None
    ) -> ContainerProxy:
        """
        Get container proxy.
        
        Args:
            container_name: Container name
            database_name: Database name (uses default from settings if None)
            
        Returns:
            ContainerProxy instance
        """
        database = self.get_database(database_name)
        return database.get_container_client(container_name)
    
    def create_database_if_not_exists(
        self, 
        database_name: str | None = None
    ) -> DatabaseProxy:
        """
        Create database if it doesn't exist.
        
        Args:
            database_name: Database name (uses default from settings if None)
            
        Returns:
            DatabaseProxy instance
        """
        db_name = database_name or settings.cosmos_database_name
        try:
            database = self.client.create_database_if_not_exists(id=db_name)
            logger.info(f"✓ Database '{db_name}' ready")
            return database
        except Exception as e:
            logger.error(f"Failed to create database '{db_name}': {e}")
            raise
    
    def create_container_if_not_exists(
        self,
        container_name: str,
        partition_key_path: str,
        database_name: str | None = None,
        hierarchical_partition_key_paths: list[str] | None = None,
        default_ttl: int | None = None
    ) -> ContainerProxy:
        """
        Create container if it doesn't exist.
        
        Args:
            container_name: Container name
            partition_key_path: Partition key path (e.g., "/userId")
            database_name: Database name (uses default if None)
            hierarchical_partition_key_paths: For hierarchical partition keys (HPK)
            default_ttl: Time-to-live in seconds (None = no TTL)
            
        Returns:
            ContainerProxy instance
        """
        database = self.get_database(database_name)
        
        try:
            # Configure partition key
            if hierarchical_partition_key_paths:
                # Use Hierarchical Partition Keys for better distribution
                partition_key = PartitionKey(
                    path=hierarchical_partition_key_paths,
                    kind='MultiHash'
                )
                logger.info(f"Using Hierarchical Partition Key: {hierarchical_partition_key_paths}")
            else:
                partition_key = PartitionKey(path=partition_key_path)
            
            # Configure container settings
            container_properties = {
                'id': container_name,
                'partition_key': partition_key
            }
            
            if default_ttl is not None:
                container_properties['default_ttl'] = default_ttl
            
            container = database.create_container_if_not_exists(
                id=container_name,
                partition_key=partition_key,
                default_ttl=default_ttl
            )
            
            logger.info(f"✓ Container '{container_name}' ready")
            return container
            
        except Exception as e:
            logger.error(f"Failed to create container '{container_name}': {e}")
            raise
    
    def execute_with_retry(
        self,
        operation,
        max_retries: int = 3,
        initial_delay: float = 1.0
    ):
        """
        Execute Cosmos DB operation with exponential backoff retry.
        
        Handles 429 (Rate Limited) errors automatically.
        Logs diagnostic information for performance monitoring.
        
        Args:
            operation: Callable operation to execute
            max_retries: Maximum retry attempts
            initial_delay: Initial delay in seconds
            
        Returns:
            Operation result
            
        Raises:
            Last exception if all retries fail
        """
        delay = initial_delay
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                result = operation()
                elapsed_time = time.time() - start_time
                
                # Log if latency exceeds threshold
                if elapsed_time > settings.cosmos_latency_threshold_ms / 1000:
                    logger.warning(
                        f"High latency detected: {elapsed_time*1000:.2f}ms "
                        f"(threshold: {settings.cosmos_latency_threshold_ms}ms)"
                    )
                
                return result
                
            except exceptions.CosmosHttpResponseError as e:
                last_exception = e
                
                # Log diagnostic information
                logger.warning(
                    f"Cosmos DB error [Attempt {attempt + 1}/{max_retries + 1}]: "
                    f"Status {e.status_code} - {e.message}"
                )
                
                # Handle rate limiting (429)
                if e.status_code == 429:
                    if attempt < max_retries:
                        retry_after = e.headers.get('x-ms-retry-after-ms', delay * 1000)
                        wait_time = float(retry_after) / 1000 if retry_after else delay
                        
                        logger.info(f"Rate limited. Retrying after {wait_time:.2f}s...")
                        time.sleep(wait_time)
                        delay *= 2  # Exponential backoff
                        continue
                
                # Re-raise non-retryable errors
                raise
                
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in Cosmos DB operation: {e}")
                raise
        
        # All retries exhausted
        logger.error(f"Operation failed after {max_retries} retries")
        raise last_exception
    
    def close(self) -> None:
        """Close Cosmos DB client connection."""
        if self._client:
            try:
                # CosmosClient doesn't have explicit close in newer SDKs
                # Connection pooling is managed automatically
                logger.info("Cosmos DB client closed")
                self._client = None
            except Exception as e:
                logger.error(f"Error closing Cosmos DB client: {e}")


# Singleton instance
cosmos_db = CosmosDBManager()


def get_cosmos_db() -> CosmosDBManager:
    """Dependency injection helper for FastAPI."""
    return cosmos_db
