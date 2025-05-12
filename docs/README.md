# Meet2Obsidian: Project Documentation

## Overview

Welcome to the meet2obsidian project documentation! Here you'll find all the necessary information for both users and developers.

## Documentation Structure

- [User Documentation](user/README.md) - guides for installation, configuration, and usage
- [Developer Documentation](dev/README.md) - information about architecture, components, and development process
- [API Documentation](api/README.md) - specifications for external and internal APIs
- [Examples](examples/) - examples of configurations, prompts, and templates

## About the Project

meet2obsidian is a command-line utility for macOS designed to automatically process meeting video recordings, transcribe them, and create structured notes in Obsidian. The system works in the background, monitoring a specified directory for new video files and automatically processing them.

## Project Status

Current implemented features:

- Basic infrastructure setup
- Configuration management
- API key management
- Structured logging system

### Recently Completed

- **Epic 7: Tests for the logging module** - Created comprehensive unit tests for the logging functionality
- **Epic 8: Implementation of logging module** - Implemented structured logging with structlog, file rotation, and various logging levels
- **Epic 9: Tests for secure API key storage** - Created unit and integration tests for secure storage of API keys in system keychain

### Coming Soon

- Audio extraction from video files
- Integration with Rev.ai API for transcription
- Integration with Claude API for notes generation
- Obsidian note creation and formatting

## Quick Start

For a quick start, see the [installation guide](user/getting-started/installation.md) in the user documentation section.

## Key Features

- **Automatic processing** of meeting recordings
- **Structured logging** with JSON format for better diagnostics
- **Flexible configuration** through YAML config files
- **Command-line interface** for easy operation
- **API integration** with Rev.ai and Claude
