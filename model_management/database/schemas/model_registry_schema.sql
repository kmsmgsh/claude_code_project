-- Model Registry Schema
-- Table prefix: mr_ (model registry)
-- Compatible with SQLite, PostgreSQL, MySQL

-- Models table: stores unique model names
CREATE TABLE IF NOT EXISTS mr_models (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Model versions table: stores each version of a model
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

-- Model tags table: stores key-value tags for model versions
CREATE TABLE IF NOT EXISTS mr_model_tags (
    id INTEGER PRIMARY KEY,
    model_version_id INTEGER NOT NULL,
    tag_key TEXT NOT NULL,
    tag_value TEXT,
    
    FOREIGN KEY (model_version_id) REFERENCES mr_model_versions(id) ON DELETE CASCADE,
    UNIQUE(model_version_id, tag_key)
);

-- Performance indexes for model registry
CREATE INDEX IF NOT EXISTS idx_mr_models_name ON mr_models(name);
CREATE INDEX IF NOT EXISTS idx_mr_model_versions_model_id ON mr_model_versions(model_id);
CREATE INDEX IF NOT EXISTS idx_mr_model_versions_version ON mr_model_versions(version);
CREATE INDEX IF NOT EXISTS idx_mr_model_tags_key ON mr_model_tags(tag_key);
CREATE INDEX IF NOT EXISTS idx_mr_model_tags_key_value ON mr_model_tags(tag_key, tag_value);