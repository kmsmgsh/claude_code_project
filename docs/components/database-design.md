# Database Design & Implementation

This document details the database architecture and implementation decisions for the MLOps Model Registry system.

## 🎯 Design Philosophy

### Why Raw SQL?

We chose **raw SQL over ORM** for several key reasons:

1. **Simplicity**: Direct, transparent database operations
2. **Performance**: No abstraction layer overhead
3. **Control**: Full access to database-specific features
4. **Learning**: Easy to understand and debug SQL queries
5. **Portability**: Standard SQL works across database systems

### Why Table Prefixes?

We use **table prefixes** (`mr_*` for model registry) instead of separate databases:

- ✅ **Single Database**: Easier management and backups
- ✅ **Cross-Module Joins**: Can relate data across components
- ✅ **Namespace Clarity**: Clear component ownership
- ✅ **Migration Friendly**: Can evolve to schemas later

## 🗄️ Database Schema

### Core Tables

#### `mr_models` - Model Names
```sql
CREATE TABLE mr_models (
    id INTEGER PRIMARY KEY,           -- Auto-incrementing model ID
    name TEXT NOT NULL UNIQUE,        -- Model name (e.g., "linear_predictor")
    description TEXT,                 -- Optional model description
    created_at TEXT NOT NULL,         -- ISO timestamp when first created
    updated_at TEXT NOT NULL          -- ISO timestamp when last modified
);
```

#### `mr_model_versions` - Model Versions
```sql
CREATE TABLE mr_model_versions (
    id INTEGER PRIMARY KEY,           -- Auto-incrementing version ID
    model_id INTEGER NOT NULL,        -- Foreign key to mr_models.id
    version TEXT NOT NULL,            -- Version string (1, 2, 3, ...)
    description TEXT,                 -- Version-specific description
    storage_path TEXT NOT NULL,       -- Path to model file
    file_size_bytes INTEGER DEFAULT 0, -- File size in bytes
    created_at TEXT NOT NULL,         -- ISO timestamp when version created
    
    FOREIGN KEY (model_id) REFERENCES mr_models(id) ON DELETE CASCADE,
    UNIQUE(model_id, version)         -- One version per model
);
```

#### `mr_model_tags` - Key-Value Tags
```sql
CREATE TABLE mr_model_tags (
    id INTEGER PRIMARY KEY,           -- Auto-incrementing tag ID
    model_version_id INTEGER NOT NULL, -- Foreign key to mr_model_versions.id
    tag_key TEXT NOT NULL,            -- Tag key (e.g., "type", "author")
    tag_value TEXT,                   -- Tag value (e.g., "regression", "team_a")
    
    FOREIGN KEY (model_version_id) REFERENCES mr_model_versions(id) ON DELETE CASCADE,
    UNIQUE(model_version_id, tag_key) -- One key per model version
);
```

### Performance Indexes

```sql
-- Fast model name lookups
CREATE INDEX idx_mr_models_name ON mr_models(name);

-- Fast version queries by model
CREATE INDEX idx_mr_model_versions_model_id ON mr_model_versions(model_id);
CREATE INDEX idx_mr_model_versions_version ON mr_model_versions(version);

-- Fast tag-based searches
CREATE INDEX idx_mr_model_tags_key ON mr_model_tags(tag_key);
CREATE INDEX idx_mr_model_tags_key_value ON mr_model_tags(tag_key, tag_value);
```

## 🔄 Migration System

### Schema Versioning
```sql
-- Migration tracking table
CREATE TABLE schema_migrations (
    version TEXT PRIMARY KEY,        -- Migration version (e.g., "001", "002")
    applied_at TEXT NOT NULL         -- When migration was applied
);
```

### Migration Files Structure
```
model_management/database/migrations/
├── 001_create_model_registry.sql   -- Initial schema
├── 002_add_performance_metrics.sql -- Future: performance tracking
└── 003_add_model_lineage.sql       -- Future: model relationships
```

### Migration Example
```sql
-- migrations/002_add_performance_metrics.sql
ALTER TABLE mr_model_versions ADD COLUMN accuracy REAL;
ALTER TABLE mr_model_versions ADD COLUMN f1_score REAL;

CREATE INDEX idx_mr_model_versions_accuracy ON mr_model_versions(accuracy);

INSERT OR IGNORE INTO schema_migrations (version, applied_at) 
VALUES ('002', datetime('now'));
```

## 📊 Database Operations

### Common Queries

#### Get All Models with Latest Version
```sql
SELECT 
    m.name,
    mv.version,
    mv.description,
    mv.created_at,
    mv.file_size_bytes
FROM mr_models m
JOIN mr_model_versions mv ON m.id = mv.model_id
WHERE mv.id = (
    SELECT MAX(id) 
    FROM mr_model_versions mv2 
    WHERE mv2.model_id = m.id
)
ORDER BY m.name;
```

