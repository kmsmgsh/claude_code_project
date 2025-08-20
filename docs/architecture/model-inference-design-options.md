# Model Inference API Design Options

**Status**: Draft for Architecture Review  
**Date**: 2025-08-20  
**Author**: Development Team  

## Overview

We have completed the **Model Management** module and now need to implement **Model Inference API** to allow external applications to call our trained models for predictions. This document presents two architectural approaches for senior architecture review.

## Current State

- ✅ Model Registry with versioning (SQLite backend)
- ✅ Model storage and metadata management  
- ✅ FastAPI management endpoints (`/models`, `/models/stats`)
- ✅ Example models: `binary_classifier v1`, `quadratic_predictor v1`

## Design Goal

Create a dynamic inference system where:
1. Models can be deployed/undeployed at runtime
2. Only deployed models serve inference requests
3. Multiple versions of same model can be deployed simultaneously
4. System manages model loading, caching, and lifecycle

---

# Option 1: Dynamic Endpoints Approach

## Architecture
Each deployed model gets its own dedicated REST endpoint that is created/removed dynamically at runtime.

## API Design

### Deployment Management
```bash
# Deploy a model - creates dedicated inference endpoint
POST /deployments/deploy
{
  "model_name": "binary_classifier",
  "version": "1", 
  "endpoint_name": "classifier_prod"
}
# ✅ Creates: POST /predict/classifier_prod

# Undeploy a model - removes inference endpoint
POST /deployments/undeploy  
{
  "endpoint_name": "classifier_prod"
}
# ❌ Removes: POST /predict/classifier_prod

# List active deployments
GET /deployments
```

### Inference Endpoints (Dynamically Created)
```bash
# Each deployed model gets dedicated endpoint
POST /predict/classifier_prod
{
  "input": [0.5, 0.8, 0.2]
}

POST /predict/predictor_v1  
{
  "input": 2.5
}

POST /predict/classifier_canary  # A/B testing
{
  "input": [0.5, 0.8, 0.2]
}
```

## Implementation
```python
def create_inference_endpoint(endpoint_name: str, model_name: str, version: str):
    """Dynamically add inference endpoint to FastAPI app"""
    
    async def predict(request: dict):
        model = loaded_models[endpoint_name]
        result = model(request['input'])
        return {"prediction": result}
    
    # Add route to FastAPI at runtime
    route = APIRoute(
        path=f"/predict/{endpoint_name}",
        endpoint=predict,
        methods=["POST"]
    )
    app.router.routes.append(route)
```

## Pros
- ✅ **RESTful Design**: Clean, resource-oriented URLs
- ✅ **External App Friendly**: Fixed URL per model service
- ✅ **A/B Testing**: Easy to deploy multiple versions with different names
- ✅ **Service Isolation**: Each deployment has dedicated endpoint
- ✅ **API Documentation**: Each endpoint appears in OpenAPI docs

## Cons  
- ❌ **Implementation Complexity**: Dynamic route management in FastAPI
- ❌ **Route Cleanup**: Need to properly remove routes on undeploy
- ❌ **OpenAPI Updates**: Documentation needs runtime updates
- ❌ **Endpoint Discovery**: Clients need to know endpoint names

## Use Cases
- Production deployments with stable endpoint names
- A/B testing (deploy same model as different endpoints)
- Multi-tenant scenarios (customer-specific endpoints)

---

# Option 2: Universal API Approach

## Architecture  
Single prediction endpoint that routes requests to different models based on request payload.

## API Design

### Deployment Management (Same)
```bash
# Deploy a model - makes it available for prediction
POST /deployments/deploy
{
  "model_name": "binary_classifier",
  "version": "1"
}

# Undeploy a model - removes from available models
POST /deployments/undeploy
{
  "model_name": "binary_classifier", 
  "version": "1"
}

# List active deployments  
GET /deployments
```

