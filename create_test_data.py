"""
Simple script to create test data for API demo
"""

import sys
import os
from model_management import create_registry

# Create some simple test models
def linear_model(x):
    return 2 * x + 1

def quadratic_model(x):
    return x**2 + 3*x + 2

class SimpleClassifier:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
    
    def predict(self, x):
        return 1 if x > self.threshold else 0

def create_test_data():
    """Create test data for API"""
    print("🔧 Creating test data for API...")
    
    # Create registry (this will be used by API)
    registry = create_registry("database", 
                              path="./api_models", 
                              db_path="./api_models/registry.db")
    
    # Add some test models
    v1 = registry.save_model(
        linear_model,
        "linear_predictor",
        "Simple linear regression model",
        tags={"type": "regression", "complexity": "low", "author": "data_team"}
    )
    
    v2 = registry.save_model(
        quadratic_model,
        "quadratic_predictor", 
        "Quadratic polynomial model",
        tags={"type": "regression", "complexity": "medium", "author": "ml_team"}
    )
    
    classifier = SimpleClassifier(threshold=0.3)
    v3 = registry.save_model(
        classifier,
        "binary_classifier",
        "Simple threshold classifier", 
        tags={"type": "classification", "threshold": "0.3", "author": "data_team"}
    )
    
    print(f"✅ Created test data:")
    print(f"   - linear_predictor v{v1}")
    print(f"   - quadratic_predictor v{v2}")
    print(f"   - binary_classifier v{v3}")
    
    # Verify data
    models = registry.list_models()
    print(f"📊 Total models in registry: {len(models)}")
    
    return registry

if __name__ == "__main__":
    create_test_data()