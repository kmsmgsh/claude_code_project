"""
Model Management Package
Simple, extensible model registry with pluggable storage backends
"""

from .model_registry import ModelRegistry, create_registry
from .storage_backends import (
    StorageBackend, 
    LocalStorageBackend, 
    S3StorageBackend,
    MetadataBackend,
    JSONMetadataBackend,
    DatabaseMetadataBackend
)

__version__ = "0.1.0"
__all__ = [
    "ModelRegistry",
    "create_registry", 
    "StorageBackend",
    "LocalStorageBackend",
    "S3StorageBackend", 
    "MetadataBackend",
    "JSONMetadataBackend",
    "DatabaseMetadataBackend"
]