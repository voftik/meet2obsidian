# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Meet2Obsidian is an automated tool for transcribing meeting recordings and creating structured notes in Obsidian. It:

1. Monitors for new MP4 files in a designated directory
2. Extracts audio (M4A) from video recordings
3. Transcribes speech using Rev.ai API
4. Analyzes content using Anthropic's Claude API to extract key information
5. Creates structured notes in Obsidian
6. Manages file cleanup and organization

## Development Environment

### Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install package in development mode
pip install -e .

# Install FFmpeg (required for audio extraction)
# On macOS:
brew install ffmpeg
```

### Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run a specific test file
pytest tests/unit/test_cli.py

# Run tests with specific markers
pytest -m "not integration"

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Run linting with flake8
flake8 meet2obsidian tests

# Run code formatting with black
black meet2obsidian tests

# Type checking with mypy
mypy meet2obsidian
```

## Architecture and Data Flow

Meet2Obsidian uses a pipeline architecture with several connected components:

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  File Monitor     │────▶│  Audio Processor  │────▶│  Transcription    │
│                   │     │                   │     │  Service (Rev.ai) │
└───────────────────┘     └───────────────────┘     └───────────────────┘
                                                              │
                                                              ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│                   │     │                   │     │                   │
│  Obsidian         │◀────│  Note Generator   │◀────│  Content Analyzer │
│  Integration      │     │                   │     │  (Claude API)     │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

Key components:

1. **Core Module** (`core.py`): Central orchestration of the processing pipeline
2. **Monitoring Module** (`monitor.py`): Uses watchdog to detect new MP4 files
3. **Audio Processing** (`audio/extractor.py`): Uses ffmpeg-python for extraction
4. **API Integration**:
   - `api/revai.py`: Handles Rev.ai API for transcription
   - `api/claude.py`: Manages Claude API for content analysis
5. **Note Generation**:
   - `note/generator.py`: Creates Markdown content from analysis
   - `note/obsidian.py`: Handles Obsidian vault integration
6. **Utility Modules**:
   - `utils/security.py`: Manages API keys in macOS Keychain
   - `utils/logging.py`: Structured logging with structlog
   - `utils/status.py`: Tracks processing status
   - `cache.py`: Optimizes API usage through local caching

The configuration system uses a hierarchical approach combining default settings, user configuration, and command-line overrides. API keys are stored securely in macOS Keychain.

## Key Design Patterns

1. **Pipeline Processing**: Files flow through sequential processing stages
2. **Publisher-Subscriber**: For file monitoring and event handling
3. **Template Method**: For customizable note generation
4. **Strategy Pattern**: For different analysis approaches
5. **Caching**: For optimizing API usage and performance

## CLI Commands

The main interface for users is through the CLI:

```bash
# Start the service
meet2obsidian start

# Check status
meet2obsidian status

# Stop the service
meet2obsidian stop

# Configure settings
meet2obsidian config

# Test configuration and API connections
meet2obsidian test

# View logs
meet2obsidian logs
```

## Development Tasks

### Setting up API Keys for Development

The KeychainManager in `utils/security.py` provides methods for storing and retrieving API keys:

```python
# Example usage in tests or development
from meet2obsidian.utils.security import KeychainManager

# Create manager instance
keychain = KeychainManager()

# Store API keys (during development/testing)
keychain.store_api_key('rev_ai', 'your-rev-ai-key')
keychain.store_api_key('claude', 'your-claude-key')

# Retrieve keys
rev_ai_key = keychain.get_api_key('rev_ai')
```

## LaunchAgent Integration

The project includes a script (`scripts/setup_launchagent.sh`) to set up Meet2Obsidian as a LaunchAgent for automatic startup on macOS.