import sqlite3

# Check what's actually in the database
db_path = "./db_models/registry.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== Database Contents ===")
    
    # Check models table
    cursor.execute("SELECT * FROM mr_models")
    models = cursor.fetchall()
    print(f"Models table: {models}")
    
    # Check versions table
    cursor.execute("SELECT * FROM mr_model_versions")
    versions = cursor.fetchall()
    print(f"Versions table: {versions}")
    
    # Check tags table
    cursor.execute("SELECT * FROM mr_model_tags")
    tags = cursor.fetchall()
    print(f"Tags table: {tags}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")