# CareerForgeAI Initialization Script
# Initializes Azure Cosmos DB database and containers

from src.config.cosmosdb import cosmos_db
from src.config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_cosmos_db():
    """Initialize Cosmos DB database and containers."""
    
    try:
        logger.info(f"🔄 Initializing database: {settings.cosmos_database_name}")
        logger.info(f"📍 Environment: {settings.environment.value}")
        
        if settings.cosmos_use_emulator:
            logger.info(f"🖥️  Using Cosmos DB Emulator: {settings.cosmos_emulator_url}")
        else:
            logger.info(f"☁️  Using Cloud Cosmos DB: {settings.cosmos_endpoint}")
        
        # Create database
        database = cosmos_db.create_database_if_not_exists()
        logger.info(f"✓ Database '{settings.cosmos_database_name}' ready")
        
        # Create Users container (single partition key)
        logger.info(f"Creating container: {settings.container_users}")
        cosmos_db.create_container_if_not_exists(
            container_name=settings.container_users,
            partition_key_path="/userId"
        )
        logger.info(f"✓ Container '{settings.container_users}' ready")
        
        # Create Sessions container (hierarchical partition key with TTL)
        logger.info(f"Creating container: {settings.container_sessions} (with TTL)")
        cosmos_db.create_container_if_not_exists(
            container_name=settings.container_sessions,
            partition_key_path="/userId",
            hierarchical_partition_key_paths=["/userId", "/sessionId"],
            default_ttl=2592000  # 30 days auto-cleanup
        )
        logger.info(f"✓ Container '{settings.container_sessions}' ready with 30-day TTL")
        
        # Create Interviews container
        logger.info(f"Creating container: {settings.container_interviews}")
        cosmos_db.create_container_if_not_exists(
            container_name=settings.container_interviews,
            partition_key_path="/userId"
        )
        logger.info(f"✓ Container '{settings.container_interviews}' ready")
        
        # Create Profiles container
        logger.info(f"Creating container: {settings.container_profiles}")
        cosmos_db.create_container_if_not_exists(
            container_name=settings.container_profiles,
            partition_key_path="/userId"
        )
        logger.info(f"✓ Container '{settings.container_profiles}' ready")
        
        # Create Recommendations container
        logger.info(f"Creating container: {settings.container_recommendations}")
        cosmos_db.create_container_if_not_exists(
            container_name=settings.container_recommendations,
            partition_key_path="/userId"
        )
        logger.info(f"✓ Container '{settings.container_recommendations}' ready")
        
        logger.info("\n✅ Database initialization complete!")
        logger.info(f"\nℹ️  Database Name: {settings.cosmos_database_name}")
        logger.info(f"ℹ️  Total Containers: 5")
        logger.info(f"ℹ️  Partition Strategy: /userId (with HPK for sessions)")
        
        if settings.cosmos_use_emulator:
            logger.info(f"\n🌐 Access Cosmos DB Explorer:")
            logger.info(f"   URL: {settings.cosmos_emulator_url}/_explorer/index.html")
        
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    initialize_cosmos_db()
