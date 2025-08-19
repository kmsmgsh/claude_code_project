# MLOps Management System

A comprehensive machine learning operations platform providing end-to-end model lifecycle management with centralized model registry, database storage, and REST API access.

## 🚀 Features

- **🎯 Model Registry**: Centralized model storage with automatic versioning
- **🗄️ Database Backend**: Production-ready SQLite with PostgreSQL/MySQL compatibility  
- **🌐 REST API**: FastAPI backend with interactive documentation
- **📊 Advanced Querying**: Model search, statistics, and metadata management
- **🔄 Migration System**: Database schema evolution and backend switching
- **📖 Comprehensive Documentation**: Architecture guides and API references

## 🏗️ Architecture

```
HTTP Client → FastAPI → ModelRegistry → SQLite Database
                ↓              ↓            ↓
           Interactive    Model Files   Metadata
              Docs       (.pkl files)   & Tags
```

## 📖 Documentation

**📚 [View Complete Documentation](https://kmsmgsh.github.io/mlops-management-system/)**

- [Model Management Guide](https://kmsmgsh.github.io/mlops-management-system/components/model-management/)
- [REST API Documentation](https://kmsmgsh.github.io/mlops-management-system/components/rest-api/)  
- [Database Design](https://kmsmgsh.github.io/mlops-management-system/components/database-design/)
- [Migration Guide](https://kmsmgsh.github.io/mlops-management-system/development/migration-guide/)

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/kmsmgsh/mlops-management-system.git
cd mlops-management-system
```

### 2. Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn
```

### 3. Create Test Data
```bash
python create_test_data.py
```

### 4. Start REST API
```bash
cd api
python main.py
```

### 5. Access API
- **Interactive Docs**: http://localhost:8001/docs
- **API Endpoints**: http://localhost:8001/models
- **Statistics**: http://localhost:8001/models/stats

## 💻 Usage Examples

### Python API
```python
from model_management import create_registry

# Create registry with database backend
registry = create_registry("database")

# Save a model
def my_model(x):
    return x * 2 + 1

registry.save_model(my_model, "linear_model", "Simple predictor",
                   tags={"type": "regression", "author": "team_a"})

# Load model
loaded_model = registry.load_model("linear_model")
result = loaded_model(5)  # Returns 11
```

### REST API
```bash
# List all models
curl http://localhost:8001/models

# Get model count  
curl http://localhost:8001/models/count

# Get statistics
curl http://localhost:8001/models/stats
```

## 🗄️ Storage Backends

### JSON Backend (Development)
```python
registry = create_registry("local")  # Uses JSON files
```

### Database Backend (Production)
```python  
registry = create_registry("database")  # Uses SQLite
```

### Future: PostgreSQL/MySQL
```python
# Planned - same schema, different driver
registry = create_registry("postgresql", connection_string="...")
```

## 📊 Database Schema

```sql
-- Models table
CREATE TABLE mr_models (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL
);

-- Model versions with metadata
CREATE TABLE mr_model_versions (
    id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    storage_path TEXT NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES mr_models(id)
);

-- Key-value tags
CREATE TABLE mr_model_tags (
    id INTEGER PRIMARY KEY,
    model_version_id INTEGER NOT NULL,
    tag_key TEXT NOT NULL,
    tag_value TEXT,
    FOREIGN KEY (model_version_id) REFERENCES mr_model_versions(id)
);
```

## 🧪 Testing

```bash
# Test JSON backend
python model_management/example.py

# Test database backend
python model_management/database_example.py

# Start API server
cd api && python main.py

# Test API endpoints
curl http://localhost:8001/models
```

## 📁 Project Structure

```
mlops-management-system/
├── model_management/           # Core Python package
│   ├── model_registry.py      # Main registry class
│   ├── storage_backends.py    # Abstract backends
│   └── database/              # Database operations
│       ├── database_manager.py
│       ├── schemas/
│       └── migrations/
├── api/                       # FastAPI REST API  
│   └── main.py
├── docs/                      # Documentation source
│   ├── components/
│   ├── architecture/
│   └── development/
├── requirements.txt           # Dependencies
└── mkdocs.yml                # Documentation config
```

## 🛠️ Technology Stack

- **Backend**: Python, FastAPI, Uvicorn
- **Database**: SQLite (PostgreSQL/MySQL compatible)
- **Storage**: Local filesystem (S3 planned)
- **Documentation**: MkDocs Material
- **API**: REST with OpenAPI/Swagger

## 🚀 Deployment

### Development
```bash
# Local SQLite database
python api/main.py
```

### Production (Planned)
```bash
# PostgreSQL + Docker + Kubernetes
docker build -t mlops-api .
kubectl apply -f k8s/
```

## 📈 Roadmap

### ✅ Phase 1: Core Registry (Completed)
- Model registry with versioning
- SQLite database backend
- REST API with documentation

### 🚧 Phase 2: Enhanced API (Planned)
- Model upload/download endpoints
- Authentication and authorization
- Advanced search and filtering

### 🎯 Phase 3: Enterprise Features (Future)
- PostgreSQL/MySQL support
- S3 storage backend
- Kubernetes deployment
- Model serving integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests and documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- **📚 [Documentation](https://kmsmgsh.github.io/mlops-management-system/)**
- **🐛 [Issues](https://github.com/kmsmgsh/mlops-management-system/issues)**
- **💡 [Discussions](https://github.com/kmsmgsh/mlops-management-system/discussions)**

---

Built with ❤️ using FastAPI, SQLite, and modern MLOps practices.