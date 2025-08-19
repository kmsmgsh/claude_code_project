"""
Database Manager for Model Registry
Handles SQLite database operations with raw SQL
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database connections and operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_database_exists()
        self._run_migrations()
    
    def _ensure_database_exists(self):
        """Create database directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _run_migrations(self):
        """Run database migrations"""
        migration_file = os.path.join(
            os.path.dirname(__file__), 
            "migrations", 
            "001_create_model_registry.sql"
        )
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        with self.get_connection() as conn:
            conn.executescript(migration_sql)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


class SQLiteMetadataBackend:
    """SQLite implementation of MetadataBackend using raw SQL"""
    
    def __init__(self, db_path: str = "./models/registry.db"):
        self.db_manager = DatabaseManager(db_path)
    
    def save_model_metadata(self, model_info: Dict) -> None:
        """Save model metadata to database"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Insert or get model
            model_id = self._get_or_create_model(cursor, model_info['name'])
            
            # 2. Insert model version
            cursor.execute("""
                INSERT INTO mr_model_versions 
                (model_id, version, description, storage_path, file_size_bytes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                model_id,
                model_info['version'],
                model_info.get('description', ''),
                model_info['storage_path'],
                model_info.get('file_size', 0),
                model_info['created_at']
            ))
            
            version_id = cursor.lastrowid
            
            # 3. Insert tags if any
            if 'tags' in model_info and model_info['tags']:
                for tag_key, tag_value in model_info['tags'].items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO mr_model_tags 
                        (model_version_id, tag_key, tag_value)
                        VALUES (?, ?, ?)
                    """, (version_id, tag_key, str(tag_value)))
    
    def load_metadata(self) -> Dict:
        """Load all metadata in the format expected by ModelRegistry"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all models with their versions
            cursor.execute("""
                SELECT 
                    m.name,
                    mv.version,
                    mv.description,
                    mv.storage_path,
                    mv.file_size_bytes,
                    mv.created_at,
                    mv.id as version_id
                FROM mr_models m
                JOIN mr_model_versions mv ON m.id = mv.model_id
                ORDER BY m.name, CAST(mv.version AS INTEGER)
            """)
            
            models_data = {}
            version_ids = []
            
            for row in cursor.fetchall():
                model_name = row['name']
                if model_name not in models_data:
                    models_data[model_name] = []
                
                version_info = {
                    'name': model_name,
                    'version': row['version'],
                    'description': row['description'],
                    'storage_path': row['storage_path'],
                    'file_size': row['file_size_bytes'],
                    'created_at': row['created_at'],
                    'tags': {}
                }
                
                models_data[model_name].append(version_info)
                version_ids.append((row['version_id'], len(models_data[model_name]) - 1, model_name))
            
            # Get all tags
            if version_ids:
                version_id_list = [str(vid) for vid, _, _ in version_ids]
                cursor.execute(f"""
                    SELECT model_version_id, tag_key, tag_value
                    FROM mr_model_tags
                    WHERE model_version_id IN ({','.join(['?'] * len(version_id_list))})
                """, version_id_list)
                
                # Map tags back to versions
                for row in cursor.fetchall():
                    version_id = row['model_version_id']
                    # Find the corresponding model and version
                    for vid, version_idx, model_name in version_ids:
                        if vid == version_id:
                            models_data[model_name][version_idx]['tags'][row['tag_key']] = row['tag_value']
                            break
            
            return models_data
    
    def delete_model_version(self, name: str, version: str) -> None:
        """Delete a specific model version"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM mr_model_versions 
                WHERE model_id = (SELECT id FROM mr_models WHERE name = ?)
                AND version = ?
            """, (name, version))
            
            # Clean up model if no versions left
            cursor.execute("""
                DELETE FROM mr_models 
                WHERE id NOT IN (SELECT DISTINCT model_id FROM mr_model_versions)
            """)
    
    def get_statistics(self) -> Dict:
        """Get comprehensive statistics about models"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get overall stats
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT m.id) as total_models,
                    COUNT(mv.id) as total_versions,
                    SUM(mv.file_size_bytes) as total_size_bytes
                FROM mr_models m
                LEFT JOIN mr_model_versions mv ON m.id = mv.model_id
            """)
            
            stats = cursor.fetchone()
            
            # Get per-model stats
            cursor.execute("""
                SELECT 
                    m.name,
                    COUNT(mv.id) as version_count,
                    SUM(mv.file_size_bytes) as total_size_bytes,
                    MAX(CAST(mv.version AS INTEGER)) as latest_version,
                    MAX(mv.created_at) as latest_created_at
                FROM mr_models m
                LEFT JOIN mr_model_versions mv ON m.id = mv.model_id
                GROUP BY m.id, m.name
            """)
            
            model_stats = {}
            for row in cursor.fetchall():
                model_stats[row['name']] = {
                    'version_count': row['version_count'],
                    'total_size_bytes': row['total_size_bytes'] or 0,
                    'total_size_mb': round((row['total_size_bytes'] or 0) / (1024 * 1024), 2),
                    'latest_version': str(row['latest_version']) if row['latest_version'] else '0',
                    'latest_created_at': row['latest_created_at']
                }
            
            return {
                'summary': {
                    'total_models': stats['total_models'],
                    'total_versions': stats['total_versions'],
                    'total_size_bytes': stats['total_size_bytes'] or 0,
                    'total_size_mb': round((stats['total_size_bytes'] or 0) / (1024 * 1024), 2)
                },
                'models': model_stats
            }
    
    def find_models_by_tag(self, tag_key: str, tag_value: str = None) -> List[Dict]:
        """Find models by tag"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if tag_value is None:
                cursor.execute("""
                    SELECT 
                        m.name,
                        mv.version,
                        mv.description,
                        mt.tag_key,
                        mt.tag_value,
                        mv.created_at
                    FROM mr_models m
                    JOIN mr_model_versions mv ON m.id = mv.model_id
                    JOIN mr_model_tags mt ON mv.id = mt.model_version_id
                    WHERE mt.tag_key = ?
                    ORDER BY m.name, CAST(mv.version AS INTEGER)
                """, (tag_key,))
            else:
                cursor.execute("""
                    SELECT 
                        m.name,
                        mv.version,
                        mv.description,
                        mt.tag_key,
                        mt.tag_value,
                        mv.created_at
                    FROM mr_models m
                    JOIN mr_model_versions mv ON m.id = mv.model_id
                    JOIN mr_model_tags mt ON mv.id = mt.model_version_id
                    WHERE mt.tag_key = ? AND mt.tag_value = ?
                    ORDER BY m.name, CAST(mv.version AS INTEGER)
                """, (tag_key, tag_value))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'name': row['name'],
                    'version': row['version'],
                    'description': row['description'],
                    'tag_key': row['tag_key'],
                    'tag_value': row['tag_value'],
                    'created_at': row['created_at']
                })
            
            return results
    
    def _get_or_create_model(self, cursor, name: str) -> int:
        """Get existing model ID or create new model"""
        # Try to get existing model
        cursor.execute("SELECT id FROM mr_models WHERE name = ?", (name,))
        row = cursor.fetchone()
        
        if row:
            return row['id']
        
        # Create new model
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO mr_models (name, created_at, updated_at)
            VALUES (?, ?, ?)
        """, (name, now, now))
        
        return cursor.lastrowid