### Single Inference Endpoint
```bash
# Universal endpoint - model specified in request body
POST /predict
{
  "model_name": "binary_classifier",
  "version": "1",  # Optional, defaults to latest
  "input": [0.5, 0.8, 0.2]
}

POST /predict
{
  "model_name": "quadratic_predictor", 
  "version": "1",
  "input": 2.5
}

POST /predict
{
  "model_name": "binary_classifier",  # Uses latest version
  "input": [0.5, 0.8, 0.2]
}
```

## Implementation
```python
@app.post("/predict")
async def universal_predict(request: PredictionRequest):
    # Validate model is deployed
    deployment_key = f"{request.model_name}:v{request.version}"
    if deployment_key not in active_deployments:
        raise HTTPException(404, "Model not deployed")
    
    # Load model if not cached
    if deployment_key not in loaded_models:
        model = registry.load_model(request.model_name, request.version)
        loaded_models[deployment_key] = model
    
    # Make prediction
    result = loaded_models[deployment_key](request.input)
    return {"prediction": result}
```

## Pros
- ✅ **Simple Implementation**: No dynamic route management
- ✅ **Consistent API**: Single endpoint, predictable interface
- ✅ **Easy Model Addition**: New models require no code changes
- ✅ **Version Flexibility**: Easy to specify or default versions
- ✅ **Maintenance**: Single prediction code path

## Cons
- ❌ **Less RESTful**: Model selection in payload vs URL path
- ❌ **Request Payload**: Clients must specify model in every request
- ❌ **URL Semantics**: Less semantic than resource-specific URLs
- ❌ **API Discovery**: Single endpoint doesn't reveal available models

## Use Cases  
- Development and testing environments
- Applications that need to call multiple models
- Scenarios where model selection is dynamic

---

# Comparison Matrix

| Factor | Dynamic Endpoints | Universal API |
|--------|------------------|---------------|
| **Implementation Complexity** | High | Low |
| **RESTful Design** | ✅ High | ❌ Medium |
| **External App Integration** | ✅ Easy (fixed URLs) | ⚠️ Requires model name |
| **A/B Testing** | ✅ Easy (multiple endpoints) | ⚠️ Requires client logic |
| **Maintenance** | ❌ Complex routing | ✅ Simple single endpoint |
| **API Documentation** | ✅ Each endpoint documented | ⚠️ Single generic endpoint |
| **Performance** | ✅ Direct routing | ✅ Single lookup |
| **Scalability** | ⚠️ Route table growth | ✅ Constant complexity |
| **Error Handling** | ⚠️ Per-endpoint logic | ✅ Centralized logic |
| **Testing** | ❌ Test each endpoint | ✅ Test single code path |

# Deployment State Management (Common)

Both approaches share the same deployment state management:

```python
# In-memory deployment tracking
active_deployments = {
    "binary_classifier:v1": {
        "model_name": "binary_classifier",
        "version": "1",
        "status": "active", 
        "deployed_at": "2025-08-20T10:00:00Z",
        "request_count": 1247,
        "avg_latency_ms": 45
    }
}

# Model caching
loaded_models = {
    "binary_classifier:v1": <model_object>,
    "quadratic_predictor:v1": <model_object>
}
```

# Implementation Effort

## Option 1: Dynamic Endpoints
- **Effort**: 3-4 days
- **Risk**: Medium (FastAPI route manipulation)
- **Components**: Route manager, endpoint generator, cleanup logic

## Option 2: Universal API
- **Effort**: 1-2 days  
- **Risk**: Low (standard FastAPI)
- **Components**: Single endpoint, request validation, model routing

# Recommendation for Architecture Review

Both approaches are technically viable. The decision should be based on:

1. **Integration Priorities**: How will external applications integrate?
2. **Operational Complexity**: What level of complexity can we maintain?
3. **API Design Philosophy**: REST purity vs pragmatic simplicity?
4. **Future Requirements**: Multi-tenancy, A/B testing needs?

# Next Steps

1. **Architecture Review**: Senior architects choose approach
2. **Implementation**: 1-2 week development cycle  
3. **Testing**: Validate with both model types
4. **Documentation**: API documentation and usage examples
5. **Deployment**: Production readiness assessment

---

**Request for Decision**: Please review both options and provide guidance on preferred approach for implementation.