#!/bin/bash

# Simple script to create the directory structure only
echo "Creating documentation directory structure..."

# Create main directories
mkdir -p docs
mkdir -p docs/user
mkdir -p docs/dev
mkdir -p docs/api
mkdir -p docs/assets
mkdir -p docs/examples

# Create user documentation subdirectories
mkdir -p docs/user/getting-started
mkdir -p docs/user/usage
mkdir -p docs/user/troubleshooting
mkdir -p docs/user/advanced

# Create developer documentation subdirectories
mkdir -p docs/dev/architecture
mkdir -p docs/dev/setup
mkdir -p docs/dev/development
mkdir -p docs/dev/components
mkdir -p docs/dev/roadmap

# Create API documentation subdirectories
mkdir -p docs/api/internal

# Create assets subdirectories
mkdir -p docs/assets/images/screenshots
mkdir -p docs/assets/diagrams/mermaid
mkdir -p docs/assets/diagrams/drawio
mkdir -p docs/assets/templates

# Create examples subdirectories
mkdir -p docs/examples/config-examples
mkdir -p docs/examples/prompt-examples
mkdir -p docs/examples/template-examples

# Copy existing API specifications if they exist
if [ -f "claude-api-spec.md" ]; then
    cp claude-api-spec.md docs/api/claude.md
    echo "Copied Claude API specification"
fi

if [ -f "revai-api-spec.md" ]; then
    cp revai-api-spec.md docs/api/rev-ai.md
    echo "Copied Rev.ai API specification"
fi

echo "Directory structure created successfully!"
ls -la docs/
