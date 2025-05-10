#!/bin/bash

# Script for creating meet2obsidian project documentation structure
# Author: Claude
# Date: 2025-05-10

set -e  # Stop on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to create directories
create_directory() {
    if [ ! -d "$1" ]; then
        mkdir -p "$1"
        echo -e "${GREEN}Directory created:${NC} $1"
    else
        echo -e "${YELLOW}Directory already exists:${NC} $1"
    fi
}

# Function to create files with content
create_file() {
    if [ ! -f "$1" ]; then
        echo -e "$2" > "$1"
        echo -e "${GREEN}File created:${NC} $1"
    else
        echo -e "${YELLOW}File already exists:${NC} $1"
    fi
}

# Function to copy existing API specifications
copy_api_specs() {
    if [ -f "claude-api-spec.md" ]; then
        cp "claude-api-spec.md" "docs/api/claude.md"
        echo -e "${GREEN}Claude API specification copied${NC}"
    else
        echo -e "${YELLOW}Claude API specification not found${NC}"
    fi
    
    # Add similar code for Rev.ai API specification if it exists
}

# Function to print completion message
print_completion_message() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${GREEN}Documentation structure created successfully!${NC}"
    echo -e "${BLUE}========================================${NC}\n"
    echo -e "Root directory: ${YELLOW}docs/${NC}"
    echo -e "User documentation: ${YELLOW}docs/user/${NC}"
    echo -e "Developer documentation: ${YELLOW}docs/dev/${NC}"
    echo -e "API specifications: ${YELLOW}docs/api/${NC}"
    echo -e "Resources: ${YELLOW}docs/assets/${NC}"
    echo -e "Examples: ${YELLOW}docs/examples/${NC}\n"
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "1. Fill README.md files with appropriate content"
    echo -e "2. Add actual component documentation"
    echo -e "3. Create user guides for main features"
    echo -e "4. Update API specifications if needed\n"
}