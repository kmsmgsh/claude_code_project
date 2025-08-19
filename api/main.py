"""
Simple FastAPI for Model Management - View Models and Metadata
"""

from fastapi import FastAPI, HTTPException
from typing import Dict, List, Any
import os
import sys

# Add parent directory to path to import model_management
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from model_management import create_registry

# Initialize FastAPI app
app = FastAPI(
    title="Model Registry API",
    description="Simple API to view models and metadata",
    version="1.0.0"
)

# Global registry instance
registry = None

def get_registry():
    """Get or create registry instance"""
    global registry
    if registry is None:
        registry = create_registry("database", 
                                  path="../api_models", 
                                  db_path="../api_models/registry.db")
    return registry

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Model Registry API", "endpoints": ["/models", "/models/count", "/models/stats"]}

@app.get("/models")
async def list_models():
    """Get list of all models and their metadata"""
    try:
        reg = get_registry()
        models = reg.list_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/count")
async def get_model_count():
    """Get count of models and versions"""
    try:
        reg = get_registry()
        models = reg.list_models()
        
        total_models = len(models)
        total_versions = sum(len(versions) for versions in models.values())
        
        return {
            "total_models": total_models,
            "total_versions": total_versions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models/stats")
async def get_statistics():
    """Get detailed statistics from database"""
    try:
        reg = get_registry()
        
        # Get database backend stats if available
        if hasattr(reg.metadata_backend, 'backend'):
            stats = reg.metadata_backend.backend.get_statistics()
            return stats
        else:
            return {"error": "Advanced stats only available with database backend"}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)