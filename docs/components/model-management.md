# Model Management Module

The Model Management module provides a centralized repository for storing, versioning, and managing machine learning models with pluggable storage backends.

## 🏗️ Architecture

### Abstract Storage Design

The module follows a **clean architecture** with abstract interfaces that allow switching storage backends without changing business logic.

```mermaid
graph TD
    A[Model Registry] --> B[Storage Backend Interface]
    A --> C[Metadata Backend Interface]
    
    B --> D[Local Storage]
    B --> E[S3 Storage]
    B --> F[Other Storage...]
    
    C --> G[JSON Metadata]
    C --> H[Database Metadata]
    C --> I[Other Metadata...]
    
    subgraph "Implemented"
        D
        G
    end
    
    subgraph "Planned"
        E
        H
        F
        I
    end
```

## 🧩 Components

### 1. Storage Backends

Abstract interface for model storage with concrete implementations:

#### `StorageBackend` (Abstract)
```python
class StorageBackend(ABC):
    @abstractmethod
    def save_model(self, model: Any, path: str) -> None: ...
    
    @abstractmethod
    def load_model(self, path: str) -> Any: ...
    
    @abstractmethod
    def delete_model(self, path: str) -> None: ...
```

#### `LocalStorageBackend` ✅ Implemented
- Stores models on local filesystem using pickle
- Automatic directory creation
- File size tracking

#### `S3StorageBackend` 🚧 Planned
- Cloud storage for production deployments
- Supports S3-compatible storage systems

### 2. Metadata Backends

Abstract interface for metadata storage:

#### `MetadataBackend` (Abstract)
```python
class MetadataBackend(ABC):
    @abstractmethod
    def save_metadata(self, metadata: Dict) -> None: ...
    
    @abstractmethod
    def load_metadata(self) -> Dict: ...
```

#### `JSONMetadataBackend` ✅ Implemented
- Stores metadata in JSON files
- Human-readable format
- Simple file-based persistence

#### `DatabaseMetadataBackend` ✅ Implemented
- **SQLite database** storage with raw SQL
- **PostgreSQL/MySQL ready** - same schema, different drivers
- **Advanced querying** capabilities with indexes
- **Migration system** for schema evolution
- **Production-ready** with transaction safety

### 3. Model Registry

Main interface for model operations:

```python
class ModelRegistry:
    def save_model(self, model, name, description="", tags=None) -> str
    def load_model(self, name, version=None) -> Any
    def delete_model(self, name, version=None) -> None
    def list_models(self) -> Dict
    def get_model_versions(self, name) -> List[Dict]
```

## 🚀 Usage Examples

### Basic Usage

```python
from model_management import create_registry

# Create registry with local storage
registry = create_registry("local", path="./models")

# Save a model
def my_model(x):
    return x * 2 + 1

version = registry.save_model(
    my_model, 
    "linear_model", 
    "Simple linear predictor",
    tags={"type": "function", "complexity": "low"}
)

# Load the model
loaded_model = registry.load_model("linear_model")
result = loaded_model(5)  # Returns 11
```

### Working with Versions

```python
# Save multiple versions
registry.save_model(model_v1, "classifier", "Initial version")
registry.save_model(model_v2, "classifier", "Improved accuracy")
registry.save_model(model_v3, "classifier", "Latest with new features")

# Load specific version
old_model = registry.load_model("classifier", version="1")

# Load latest version (default)
latest_model = registry.load_model("classifier")

# Get version information
versions = registry.get_model_versions("classifier")
latest_version = registry.get_latest_version("classifier")
```

### Model Information and Metadata

```python
# List all models
all_models = registry.list_models()

for name, versions in all_models.items():
    print(f"Model: {name}")
    for version_info in versions:
        print(f"  v{version_info['version']}: {version_info['description']}")
        print(f"    Created: {version_info['created_at']}")
        print(f"    Size: {version_info['file_size']} bytes")
        print(f"    Tags: {version_info['tags']}")
```

### Backend Configuration Options

```python
# Option 1: JSON metadata (simple, human-readable)
registry = create_registry("local", 
                          path="./models", 
                          metadata_path="./models/registry.json")

# Option 2: SQLite database (production-ready, queryable)
registry = create_registry("database", 
                          path="./models", 
                          db_path="./models/registry.db")

# Option 3: Custom backend configuration
from model_management import ModelRegistry, LocalStorageBackend, DatabaseMetadataBackend

storage = LocalStorageBackend("/custom/model/path")
metadata = DatabaseMetadataBackend("/custom/registry.db")
registry = ModelRegistry(storage, metadata)
```

## 🔧 Configuration

### Factory Function

The `create_registry()` function provides easy configuration:

```python
# JSON metadata backend (default)
registry = create_registry("local")

# SQLite database backend 
registry = create_registry("database")

# Custom paths
registry = create_registry("local", path="/my/models", metadata_path="/my/registry.json")
registry = create_registry("database", path="/my/models", db_path="/my/registry.db")

# Future: Cloud storage
# registry = create_registry("s3", bucket="my-models", region="us-east-1")
```

## 📁 Storage Structure

### JSON Backend Structure
```
models/
├── registry.json                 # Metadata file
├── linear_model/
│   ├── v1/
│   │   └── model.pkl             # Model file version 1
│   └── v2/
│       └── model.pkl             # Model file version 2
└── classifier/
    └── v1/
        └── model.pkl             # Classifier model
```

