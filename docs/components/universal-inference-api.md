# Universal Inference API Demo

**Status**: Implemented - Option 2 Demo  
**Implementation**: `api/main.py`  
**Demo Guide**: `UNIVERSAL_API_DEMO.md`

## Overview

The Universal Inference API provides a single endpoint that can serve predictions from any deployed model, with explicit deployment management for memory control.

## Architecture

```
Model Registry (Storage) → Deployment Control → Active Models (Memory) → Inference
     ↓                          ↓                       ↓                    ↓
[All Models Stored]      [POST /deployments/deploy]   [Limited in Memory]   [POST /predict]
```

### Key Design Decisions

1. **Single Universal Endpoint** - `POST /predict` handles all models
2. **Explicit Deployment** - Models must be deployed before inference
3. **Memory Management** - Only deployed models consume memory
4. **Model Selection in Payload** - Model specified in request body

## API Endpoints

### Deployment Management

#### Deploy Model
```http
POST /deployments/deploy
Content-Type: application/json

{
  "model_name": "binary_classifier",
  "version": "1"
}
```

**Response:**
```json
{
  "status": "deployed",
  "deployment_key": "binary_classifier:v1",
  "load_time_seconds": 0.023,
  "memory_usage_mb": 2.1,
  "message": "Model ready for inference at POST /predict"
}
```

#### Undeploy Model
```http
POST /deployments/undeploy
Content-Type: application/json

{
  "model_name": "binary_classifier",
  "version": "1"
}
```

#### List Deployments
```http
GET /deployments
```

**Response:**
```json
{
  "active_deployments": [
    {
      "deployment_key": "binary_classifier:v1",
      "model_name": "binary_classifier",
      "version": "1",
      "status": "active",
      "memory_usage_mb": 2.1,
      "request_count": 5,
      "last_used": "2025-08-20T10:30:00Z"
    }
  ],
  "summary": {
    "total_deployed": 1,
    "total_models_in_memory": 1,
    "current_memory": {"rss_mb": 47.3}
  }
}
```

#### Deployment Status
```http
GET /deployments/status
```

### Universal Inference

#### Make Prediction
```http
POST /predict
Content-Type: application/json

{
  "model_name": "binary_classifier",
  "version": "1",
  "input": [0.5, 0.8, 0.2]
}
```

**Response:**
```json
{
  "prediction": 1,
  "metadata": {
    "model_name": "binary_classifier",
    "version": "1",
    "deployment_key": "binary_classifier:v1",
    "inference_time_ms": 0.15,
    "request_count": 6
  },
  "model_info": {
    "description": "Simple threshold classifier",
    "tags": {
      "type": "classification",
      "author": "data_team"
    }
  }
}
```

## Usage Workflow

### 1. Check Available Models
```bash
GET /models
# Shows all models in registry (not deployed)
```

### 2. Deploy Needed Models
```bash
POST /deployments/deploy
{"model_name": "binary_classifier", "version": "1"}
```

### 3. Make Predictions
```bash
POST /predict
{
  "model_name": "binary_classifier",
  "input": [0.5, 0.8, 0.2]
}
```

### 4. Monitor Usage
```bash
GET /deployments/status
# Check memory usage and request counts
```

### 5. Clean Up
```bash
POST /deployments/undeploy
{"model_name": "binary_classifier", "version": "1"}
```

## Model Input Formats

The Universal API supports different input formats based on model type:

### Binary Classifier
```json
{
  "model_name": "binary_classifier",
  "input": [0.5, 0.8, 0.2]
}
```

### Quadratic Predictor
```json
{
  "model_name": "quadratic_predictor", 
  "input": 2.5
}
```

### Future Models
The API automatically adapts to any model in the registry:
```json
{
  "model_name": "any_new_model",
  "input": {...}
}
```

## Error Handling

### Model Not Deployed
```http
POST /predict
{"model_name": "undeployed_model", "input": [...]}

Response: 404
{
  "detail": "Model 'undeployed_model' v1 not deployed. Deploy it first using POST /deployments/deploy. Available deployments: ['binary_classifier:v1']"
}
```

### Model Not Found in Registry
```http
POST /deployments/deploy
{"model_name": "nonexistent_model"}

Response: 404
{
  "detail": "Model 'nonexistent_model' not found in registry"
}
```

### Invalid Input Format
```http
POST /predict
{"model_name": "binary_classifier", "input": "invalid"}

Response: 400
{
  "detail": "Prediction failed: model expected array, got string. Check input format."
}
```

## Performance Features

### Memory Management
- **Controlled Loading**: Only deployed models consume memory
- **Memory Tracking**: Monitor memory usage per model
- **Resource Cleanup**: Undeploy unused models

### Request Tracking
- **Usage Statistics**: Count requests per model
- **Performance Metrics**: Track inference times
- **Last Used Timestamp**: Monitor model activity

### Caching
- **In-Memory Models**: Fast predictions on deployed models
- **Lazy Loading**: Models loaded only when deployed
- **Persistent State**: Deployment state survives across requests

## Operational Benefits

### Production Readiness
✅ **Memory Control** - Deploy only needed models  
✅ **Resource Monitoring** - Track usage and performance  
✅ **Error Handling** - Clear error messages and validation  
✅ **API Documentation** - Interactive OpenAPI docs  

### Development Efficiency
✅ **Single Endpoint** - Consistent interface for all models  
✅ **Version Control** - Specify exact model versions  
✅ **Easy Testing** - Simple REST API calls  
✅ **Flexible Input** - Supports any model input format  

### Scalability
✅ **Model Addition** - New models work automatically  
✅ **Version Management** - Multiple versions deployable  
✅ **Resource Limits** - Controlled memory usage  
✅ **Monitoring Ready** - Built-in metrics collection  

## Demo Instructions

1. **Start Server**: `cd api && python main.py`
2. **Visit Docs**: http://127.0.0.1:8001/docs
3. **Follow Guide**: See `UNIVERSAL_API_DEMO.md` for step-by-step workflow
4. **Test with Postman**: Use provided request examples

## Next Steps

This implementation demonstrates the Universal API approach (Option 2) with deployment layer management. Based on this demo, the team can:

1. **Architecture Decision**: Choose between Universal API vs Dynamic Endpoints
2. **Production Enhancements**: Add authentication, logging, metrics
3. **Scaling Features**: Add model versioning, A/B testing, auto-scaling
4. **Integration**: Connect with existing ML pipelines and monitoring systems

The Universal API provides a solid foundation for enterprise MLOps model serving with proper memory management and operational control.