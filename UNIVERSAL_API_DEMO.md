# Universal API Demo - Option 2

Complete demo of Universal Inference API with Deployment Layer for memory management.

## 🚀 Start the Demo

```bash
cd api
python main.py
```

Visit: **http://127.0.0.1:8001/docs** for interactive API documentation

## 📋 Demo Workflow

### Step 1: Check Available Models in Registry
```bash
GET http://127.0.0.1:8001/models
```

**Expected Response:**
```json
{
  "models": {
    "binary_classifier": [...],
    "quadratic_predictor": [...]
  }
}
```

### Step 2: Check Current Deployments (Should be Empty)
```bash
GET http://127.0.0.1:8001/deployments
```

**Expected Response:**
```json
{
  "active_deployments": [],
  "summary": {
    "total_deployed": 0,
    "total_models_in_memory": 0,
    "current_memory": {"rss_mb": 45.2, "vms_mb": 123.4}
  }
}
```

### Step 3: Try Prediction Before Deployment (Should Fail)
```bash
POST http://127.0.0.1:8001/predict
Content-Type: application/json

{
  "model_name": "binary_classifier",
  "version": "1",
  "input": [0.5, 0.8, 0.2]
}
```

**Expected Response:**
```json
{
  "detail": "Model 'binary_classifier' v1 not deployed. Deploy it first using POST /deployments/deploy. Available deployments: []"
}
```

### Step 4: Deploy Binary Classifier
```bash
POST http://127.0.0.1:8001/deployments/deploy
Content-Type: application/json

{
  "model_name": "binary_classifier",
  "version": "1"
}
```

**Expected Response:**
```json
{
  "status": "deployed",
  "deployment_key": "binary_classifier:v1",
  "model_name": "binary_classifier",
  "version": "1",
  "deployed_at": "2025-08-20T...",
  "load_time_seconds": 0.023,
  "memory_usage_mb": 2.1,
  "message": "Model ready for inference at POST /predict"
}
```

### Step 5: Check Deployments (Should Show Deployed Model)
```bash
GET http://127.0.0.1:8001/deployments
```

**Expected Response:**
```json
{
  "active_deployments": [
    {
      "deployment_key": "binary_classifier:v1",
      "model_name": "binary_classifier",
      "version": "1",
      "status": "active",
      "deployed_at": "2025-08-20T...",
      "load_time_seconds": 0.023,
      "memory_usage_mb": 2.1,
      "request_count": 0,
      "last_used": null
    }
  ],
  "summary": {
    "total_deployed": 1,
    "total_models_in_memory": 1,
    "current_memory": {"rss_mb": 47.3, "vms_mb": 125.5}
  }
}
```

### Step 6: Make Prediction (Should Work Now)
```bash
POST http://127.0.0.1:8001/predict
Content-Type: application/json

{
  "model_name": "binary_classifier", 
  "version": "1",
  "input": [0.5, 0.8, 0.2]
}
```

**Expected Response:**
```json
{
  "prediction": 1,
  "metadata": {
    "model_name": "binary_classifier",
    "version": "1", 
    "deployment_key": "binary_classifier:v1",
    "inference_time_ms": 0.15,
    "timestamp": "2025-08-20T...",
    "request_count": 1
  },
  "model_info": {
    "description": "Simple threshold classifier",
    "tags": {
      "author": "data_team",
      "threshold": "0.3",
      "type": "classification"
    }
  }
}
```

### Step 7: Deploy Quadratic Predictor  
```bash
POST http://127.0.0.1:8001/deployments/deploy
Content-Type: application/json

{
  "model_name": "quadratic_predictor",
  "version": "1"
}
```

### Step 8: Test Quadratic Predictor
```bash
POST http://127.0.0.1:8001/predict
Content-Type: application/json

{
  "model_name": "quadratic_predictor",
  "version": "1", 
  "input": 2.5
}
```

**Expected Response:**
```json
{
  "prediction": 6.25,
  "metadata": {
    "model_name": "quadratic_predictor",
    "version": "1",
    "deployment_key": "quadratic_predictor:v1", 
    "inference_time_ms": 0.12,
    "timestamp": "2025-08-20T...",
    "request_count": 1
  },
  "model_info": {
    "description": "Quadratic polynomial model",
    "tags": {
      "author": "ml_team",
      "complexity": "medium", 
      "type": "regression"
    }
  }
}
```

### Step 9: Check Deployment Status
```bash
GET http://127.0.0.1:8001/deployments/status
```

**Expected Response:**
```json
{
  "system_status": {
    "memory": {"rss_mb": 49.8, "vms_mb": 127.2},
    "deployed_models": 2,
    "loaded_models": 2,
    "total_requests_served": 2
  },
  "deployments": {
    "binary_classifier:v1": {
      "model_name": "binary_classifier",
      "status": "active",
      "request_count": 1,
      "last_used": "2025-08-20T..."
    },
    "quadratic_predictor:v1": {
      "model_name": "quadratic_predictor", 
      "status": "active",
      "request_count": 1,
      "last_used": "2025-08-20T..."
    }
  },
  "timestamp": "2025-08-20T..."
}
```

### Step 10: Undeploy Binary Classifier
```bash
POST http://127.0.0.1:8001/deployments/undeploy
Content-Type: application/json

{
  "model_name": "binary_classifier",
  "version": "1"
}
```

**Expected Response:**
```json
{
  "status": "undeployed",
  "deployment_key": "binary_classifier:v1",
  "model_name": "binary_classifier", 
  "version": "1",
  "was_deployed_at": "2025-08-20T...",
  "total_requests": 1,
  "uptime_info": {
    "deployed_at": "2025-08-20T...",
    "last_used": "2025-08-20T..."
  },
  "message": "Model removed from memory"
}
```

### Step 11: Try Prediction on Undeployed Model (Should Fail)
```bash
POST http://127.0.0.1:8001/predict
Content-Type: application/json

{
  "model_name": "binary_classifier",
  "version": "1", 
  "input": [0.5, 0.8, 0.2]
}
```

**Expected Response:**
```json
{
  "detail": "Model 'binary_classifier' v1 not deployed. Deploy it first using POST /deployments/deploy. Available deployments: ['quadratic_predictor:v1']"
}
```

## ✅ Demo Features Demonstrated

1. **Memory Management**: Only deployed models consume memory
2. **Deployment Control**: Explicit deploy/undeploy lifecycle
3. **Universal API**: Single `/predict` endpoint handles all models
4. **Resource Monitoring**: Track memory usage and request counts
5. **Error Handling**: Clear messages when models not deployed
6. **Performance Tracking**: Load times, inference times, usage stats

## 🎯 Key Benefits

- **Controlled Memory Usage**: Deploy only needed models
- **Production Ready**: Deployment layer provides operational control
- **Universal Interface**: Consistent API for all model types
- **Observability**: Full visibility into model usage and performance
- **Resource Efficiency**: Undeploy unused models to free memory

## 📊 API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/models` | GET | List models in registry |
| `/deployments/deploy` | POST | Load model into memory |
| `/deployments/undeploy` | POST | Remove model from memory |
| `/deployments` | GET | List deployed models |
| `/deployments/status` | GET | System status & metrics |
| `/predict` | POST | Universal inference endpoint |

This demo shows how the Universal API (Option 2) provides a clean, manageable approach to model serving with proper memory management!