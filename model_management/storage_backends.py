"""
Abstract Storage Layer for Model Registry
Supports multiple storage backends: local, S3, etc.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import os
import pickle
import json


class StorageBackend(ABC):
    """Abstract base class for storage backends"""
    
    @abstractmethod
    def save_model(self, model: Any, path: str) -> None:
        """Save model to storage"""
        pass
    
    @abstractmethod
    def load_model(self, path: str) -> Any:
        """Load model from storage"""
        pass
    
    @abstractmethod
    def delete_model(self, path: str) -> None:
        """Delete model from storage"""
        pass
    
    @abstractmethod
    def model_exists(self, path: str) -> bool:
        """Check if model exists"""
        pass
    
    @abstractmethod
    def get_model_size(self, path: str) -> int:
        """Get model file size"""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, base_path: str = "./models"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
    
    def save_model(self, model: Any, path: str) -> None:
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            pickle.dump(model, f)
    
    def load_model(self, path: str) -> Any:
        full_path = os.path.join(self.base_path, path)
        with open(full_path, 'rb') as f:
            return pickle.load(f)
    
    def delete_model(self, path: str) -> None:
        full_path = os.path.join(self.base_path, path)
        if os.path.exists(full_path):
            os.remove(full_path)
    
    def model_exists(self, path: str) -> bool:
        full_path = os.path.join(self.base_path, path)
        return os.path.exists(full_path)
    
    def get_model_size(self, path: str) -> int:
        full_path = os.path.join(self.base_path, path)
        return os.path.getsize(full_path)


class S3StorageBackend(StorageBackend):
    """S3 storage backend (placeholder - can be implemented later)"""
    
    def __init__(self, bucket_name: str, aws_access_key: str = None):
        self.bucket_name = bucket_name
        # TODO: Initialize S3 client
        raise NotImplementedError("S3 backend coming soon!")
    
    def save_model(self, model: Any, path: str) -> None:
        # TODO: Upload to S3
        pass
    
    def load_model(self, path: str) -> Any:
        # TODO: Download from S3 and load
        pass
    
    def delete_model(self, path: str) -> None:
        # TODO: Delete from S3
        pass
    
    def model_exists(self, path: str) -> bool:
        # TODO: Check if exists in S3
        pass
    
    def get_model_size(self, path: str) -> int:
        # TODO: Get object size from S3
        pass


class MetadataBackend(ABC):
    """Abstract base class for metadata storage"""
    
    @abstractmethod
    def save_metadata(self, metadata: Dict) -> None:
        """Save metadata"""
        pass
    
    @abstractmethod
    def load_metadata(self) -> Dict:
        """Load metadata"""
        pass


class JSONMetadataBackend(MetadataBackend):
    """JSON file metadata backend"""
    
    def __init__(self, file_path: str = "./models/registry.json"):
        self.file_path = file_path
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    def save_metadata(self, metadata: Dict) -> None:
        with open(self.file_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_metadata(self) -> Dict:
        if os.path.exists(self.file_path):
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {}


class DatabaseMetadataBackend(MetadataBackend):
    """Database metadata backend using SQLite"""
    
    def __init__(self, db_path: str = "./models/registry.db"):
        from .database.database_manager import SQLiteMetadataBackend
        self.backend = SQLiteMetadataBackend(db_path)
        self._current_metadata = {}
    
    def save_metadata(self, metadata: Dict) -> None:
        """Save metadata - detect changes and update database"""
        # Find new or updated model versions by comparing with current state
        for model_name, versions in metadata.items():
            if model_name not in self._current_metadata:
                # New model - save all versions
                for version_info in versions:
                    self.backend.save_model_metadata(version_info)
            else:
                # Existing model - save only new versions
                existing_versions = {v['version'] for v in self._current_metadata[model_name]}
                for version_info in versions:
                    if version_info['version'] not in existing_versions:
                        self.backend.save_model_metadata(version_info)
        
        # Update our current state
        self._current_metadata = metadata.copy()
    
    def load_metadata(self) -> Dict:
        """Load metadata from database"""
        metadata = self.backend.load_metadata()
        self._current_metadata = metadata
        return metadata