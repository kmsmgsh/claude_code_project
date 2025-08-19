# Migration Guide: From JSON to Database Backend

This guide shows how to migrate from the JSON metadata backend to the SQLite database backend, and how to prepare for future PostgreSQL/MySQL migrations.

## 🎯 Migration Scenarios

### Scenario 1: JSON → SQLite (Development)
Migrate existing JSON metadata to SQLite database for better performance and querying.

### Scenario 2: SQLite → PostgreSQL (Production)
Scale from SQLite to PostgreSQL for multi-user, high-concurrency environments.

### Scenario 3: Cross-Database Migration
Move between different database systems while preserving all data.

## 📋 Pre-Migration Checklist

### 1. Backup Existing Data
```bash
# Backup JSON metadata
cp models/registry.json models/registry.json.backup

# Backup model files
tar -czf models_backup.tar.gz models/
```

### 2. Verify Data Integrity
```python
from model_management import create_registry

# Test current registry
registry = create_registry("local")
models = registry.list_models()

print(f"Found {len(models)} models to migrate:")
for name, versions in models.items():
    print(f"  {name}: {len(versions)} versions")
```

## 🔄 Migration Procedures

### JSON to SQLite Migration

#### Step 1: Create Migration Script
```python
# migrate_json_to_sqlite.py
import json
import os
from model_management import create_registry

def migrate_json_to_sqlite(json_path: str, db_path: str, models_path: str):
    """Migrate from JSON to SQLite backend"""
    
    print("📊 Starting JSON to SQLite migration...")
    
    # 1. Load existing JSON data
    print("📥 Loading JSON metadata...")
    with open(json_path, 'r') as f:
        json_data = json.load(f)
    
    print(f"Found {len(json_data)} models in JSON")
    
    # 2. Create new SQLite registry
    print("🗄️ Creating SQLite registry...")
    sqlite_registry = create_registry("database", 
                                     path=models_path, 
                                     db_path=db_path)
    
    # 3. Migrate each model and version
    print("🔄 Migrating models...")
    total_versions = 0
    
    for model_name, versions in json_data.items():
        print(f"  Migrating {model_name}...")
        
        for version_info in versions:
            # Reconstruct model info in database format
            model_data = {
                'name': version_info['name'],
                'version': version_info['version'],
                'description': version_info.get('description', ''),
                'storage_path': version_info['storage_path'],
                'file_size': version_info.get('file_size', 0),
                'created_at': version_info['created_at'],
                'tags': version_info.get('tags', {})
            }
            
            # Save to database
            sqlite_registry.metadata_backend.backend.save_model_metadata(model_data)
            total_versions += 1
    
    print(f"✅ Migration completed!")
    print(f"   Migrated {len(json_data)} models")
    print(f"   Migrated {total_versions} versions")
    
    # 4. Verify migration
    print("🔍 Verifying migration...")
    sqlite_models = sqlite_registry.list_models()
    
    if len(sqlite_models) == len(json_data):
        print("✅ Model count matches")
    else:
        print(f"⚠️ Model count mismatch: JSON={len(json_data)}, SQLite={len(sqlite_models)}")
    
    return sqlite_registry

if __name__ == "__main__":
    migrate_json_to_sqlite(
        json_path="./models/registry.json",
        db_path="./models/registry.db", 
        models_path="./models"
    )
```

#### Step 2: Run Migration
```bash
python migrate_json_to_sqlite.py
```

#### Step 3: Update Application Code
```python
# Before: JSON backend
registry = create_registry("local")

# After: SQLite backend  
registry = create_registry("database")
```

#### Step 4: Verify Migration
```python
# Test all functionality with new backend
registry = create_registry("database")

# List all models
models = registry.list_models()
print(f"Found {len(models)} models")

# Test loading a model
if models:
    model_name = list(models.keys())[0]
    loaded_model = registry.load_model(model_name)
    print(f"Successfully loaded {model_name}")

# Test database-specific features
stats = registry.metadata_backend.backend.get_statistics()
print(f"Database stats: {stats}")
```

### SQLite to PostgreSQL Migration

#### Step 1: Prepare PostgreSQL Database
```sql
-- Create database
CREATE DATABASE mlops_registry;

-- Connect to database
\c mlops_registry;

-- Run schema creation
-- (Use the same schema from model_registry_schema.sql)
```

#### Step 2: Data Migration Script
```python
# migrate_sqlite_to_postgresql.py
import sqlite3
import psycopg2
from datetime import datetime

def migrate_sqlite_to_postgresql(sqlite_path: str, pg_conn_string: str):
    """Migrate from SQLite to PostgreSQL"""
    
    print("🔄 Starting SQLite to PostgreSQL migration...")
    
    # Connect to both databases
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    pg_conn = psycopg2.connect(pg_conn_string)
    pg_cursor = pg_conn.cursor()
    
    try:
        # 1. Migrate models
        print("📊 Migrating models...")
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM mr_models")
        
        for row in sqlite_cursor.fetchall():
            pg_cursor.execute("""
                INSERT INTO mr_models (id, name, description, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (row['id'], row['name'], row['description'], 
                  row['created_at'], row['updated_at']))
        
        # 2. Migrate model versions
        print("📦 Migrating model versions...")
        sqlite_cursor.execute("SELECT * FROM mr_model_versions")
        
        for row in sqlite_cursor.fetchall():
            pg_cursor.execute("""
                INSERT INTO mr_model_versions 
                (id, model_id, version, description, storage_path, file_size_bytes, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (row['id'], row['model_id'], row['version'], row['description'],
                  row['storage_path'], row['file_size_bytes'], row['created_at']))
        
        # 3. Migrate tags
        print("🏷️ Migrating tags...")
        sqlite_cursor.execute("SELECT * FROM mr_model_tags")
        
        for row in sqlite_cursor.fetchall():
            pg_cursor.execute("""
                INSERT INTO mr_model_tags (id, model_version_id, tag_key, tag_value)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (row['id'], row['model_version_id'], row['tag_key'], row['tag_value']))
        
        # Commit transaction
        pg_conn.commit()
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        pg_conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate_sqlite_to_postgresql(
        sqlite_path="./models/registry.db",
        pg_conn_string="postgresql://user:password@localhost/mlops_registry"
    )
```

