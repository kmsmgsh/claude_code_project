#!/bin/bash

# Build script for MLOps Management System Documentation

set -e

echo "🔧 Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "📦 Installing dependencies..."
source venv/bin/activate
pip install -q mkdocs mkdocs-material mkdocs-mermaid2-plugin

echo "🏗️ Building documentation..."
mkdocs build

echo "✅ Documentation built successfully!"
echo "📁 Static files are in: ./site/"
echo "🌐 To serve locally, run: mkdocs serve"
echo "🚀 To deploy, copy the ./site/ directory to your web server"