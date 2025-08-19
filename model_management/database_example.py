"""
Example usage of Model Registry with Database Backend
Shows SQLite database integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from model_management import create_registry


# Define models at module level so they can be pickled
def linear_model_v1(x):
    return 2 * x + 1

def linear_model_v2(x):
    return 3 * x + 2  # Improved coefficients

class SimpleClassifier:
    def __init__(self, threshold=0.5):
        self.threshold = threshold
    
    def predict(self, x):
        return 1 if x > self.threshold else 0


def test_database_backend():
    """Test the database backend functionality"""
    
    print("🗄️ Model Registry Database Backend Example")
    print("=" * 60)
    
    # Create registry with database backend
    print("\n📊 Creating registry with SQLite database...")
    registry = create_registry("database", 
                              path="./db_models", 
                              db_path="./db_models/registry.db")
    
    print("✅ Database backend initialized")
    
    # Save some models
    print("\n💾 Saving models to database...")
    
    v1 = registry.save_model(
        linear_model_v1, 
        "linear_predictor", 
        "Original linear model",
        tags={"type": "regression", "complexity": "low", "author": "team_a"}
    )
    
    v2 = registry.save_model(
        linear_model_v2,
        "linear_predictor",
        "Enhanced linear model with better coefficients",
        tags={"type": "regression", "complexity": "low", "author": "team_b"}
    )
    
    classifier = SimpleClassifier(threshold=0.3)
    v3 = registry.save_model(
        classifier,
        "binary_classifier",
        "Threshold-based binary classifier",
        tags={"type": "classification", "threshold": 0.3, "author": "team_a"}
    )
    
    # Another classifier version
    classifier_v2 = SimpleClassifier(threshold=0.7)
    v4 = registry.save_model(
        classifier_v2,
        "binary_classifier", 
        "Updated classifier with higher threshold",
        tags={"type": "classification", "threshold": 0.7, "author": "team_c"}
    )
    
    print(f"📦 Saved 4 model versions to database")
    
    # Test database persistence - create new registry instance
    print("\n🔄 Testing database persistence...")
    registry2 = create_registry("database", 
                               path="./db_models", 
                               db_path="./db_models/registry.db")
    
    print("📋 Models loaded from database:")
    all_models = registry2.list_models()
    for name, versions in all_models.items():
        print(f"\n🎯 {name}:")
        for version_info in versions:
            print(f"  v{version_info['version']}: {version_info['description']}")
            print(f"    Tags: {version_info['tags']}")
            print(f"    Size: {version_info['file_size']} bytes")
    
    # Test model loading
    print("\n🧪 Testing model loading...")
    latest_linear = registry2.load_model("linear_predictor")
    print(f"Latest linear model (v{registry2.get_latest_version('linear_predictor')}) output for x=5: {latest_linear(5)}")
    
    specific_linear = registry2.load_model("linear_predictor", version="1")
    print(f"Linear model v1 output for x=5: {specific_linear(5)}")
    
    classifier_loaded = registry2.load_model("binary_classifier")
    print(f"Latest classifier prediction for x=0.5: {classifier_loaded.predict(0.5)}")
    
    # Test database-specific features
    print("\n📊 Database Statistics:")
    db_backend = registry2.metadata_backend.backend
    stats = db_backend.get_statistics()
    
    print(f"Total models: {stats['summary']['total_models']}")
    print(f"Total versions: {stats['summary']['total_versions']}")
    print(f"Total size: {stats['summary']['total_size_mb']} MB")
    
    print("\nPer-model statistics:")
    for name, model_stats in stats['models'].items():
        print(f"  {name}: {model_stats['version_count']} versions, {model_stats['total_size_mb']} MB")
    
    # Test tag searching
    print("\n🔍 Searching by tags:")
    regression_models = db_backend.find_models_by_tag("type", "regression")
    print(f"Regression models: {len(regression_models)} found")
    for model in regression_models:
        print(f"  {model['name']} v{model['version']}: {model['description']}")
    
    team_a_models = db_backend.find_models_by_tag("author", "team_a") 
    print(f"Team A models: {len(team_a_models)} found")
    for model in team_a_models:
        print(f"  {model['name']} v{model['version']} by {model['tag_value']}")
    
    print("\n✅ Database backend test completed successfully!")
    print(f"📁 Database file: ./db_models/registry.db")
    print("💡 You can inspect the database with any SQLite browser")


if __name__ == "__main__":
    test_database_backend()