## 🔧 Configuration Updates

### Environment-Specific Configurations

#### Development (SQLite)
```python
# config/development.py
REGISTRY_CONFIG = {
    "storage_type": "database",
    "path": "./dev_models",
    "db_path": "./dev_models/registry.db"
}
```

#### Production (PostgreSQL)
```python
# config/production.py
import os

REGISTRY_CONFIG = {
    "storage_type": "postgresql",  # Future implementation
    "connection_string": os.getenv("DATABASE_URL"),
    "models_bucket": os.getenv("S3_MODELS_BUCKET")
}
```

#### Application Code
```python
# app.py
import os
from config import development, production
from model_management import create_registry

def get_registry():
    """Factory function for environment-specific registry"""
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "production":
        config = production.REGISTRY_CONFIG
    else:
        config = development.REGISTRY_CONFIG
    
    return create_registry(**config)

# Usage
registry = get_registry()
```

## 🧪 Testing Migration

### Migration Test Script
```python
# test_migration.py
import tempfile
import os
from model_management import create_registry

def test_migration_integrity():
    """Test that migration preserves all data"""
    
    # 1. Create test data with JSON backend
    with tempfile.TemporaryDirectory() as temp_dir:
        json_registry = create_registry("local", 
                                       path=temp_dir,
                                       metadata_path=f"{temp_dir}/test.json")
        
        # Add test models
        def test_model(x):
            return x * 2
        
        json_registry.save_model(test_model, "test_model", "Test model",
                                tags={"type": "test", "version": "1.0"})
        
        # 2. Migrate to database
        db_registry = create_registry("database",
                                     path=temp_dir, 
                                     db_path=f"{temp_dir}/test.db")
        
        # Manual migration (copy metadata)
        json_models = json_registry.list_models()
        for model_name, versions in json_models.items():
            for version_info in versions:
                db_registry.metadata_backend.backend.save_model_metadata(version_info)
        
        # 3. Verify data integrity
        db_models = db_registry.list_models()
        
        assert len(json_models) == len(db_models), "Model count mismatch"
        
        for model_name in json_models:
            assert model_name in db_models, f"Missing model: {model_name}"
            
            json_versions = json_models[model_name]
            db_versions = db_models[model_name]
            
            assert len(json_versions) == len(db_versions), f"Version count mismatch for {model_name}"
        
        print("✅ Migration integrity test passed")

if __name__ == "__main__":
    test_migration_integrity()
```

## 🚨 Rollback Procedures

### Rollback from Database to JSON
```python
# rollback_to_json.py
from model_management import create_registry
import json

def rollback_database_to_json(db_path: str, json_path: str, models_path: str):
    """Rollback from database to JSON backend"""
    
    print("↩️ Rolling back from database to JSON...")
    
    # 1. Load from database
    db_registry = create_registry("database", path=models_path, db_path=db_path)
    db_models = db_registry.list_models()
    
    # 2. Save to JSON
    with open(json_path, 'w') as f:
        json.dump(db_models, f, indent=2)
    
    # 3. Verify JSON registry works
    json_registry = create_registry("local", path=models_path, metadata_path=json_path)
    json_models = json_registry.list_models()
    
    assert len(db_models) == len(json_models), "Rollback data mismatch"
    
    print("✅ Rollback completed successfully")

if __name__ == "__main__":
    rollback_database_to_json(
        db_path="./models/registry.db",
        json_path="./models/registry.json",
        models_path="./models"
    )
```

## 📊 Migration Checklist

### Pre-Migration
- [ ] Backup all data (models + metadata)
- [ ] Test migration on copy of production data
- [ ] Verify application dependencies
- [ ] Plan rollback procedure
- [ ] Schedule maintenance window

### During Migration  
- [ ] Stop application services
- [ ] Run migration script
- [ ] Verify data integrity
- [ ] Test application functionality
- [ ] Update configuration files

### Post-Migration
- [ ] Monitor system performance
- [ ] Verify all features work correctly
- [ ] Clean up old backup files (after verification period)
- [ ] Update documentation
- [ ] Train team on new backend features

## 🎯 Future Migration Paths

### Planned Migration Routes
```
JSON → SQLite → PostgreSQL → Distributed Database
  ↓       ↓         ↓              ↓
 Dev    Staging   Production   Enterprise Scale
```

### Migration Automation
Future enhancement: Automated migration tool
```bash
# Planned CLI tool
mlops-registry migrate --from json --to sqlite --path ./models
mlops-registry migrate --from sqlite --to postgresql --conn "postgresql://..."
```

This migration guide ensures smooth transitions between different backend systems as your MLOps requirements evolve.