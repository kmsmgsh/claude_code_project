"""
Simple FastAPI for Model Management - View Models and Metadata
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Any, Optional, Union
import os
import sys
import psutil
from datetime import datetime

# Add parent directory to path to import model_management
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from model_management import create_registry

# Initialize FastAPI app
app = FastAPI(
    title="MLOps Model Registry & Inference API",
    description="Model management and universal inference API - Option 2 Demo",
    version="2.0.0-demo"
)

# Global registry instance
registry = None

# Global deployment state for inference API demo
active_deployments = {}  # {"model_name:version": deployment_info}
loaded_models = {}       # {"model_name:version": model_object}

# Request/Response models for API
class DeploymentRequest(BaseModel):
    model_name: str
    version: Optional[str] = None  # Defaults to latest
    
class UndeployRequest(BaseModel):
    model_name: str
    version: Optional[str] = None
    
class PredictionRequest(BaseModel):
    model_name: str
    version: Optional[str] = None  # Defaults to latest
    input: Union[float, int, List[float], List[int], Dict]
    options: Optional[Dict] = {}

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
    return {
        "message": "MLOps Model Registry & Inference API - Universal API Demo", 
        "management_endpoints": ["/models", "/models/count", "/models/stats"],
        "deployment_endpoints": ["/deployments", "/deployments/deploy", "/deployments/undeploy"],
        "inference_endpoints": ["/predict"]
    }

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

# ========================================
# DEPLOYMENT LAYER - MEMORY MANAGEMENT
# ========================================

def get_deployment_key(model_name: str, version: str) -> str:
    """Generate deployment key for tracking"""
    return f"{model_name}:v{version}"

def get_model_latest_version(model_name: str) -> str:
    """Get latest version of a model from registry"""
    reg = get_registry()
    try:
        return reg.get_latest_version(model_name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found in registry")

def get_memory_usage():
    """Get current memory usage"""
    process = psutil.Process()
    memory_info = process.memory_info()
    return {
        "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
        "vms_mb": round(memory_info.vms / 1024 / 1024, 2)
    }

@app.post("/deployments/deploy")
async def deploy_model(request: DeploymentRequest):
    """Deploy a model into memory for inference"""
    try:
        reg = get_registry()
        
        # Get version (use latest if not specified)
        version = request.version or get_model_latest_version(request.model_name)
        deployment_key = get_deployment_key(request.model_name, version)
        
        # Check if model exists in registry
        try:
            model_info = reg._get_model_info(request.model_name, version)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=f"Registry error: {str(e)}")
        
        # Check if already deployed
        if deployment_key in active_deployments:
            return {
                "status": "already_deployed",
                "deployment_key": deployment_key,
                "message": f"Model {request.model_name} v{version} already deployed"
            }
        
        # Load model into memory
        memory_before = get_memory_usage()
        start_time = datetime.now()
        
        try:
            model = reg.load_model(request.model_name, version)
            loaded_models[deployment_key] = model
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load model: {str(e)}")
        
        load_time = (datetime.now() - start_time).total_seconds()
        memory_after = get_memory_usage()
        
        # Store deployment info
        active_deployments[deployment_key] = {
            "model_name": request.model_name,
            "version": version,
            "status": "active",
            "deployed_at": datetime.now().isoformat(),
            "model_info": model_info,
            "load_time_seconds": round(load_time, 3),
            "memory_usage_mb": memory_after["rss_mb"] - memory_before["rss_mb"],
            "request_count": 0,
            "last_used": None
        }
        
        return {
            "status": "deployed",
            "deployment_key": deployment_key,
            "model_name": request.model_name,
            "version": version,
            "deployed_at": active_deployments[deployment_key]["deployed_at"],
            "load_time_seconds": load_time,
            "memory_usage_mb": active_deployments[deployment_key]["memory_usage_mb"],
            "message": f"Model ready for inference at POST /predict"
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Deployment failed: {str(e)}")

@app.post("/deployments/undeploy") 
async def undeploy_model(request: UndeployRequest):
    """Remove a model from memory"""
    try:
        # Get version (use latest if not specified)
        version = request.version or get_model_latest_version(request.model_name)
        deployment_key = get_deployment_key(request.model_name, version)
        
        # Check if deployed
        if deployment_key not in active_deployments:
            raise HTTPException(
                status_code=404, 
                detail=f"Model {request.model_name} v{version} not currently deployed"
            )
        
        # Get deployment info before removal
        deployment_info = active_deployments[deployment_key]
        
        # Remove from memory
        if deployment_key in loaded_models:
            del loaded_models[deployment_key]
        del active_deployments[deployment_key]
        
        return {
            "status": "undeployed",
            "deployment_key": deployment_key,
            "model_name": request.model_name,
            "version": version,
            "was_deployed_at": deployment_info["deployed_at"],
            "total_requests": deployment_info["request_count"],
            "uptime_info": {
                "deployed_at": deployment_info["deployed_at"],
                "last_used": deployment_info["last_used"]
            },
            "message": "Model removed from memory"
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Undeployment failed: {str(e)}")

@app.get("/deployments")
async def list_deployments():
    """List all currently deployed models"""
    deployments = []
    current_memory = get_memory_usage()
    
    for deployment_key, info in active_deployments.items():
        deployments.append({
            "deployment_key": deployment_key,
            "model_name": info["model_name"],
            "version": info["version"],
            "status": info["status"],
            "deployed_at": info["deployed_at"],
            "load_time_seconds": info["load_time_seconds"],
            "memory_usage_mb": info["memory_usage_mb"],
            "request_count": info["request_count"],
            "last_used": info["last_used"]
        })
    
    return {
        "active_deployments": deployments,
        "summary": {
            "total_deployed": len(deployments),
            "total_models_in_memory": len(loaded_models),
            "current_memory": current_memory
        }
    }

@app.get("/deployments/status")
async def deployment_status():
    """Get detailed deployment and memory status"""
    current_memory = get_memory_usage()
    total_requests = sum(info["request_count"] for info in active_deployments.values())
    
    return {
        "system_status": {
            "memory": current_memory,
            "deployed_models": len(active_deployments),
            "loaded_models": len(loaded_models),
            "total_requests_served": total_requests
        },
        "deployments": active_deployments,
        "timestamp": datetime.now().isoformat()
    }

# ========================================
# UNIVERSAL INFERENCE API
# ========================================

@app.post("/predict")
async def universal_predict(request: PredictionRequest):
    """Universal prediction endpoint - only works for deployed models"""
    try:
        # Get version (use latest if not specified)
        version = request.version or get_model_latest_version(request.model_name)
        deployment_key = get_deployment_key(request.model_name, version)
        
        # Check if model is deployed (in memory)
        if deployment_key not in active_deployments:
            available_deployments = list(active_deployments.keys())
            raise HTTPException(
                status_code=404, 
                detail=f"Model '{request.model_name}' v{version} not deployed. Deploy it first using POST /deployments/deploy. Available deployments: {available_deployments}"
            )
        
        # Get model from memory (should be loaded)
        if deployment_key not in loaded_models:
            raise HTTPException(
                status_code=500,
                detail=f"Model {deployment_key} is marked as deployed but not in memory. Please redeploy."
            )
        
        # Make prediction
        model = loaded_models[deployment_key]
        start_time = datetime.now()
        
        try:
            prediction = model(request.input)
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Prediction failed: {str(e)}. Check input format."
            )
        
        # Update deployment stats
        inference_time = (datetime.now() - start_time).total_seconds() * 1000
        active_deployments[deployment_key]["request_count"] += 1
        active_deployments[deployment_key]["last_used"] = datetime.now().isoformat()
        
        # Return prediction with metadata
        return {
            "prediction": prediction,
            "metadata": {
                "model_name": request.model_name,
                "version": version,
                "deployment_key": deployment_key,
                "inference_time_ms": round(inference_time, 2),
                "timestamp": datetime.now().isoformat(),
                "request_count": active_deployments[deployment_key]["request_count"]
            },
            "model_info": {
                "description": active_deployments[deployment_key]["model_info"].get("description", ""),
                "tags": active_deployments[deployment_key]["model_info"].get("tags", {})
            }
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting MLOps Universal Inference API Demo")
    print("📚 Visit http://127.0.0.1:8001/docs for interactive API documentation")
    uvicorn.run(app, host="127.0.0.1", port=8001)