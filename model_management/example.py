"""
Example usage of the Model Registry
Shows how to use different storage backends
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from model_management import create_registry


# Define models at module level so they can be pickled
def linear_model(x):
    return 2 * x + 1

def improved_linear_model(x):
    return 3 * x + 2

class SimpleClassifier:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
    
    def predict(self, x):
        return 1 if x > self.threshold else 0


def example_usage():
    """Example of how to use the model registry"""
    
    print("🚀 Model Registry Example")
    print("=" * 50)
    
    # Create a registry with local storage
    registry = create_registry("local", path="./example_models")
    
    print("\n📝 Saving models...")
    v1 = registry.save_model(
        linear_model, 
        "linear_predictor", 
        "Simple linear function",
        tags={"type": "function", "complexity": "low"}
    )
    
    classifier = SimpleClassifier(threshold=0.3)
    v2 = registry.save_model(
        classifier,
        "simple_classifier", 
        "Threshold-based classifier",
        tags={"type": "classifier", "threshold": 0.3}
    )
    
    v3 = registry.save_model(
        improved_linear_model,
        "linear_predictor",
        "Improved linear function with new coefficients"
    )
    
    print("\n📋 Listing all models:")
    for name, versions in registry.list_models().items():
        print(f"\n🎯 {name}:")
        for version_info in versions:
            print(f"  v{version_info['version']}: {version_info['description']}")
            print(f"    Created: {version_info['created_at'][:19]}")
            print(f"    Size: {version_info['file_size']} bytes")
            if version_info['tags']:
                print(f"    Tags: {version_info['tags']}")
    
    print("\n📦 Loading models...")
    
    # Load latest version of linear predictor
    latest_linear = registry.load_model("linear_predictor")
    print(f"Latest linear model output for x=5: {latest_linear(5)}")
    
    # Load specific version
    v1_linear = registry.load_model("linear_predictor", version="1")
    print(f"Version 1 linear model output for x=5: {v1_linear(5)}")
    
    # Load classifier
    classifier_loaded = registry.load_model("simple_classifier")
    print(f"Classifier prediction for x=0.4: {classifier_loaded.predict(0.4)}")
    print(f"Classifier prediction for x=0.2: {classifier_loaded.predict(0.2)}")
    
    print("\n🔍 Model information:")
    linear_versions = registry.get_model_versions("linear_predictor")
    print(f"Linear predictor has {len(linear_versions)} versions")
    print(f"Latest version: {registry.get_latest_version('linear_predictor')}")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    example_usage()