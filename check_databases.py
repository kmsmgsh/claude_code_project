import sqlite3
import os

def check_db(db_path):
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM mr_models")
        model_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM mr_model_versions") 
        version_count = cursor.fetchone()[0]
        conn.close()
        print(f"{db_path}: {model_count} models, {version_count} versions")
        return model_count > 0
    else:
        print(f"{db_path}: Not found")
        return False

print("🔍 Checking databases...")
check_db("./api_models/registry.db")  # Root level
check_db("./api/api_models/registry.db")  # Inside api dir