#### Get Model Statistics
```sql
SELECT 
    COUNT(DISTINCT m.id) as total_models,
    COUNT(mv.id) as total_versions,
    SUM(mv.file_size_bytes) as total_size_bytes,
    AVG(mv.file_size_bytes) as avg_size_bytes
FROM mr_models m
LEFT JOIN mr_model_versions mv ON m.id = mv.model_id;
```

#### Find Models by Tag
```sql
SELECT DISTINCT
    m.name,
    mv.version,
    mv.description,
    mt.tag_value
FROM mr_models m
JOIN mr_model_versions mv ON m.id = mv.model_id
JOIN mr_model_tags mt ON mv.id = mt.model_version_id
WHERE mt.tag_key = 'type' AND mt.tag_value = 'regression'
ORDER BY m.name, CAST(mv.version AS INTEGER);
```

## 🚀 Implementation Details

### Connection Management
```python
@contextmanager
def get_connection(self):
    """Context manager for database connections"""
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row  # Enable column access by name
    try:
        yield conn
        conn.commit()  # Auto-commit on success
    except Exception:
        conn.rollback()  # Auto-rollback on error
        raise
    finally:
        conn.close()
```

### Transaction Safety
```python
def save_model_metadata(self, model_info: Dict) -> None:
    """Save model with full transaction safety"""
    with self.db_manager.get_connection() as conn:
        cursor = conn.cursor()
        
        # All operations in single transaction
        model_id = self._get_or_create_model(cursor, model_info['name'])
        cursor.execute("INSERT INTO mr_model_versions ...")
        version_id = cursor.lastrowid
        
        # Insert tags
        for tag_key, tag_value in model_info.get('tags', {}).items():
            cursor.execute("INSERT INTO mr_model_tags ...")
        
        # Automatic commit via context manager
```

### Error Handling
```python
try:
    registry.save_model(model, "test_model")
except sqlite3.IntegrityError as e:
    print(f"Constraint violation: {e}")
except sqlite3.OperationalError as e:
    print(f"Database operation failed: {e}")
```

## 🔧 Database Backends

### Current: SQLite
- **File-based**: Single `.db` file
- **Zero-config**: No server setup required
- **ACID compliance**: Full transaction support
- **Cross-platform**: Works everywhere Python does

### Future: PostgreSQL
```python
# Same schema, different connection
class PostgreSQLMetadataBackend(MetadataBackend):
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        # Use psycopg2 instead of sqlite3
```

### Future: MySQL  
```python
# Same schema, different connection
class MySQLMetadataBackend(MetadataBackend):
    def __init__(self, connection_string: str):
        self.conn_string = connection_string
        # Use mysql-connector-python
```

## 🎯 Benefits Achieved

### Development Benefits
- ✅ **Rapid Prototyping**: SQLite requires no setup
- ✅ **Easy Testing**: In-memory databases for unit tests
- ✅ **Simple Deployment**: Single file, no server required
- ✅ **Version Control**: Database file can be committed (for dev)

### Production Benefits  
- ✅ **ACID Compliance**: Full transaction safety
- ✅ **Concurrent Access**: Multiple processes can read/write
- ✅ **Query Performance**: Indexed searches are fast
- ✅ **Data Integrity**: Foreign key constraints prevent corruption

### Migration Benefits
- ✅ **Schema Evolution**: Versioned migrations
- ✅ **Database Agnostic**: Same schema works on PostgreSQL/MySQL
- ✅ **Zero Downtime**: Can migrate data while system runs
- ✅ **Rollback Support**: Can revert schema changes if needed

## 📈 Performance Characteristics

### SQLite Limits (Sufficient for Most Use Cases)
- **Database Size**: 281 TB theoretical, 128 GB practical
- **Table Size**: 256 TB  
- **Row Size**: 1 GB
- **Concurrent Readers**: Unlimited
- **Concurrent Writers**: 1 at a time

### When to Consider PostgreSQL
- **High Write Concurrency**: Many simultaneous model saves
- **Advanced Analytics**: Complex queries and aggregations  
- **Multi-User Access**: Many teams accessing simultaneously
- **Horizontal Scaling**: Multiple database servers

## 🔍 Monitoring & Maintenance

### Database Size Monitoring
```python
import os

def get_database_stats(db_path: str) -> dict:
    size_bytes = os.path.getsize(db_path)
    size_mb = size_bytes / (1024 * 1024)
    
    return {
        "file_path": db_path,
        "size_bytes": size_bytes,
        "size_mb": round(size_mb, 2)
    }
```

### Performance Monitoring
```sql
-- Check index usage (SQLite)
SELECT name, tbl_name FROM sqlite_master WHERE type = 'index';

-- Analyze query performance
EXPLAIN QUERY PLAN SELECT * FROM mr_models WHERE name = 'linear_predictor';
```

This database design provides a solid foundation for the MLOps Model Registry that can scale from development to production while maintaining simplicity and performance.