# Azure Cosmos DB Setup Guide

## 📋 Table of Contents

1. [Local Development (Emulator)](#local-development-emulator)
2. [Cloud Setup (Azure)](#cloud-setup-azure)
3. [Container Creation](#container-creation)
4. [Index Configuration](#index-configuration)
5. [Monitoring & Diagnostics](#monitoring--diagnostics)

---

## 🖥️ Local Development (Emulator)

### Option 1: Docker (Recommended)

```bash
# Using docker-compose
docker-compose up cosmosdb

# Access Cosmos DB Explorer
# URL: https://localhost:8081/_explorer/index.html
# Key: C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

### Option 2: Windows Install

1. Download [Azure Cosmos DB Emulator](https://aka.ms/cosmosdb-emulator)
2. Install and run
3. Accept self-signed certificate

### Configuration

```env
# .env file
COSMOS_USE_EMULATOR=true
COSMOS_EMULATOR_URL=https://localhost:8081
COSMOS_EMULATOR_KEY=C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==
```

---

## ☁️ Cloud Setup (Azure)

### 1. Create Cosmos DB Account

#### Via Azure Portal
1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → "Azure Cosmos DB"
3. Choose **API**: NoSQL
4. Configure:
   - **Resource Group**: Create new or use existing
   - **Account Name**: careerforge-cosmos
   - **Location**: East US (or nearest region)
   - **Capacity Mode**: Serverless (for development) or Provisioned (for production)
   - **Geo-Redundancy**: Enabled (for production)
   - **Multi-region Writes**: Enabled (for production)

#### Via Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create \
  --name careerforge-rg \
  --location eastus

# Create Cosmos DB account
az cosmosdb create \
  --name careerforge-cosmos \
  --resource-group careerforge-rg \
  --default-consistency-level Session \
  --locations regionName=eastus failoverPriority=0 \
  --locations regionName=westus failoverPriority=1 \
  --enable-multiple-write-locations true

# Get connection string
az cosmosdb keys list \
  --name careerforge-cosmos \
  --resource-group careerforge-rg \
  --type connection-strings
```

### 2. Get Credentials

```bash
# Get endpoint and key
COSMOS_ENDPOINT=$(az cosmosdb show \
  --name careerforge-cosmos \
  --resource-group careerforge-rg \
  --query documentEndpoint -o tsv)

COSMOS_KEY=$(az cosmosdb keys list \
  --name careerforge-cosmos \
  --resource-group careerforge-rg \
  --query primaryMasterKey -o tsv)

echo "COSMOS_ENDPOINT=$COSMOS_ENDPOINT"
echo "COSMOS_KEY=$COSMOS_KEY"
```

### 3. Update .env File

```env
# Production .env
COSMOS_USE_EMULATOR=false
COSMOS_ENDPOINT=https://careerforge-cosmos.documents.azure.com:443/
COSMOS_KEY=your-primary-key-here
COSMOS_DATABASE_NAME=careerforge_db
COSMOS_PREFERRED_REGIONS=["East US", "West US"]
```

---

## 🗄️ Container Creation

### Automatic Initialization (Recommended)

Create initialization script:

```python
# scripts/init_cosmos_db.py
import asyncio
from src.config.cosmosdb import cosmos_db
from src.config.settings import settings


async def initialize_database():
    """Initialize Cosmos DB database and containers."""
    
    print(f"🔄 Initializing database: {settings.cosmos_database_name}")
    
    # Create database
    database = cosmos_db.create_database_if_not_exists()
    print(f"✓ Database ready")
    
    # Create Users container (single partition key)
    cosmos_db.create_container_if_not_exists(
        container_name=settings.container_users,
        partition_key_path="/userId"
    )
    print(f"✓ Container '{settings.container_users}' ready")
    
    # Create Sessions container (hierarchical partition key)
    cosmos_db.create_container_if_not_exists(
        container_name=settings.container_sessions,
        partition_key_path="/userId",
        hierarchical_partition_key_paths=["/userId", "/sessionId"],
        default_ttl=2592000  # 30 days auto-cleanup
    )
    print(f"✓ Container '{settings.container_sessions}' ready with TTL")
    
    # Create Interviews container
    cosmos_db.create_container_if_not_exists(
        container_name=settings.container_interviews,
        partition_key_path="/userId"
    )
    print(f"✓ Container '{settings.container_interviews}' ready")
    
    # Create Profiles container
    cosmos_db.create_container_if_not_exists(
        container_name=settings.container_profiles,
        partition_key_path="/userId"
    )
    print(f"✓ Container '{settings.container_profiles}' ready")
    
    # Create Recommendations container
    cosmos_db.create_container_if_not_exists(
        container_name=settings.container_recommendations,
        partition_key_path="/userId"
    )
    print(f"✓ Container '{settings.container_recommendations}' ready")
    
    print(f"\n✅ Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(initialize_database())
```

Run initialization:

```bash
python scripts/init_cosmos_db.py
```

### Manual Creation (Via Portal)

1. Open Cosmos DB account in Azure Portal
2. Go to "Data Explorer"
3. Click "New Container"
4. Configure:
   - **Database id**: careerforge_db (create new)
   - **Container id**: users
   - **Partition key**: /userId
   - **Throughput**: 400 RU/s (autoscale) or Serverless

---

## 🔍 Index Configuration

### Default Indexing Policy

Cosmos DB automatically indexes all properties. For optimization:

```json
{
  "indexingMode": "consistent",
  "automatic": true,
  "includedPaths": [
    {
      "path": "/*"
    }
  ],
  "excludedPaths": [
    {
      "path": "/messages/*"
    },
    {
      "path": "/_etag/?"
    }
  ],
  "compositeIndexes": [
    [
      {
        "path": "/userId",
        "order": "ascending"
      },
      {
        "path": "/createdAt",
        "order": "descending"
      }
    ]
  ]
}
```

### Apply Custom Indexing

```bash
# Via Azure CLI
az cosmosdb sql container update \
  --account-name careerforge-cosmos \
  --resource-group careerforge-rg \
  --database-name careerforge_db \
  --name sessions \
  --idx @indexing-policy.json
```

---

## 📊 Monitoring & Diagnostics

### 1. Enable Diagnostic Logging

```python
# Already configured in src/config/cosmosdb.py
client = CosmosClient(
    url=settings.cosmos_endpoint,
    credential=settings.cosmos_key,
    enable_diagnostics_logging=True  # ✓ Enabled
)
```

### 2. Monitor Metrics

Key metrics to watch:
- **Request Units (RUs)**: Track consumption
- **Latency**: P50, P95, P99 percentiles
- **Throttling**: 429 error rate
- **Storage**: Current size vs limit

### 3. Azure Monitor Integration

```bash
# Enable diagnostic settings
az monitor diagnostic-settings create \
  --name cosmos-diagnostics \
  --resource /subscriptions/{sub-id}/resourceGroups/careerforge-rg/providers/Microsoft.DocumentDB/databaseAccounts/careerforge-cosmos \
  --logs '[{"category": "DataPlaneRequests", "enabled": true}]' \
  --metrics '[{"category": "Requests", "enabled": true}]' \
  --workspace /subscriptions/{sub-id}/resourceGroups/careerforge-rg/providers/Microsoft.OperationalInsights/workspaces/careerforge-logs
```

### 4. Application Insights

```python
# Add to src/config/settings.py
app_insights_connection_string: Optional[str] = None

# Add to middleware
from opencensus.ext.azure.log_exporter import AzureLogHandler

handler = AzureLogHandler(
    connection_string=settings.app_insights_connection_string
)
logging.getLogger().addHandler(handler)
```

---

## 🛠️ Best Practices

### 1. Partition Key Selection ✓
- ✅ High cardinality (many unique values)
- ✅ Evenly distributed data
- ✅ Supports common query patterns
- ❌ Avoid low-cardinality keys (status, type)

### 2. Data Modeling ✓
- ✅ Embed related data accessed together
- ✅ Reference large or independently accessed data
- ✅ Monitor 2MB item size limit
- ✅ Use TTL for automatic cleanup

### 3. Query Optimization ✓
- ✅ Provide partition key in queries
- ✅ Use parameterized queries
- ✅ Limit result sets
- ❌ Avoid cross-partition queries

### 4. Performance ✓
- ✅ Use singleton CosmosClient
- ✅ Implement retry logic for 429s
- ✅ Enable connection pooling
- ✅ Monitor diagnostic logs

---

## 🚨 Troubleshooting

### Issue: Connection Failed

```
CosmosHttpResponseError: (Unauthorized) The input authorization token can't serve the request.
```

**Solution**:
1. Verify endpoint and key in .env
2. Check network connectivity
3. For emulator: Accept self-signed certificate

### Issue: Rate Limited (429)

```
CosmosHttpResponseError: (429) Request rate is large
```

**Solution**:
- Already handled with retry logic in `cosmosdb.py`
- Increase RU/s allocation
- Use autoscale throughput

### Issue: Cross-Partition Query Slow

```
WARNING: Cross-partition query executed
```

**Solution**:
- Add partition key to query
- Use hierarchical partition keys
- Consider data model changes

---

## 📚 Resources

- [Azure Cosmos DB Documentation](https://learn.microsoft.com/azure/cosmos-db/)
- [Best Practices](https://learn.microsoft.com/azure/cosmos-db/nosql/best-practice)
- [Partitioning Guide](https://learn.microsoft.com/azure/cosmos-db/partitioning-overview)
- [Python SDK Documentation](https://learn.microsoft.com/python/api/overview/azure/cosmos-readme)
- [Emulator Documentation](https://learn.microsoft.com/azure/cosmos-db/emulator)