### Database Backend Structure  
```
models/
├── registry.db                   # SQLite database
├── linear_model/
│   ├── v1/
│   │   └── model.pkl             # Model file version 1
│   └── v2/
│       └── model.pkl             # Model file version 2
└── classifier/
    └── v1/
        └── model.pkl             # Classifier model
```

### Database Schema
```sql
-- Models table (mr_models)
CREATE TABLE mr_models (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Model versions table (mr_model_versions) 
CREATE TABLE mr_model_versions (
    id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    storage_path TEXT NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES mr_models(id) ON DELETE CASCADE
);

-- Model tags table (mr_model_tags)
CREATE TABLE mr_model_tags (
    id INTEGER PRIMARY KEY,
    model_version_id INTEGER NOT NULL,
    tag_key TEXT NOT NULL,
    tag_value TEXT,
    FOREIGN KEY (model_version_id) REFERENCES mr_model_versions(id) ON DELETE CASCADE
);
```

### Metadata Format

The `registry.json` file contains structured metadata:

```json
{
  "linear_model": [
    {
      "name": "linear_model",
      "version": "1",
      "description": "Simple linear predictor",
      "tags": {"type": "function", "complexity": "low"},
      "created_at": "2024-01-15T10:30:00.000000",
      "storage_path": "linear_model/v1/model.pkl",
      "file_size": 245
    }
  ]
}
```

## 🎯 Key Features

### ✅ Implemented Features

#### Core Features
- **Automatic Versioning**: Sequential version numbers (1, 2, 3...)
- **Model Metadata**: Description, tags, creation time, file size
- **Pluggable Storage**: Abstract backend system
- **Version Management**: Load specific versions or latest
- **Model Listing**: Browse all models and versions

#### Storage Backends
- **Local Storage**: Filesystem-based model file storage
- **S3 Storage**: Placeholder for cloud storage (planned)

#### Metadata Backends  
- **JSON Metadata**: File-based metadata storage (simple)
- **SQLite Database**: Production-ready database storage
- **Advanced Queries**: Statistics, tag searching, model filtering
- **Migration System**: Schema versioning for database evolution
- **Transaction Safety**: ACID compliance with proper error handling

#### Database Features
- **Raw SQL Implementation**: No ORM dependencies, full control
- **Cross-Database Schema**: Compatible with SQLite/PostgreSQL/MySQL
- **Performance Indexes**: Optimized for common query patterns
- **Foreign Key Constraints**: Data integrity with cascade deletes
- **Table Organization**: Prefixed tables (`mr_*`) for multi-domain support

### 🚧 Planned Features

- **S3 Storage Backend**: Cloud storage support
- **Database Metadata**: SQL database for metadata
- **Model Validation**: Automatic model testing before save
- **Model Lineage**: Track model relationships and dependencies
- **Performance Metrics**: Store model performance data
- **Model Staging**: Development → Staging → Production workflow
- **Model Comparison**: Compare different model versions
- **Search and Filtering**: Query models by tags, performance, etc.

## 🔍 Error Handling

The registry provides clear error messages:

```python
try:
    model = registry.load_model("nonexistent_model")
except ValueError as e:
    print(f"Error: {e}")  # Model 'nonexistent_model' not found in registry

try:
    model = registry.load_model("my_model", version="999")
except ValueError as e:
    print(f"Error: {e}")  # Model 'my_model' version '999' not found
```

## 🧪 Testing & Examples

### Basic JSON Backend Test
```bash
python model_management/example.py
```

### Database Backend Test
```bash
python model_management/database_example.py
```

Expected output:
```
🗄️ Model Registry Database Backend Example
============================================================

📊 Creating registry with SQLite database...
✅ Database backend initialized

💾 Saving models to database...
✅ Model 'linear_predictor' version 1 saved successfully
✅ Model 'linear_predictor' version 2 saved successfully
✅ Model 'binary_classifier' version 1 saved successfully
✅ Model 'binary_classifier' version 2 saved successfully

📊 Database Statistics:
Total models: 2
Total versions: 4
Total size: 0.0 MB

🔍 Searching by tags:
Regression models: 2 found
  linear_predictor v1: Original linear model
  linear_predictor v2: Enhanced linear model with better coefficients

✅ Database backend test completed successfully!
```

### Advanced Database Queries

The database backend supports advanced querying capabilities:

```python
from model_management import create_registry

# Create database registry
registry = create_registry("database")

# Get database backend for advanced queries
db_backend = registry.metadata_backend.backend

# Get comprehensive statistics
stats = db_backend.get_statistics()
print(f"Total models: {stats['summary']['total_models']}")
print(f"Total storage: {stats['summary']['total_size_mb']} MB")

# Search models by tags
regression_models = db_backend.find_models_by_tag("type", "regression")
for model in regression_models:
    print(f"{model['name']} v{model['version']}: {model['description']}")

# Find models by author
team_models = db_backend.find_models_by_tag("author", "team_a")
```

## 🚀 Next Steps

1. **Implement S3 Backend**: Add cloud storage support
2. **Add Database Metadata**: Use SQL for better querying
3. **Model Validation**: Automatic testing before save
4. **Performance Tracking**: Store model metrics
5. **Web API**: REST API for model management
6. **Model Staging**: Implement deployment stages

This model management module provides a solid foundation for MLOps model lifecycle management with room for future enhancements.