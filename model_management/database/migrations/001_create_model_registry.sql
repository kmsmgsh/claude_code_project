-- Migration 001: Create Model Registry Tables
-- Date: 2025-08-19
-- Description: Initial model registry schema with models, versions, and tags

-- Create models table
CREATE TABLE IF NOT EXISTS mr_models (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Create model versions table
CREATE TABLE IF NOT EXISTS mr_model_versions (
    id INTEGER PRIMARY KEY,
    model_id INTEGER NOT NULL,
    version TEXT NOT NULL,
    description TEXT,
    storage_path TEXT NOT NULL,
    file_size_bytes INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    
    FOREIGN KEY (model_id) REFERENCES mr_models(id) ON DELETE CASCADE,
    UNIQUE(model_id, version)
);

-- Create model tags table
CREATE TABLE IF NOT EXISTS mr_model_tags (
    id INTEGER PRIMARY KEY,
    model_version_id INTEGER NOT NULL,
    tag_key TEXT NOT NULL,
    tag_value TEXT,
    
    FOREIGN KEY (model_version_id) REFERENCES mr_model_versions(id) ON DELETE CASCADE,
    UNIQUE(model_version_id, tag_key)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_mr_models_name ON mr_models(name);
CREATE INDEX IF NOT EXISTS idx_mr_model_versions_model_id ON mr_model_versions(model_id);
CREATE INDEX IF NOT EXISTS idx_mr_model_versions_version ON mr_model_versions(version);
CREATE INDEX IF NOT EXISTS idx_mr_model_tags_key ON mr_model_tags(tag_key);
CREATE INDEX IF NOT EXISTS idx_mr_model_tags_key_value ON mr_model_tags(tag_key, tag_value);

-- Migration tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

INSERT OR IGNORE INTO schema_migrations (version, applied_at) 
VALUES ('001', datetime('now'));