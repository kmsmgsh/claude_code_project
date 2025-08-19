"""
Model Registry with Abstract Storage Layer
Can use different storage backends (local, S3, etc.)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from .storage_backends import StorageBackend, MetadataBackend, LocalStorageBackend, JSONMetadataBackend, DatabaseMetadataBackend


class ModelRegistry:
    """Model registry with pluggable storage backends"""
    
    def __init__(self, 
                 storage_backend: StorageBackend = None,
                 metadata_backend: MetadataBackend = None):
        """
        Initialize model registry with storage backends
        
        Args:
            storage_backend: Where to store model files
            metadata_backend: Where to store metadata
        """
        # Use defaults if not provided
        self.storage_backend = storage_backend or LocalStorageBackend()
        self.metadata_backend = metadata_backend or JSONMetadataBackend()
        
        # Load existing metadata
        self.metadata = self.metadata_backend.load_metadata()
    
    def save_model(self, model: Any, name: str, description: str = "", tags: Dict = None) -> str:
        """
        Save a model to the registry
        
        Args:
            model: The trained model object
            name: Name for the model
            description: Optional description
            tags: Optional metadata tags
            
        Returns:
            version: The version string assigned to this model
        """
        # Generate version
        version = self._get_next_version(name)
        
        # Create storage path
        model_path = f"{name}/v{version}/model.pkl"
        
        # Save the model using storage backend
        self.storage_backend.save_model(model, model_path)
        
        # Create metadata
        model_info = {
            "name": name,
            "version": version,
            "description": description,
            "tags": tags or {},
            "created_at": datetime.now().isoformat(),
            "storage_path": model_path,
            "file_size": self.storage_backend.get_model_size(model_path)
        }
        
        # Update metadata
        if name not in self.metadata:
            self.metadata[name] = []
        self.metadata[name].append(model_info)
        
        # Save metadata
        self.metadata_backend.save_metadata(self.metadata)
        
        print(f"✅ Model '{name}' version {version} saved successfully")
        return version
    
    def load_model(self, name: str, version: Optional[str] = None) -> Any:
        """
        Load a model from the registry
        
        Args:
            name: Name of the model
            version: Specific version (if None, loads latest)
            
        Returns:
            The loaded model object
        """
        model_info = self._get_model_info(name, version)
        
        # Load using storage backend
        model = self.storage_backend.load_model(model_info['storage_path'])
        
        print(f"📦 Loaded model '{name}' version {model_info['version']}")
        return model
    
    def delete_model(self, name: str, version: Optional[str] = None) -> None:
        """Delete a model version"""
        model_info = self._get_model_info(name, version)
        
        # Delete from storage
        self.storage_backend.delete_model(model_info['storage_path'])
        
        # Remove from metadata
        self.metadata[name] = [
            info for info in self.metadata[name] 
            if info['version'] != model_info['version']
        ]
        
        # Clean up empty model entries
        if not self.metadata[name]:
            del self.metadata[name]
        
        # Save updated metadata
        self.metadata_backend.save_metadata(self.metadata)
        
        print(f"🗑️ Deleted model '{name}' version {model_info['version']}")
    
    def list_models(self) -> Dict[str, List[Dict]]:
        """List all models in the registry"""
        return self.metadata
    
    def get_model_versions(self, name: str) -> List[Dict]:
        """Get all versions of a specific model"""
        if name not in self.metadata:
            raise ValueError(f"Model '{name}' not found in registry")
        return self.metadata[name]
    
    def get_latest_version(self, name: str) -> str:
        """Get the latest version number of a model"""
        if name not in self.metadata:
            raise ValueError(f"Model '{name}' not found in registry")
        
        latest = max(self.metadata[name], key=lambda x: int(x['version']))
        return latest['version']
    
    def _get_model_info(self, name: str, version: Optional[str] = None) -> Dict:
        """Get model info for a specific version"""
        if name not in self.metadata:
            raise ValueError(f"Model '{name}' not found in registry")
        
        if version is None:
            # Get latest version
            return max(self.metadata[name], key=lambda x: int(x['version']))
        else:
            # Find specific version
            for info in self.metadata[name]:
                if info['version'] == version:
                    return info
            raise ValueError(f"Model '{name}' version '{version}' not found")
    
    def _get_next_version(self, name: str) -> str:
        """Get the next version number for a model"""
        if name not in self.metadata or not self.metadata[name]:
            return "1"
        
        max_version = max(int(info['version']) for info in self.metadata[name])
        return str(max_version + 1)


# Factory function to create different registry configurations
def create_registry(storage_type: str = "local", **kwargs) -> ModelRegistry:
    """
    Factory function to create model registry with different backends
    
    Args:
        storage_type: "local", "database", "s3", etc.
        **kwargs: Backend-specific configuration
    """
    if storage_type == "local":
        storage_backend = LocalStorageBackend(kwargs.get("path", "./models"))
        metadata_backend = JSONMetadataBackend(kwargs.get("metadata_path", "./models/registry.json"))
    elif storage_type == "database":
        storage_backend = LocalStorageBackend(kwargs.get("path", "./models"))
        metadata_backend = DatabaseMetadataBackend(kwargs.get("db_path", "./models/registry.db"))
    elif storage_type == "s3":
        # TODO: Implement S3 backend
        raise NotImplementedError("S3 backend not implemented yet")
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
    
    return ModelRegistry(storage_backend, metadata_backend)