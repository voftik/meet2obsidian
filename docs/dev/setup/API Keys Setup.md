# API Keys Setup Script

## Overview

The `setup_api_keys.py` script provides a command-line interface for managing API keys used by meet2obsidian. It allows developers and users to securely set, test, list, and delete API keys for Rev.ai and Claude services.

## Features

- **Set API Keys**: Store API keys securely in macOS Keychain
- **Test API Keys**: Verify API keys before storing them
- **List API Keys**: Display stored API keys with masked values
- **Delete API Keys**: Remove API keys from the secure storage
- **Interactive Setup**: Guided setup process for all required API keys
- **Rich Formatting**: Enhanced terminal output with color and formatting (when available)
- **Graceful Degradation**: Works even with minimal dependencies

## Architecture

The script integrates with the main meet2obsidian application through the `KeychainManager` class in the `meet2obsidian.utils.security` module. It also provides a fallback implementation when run in standalone mode.

```
┌────────────────────┐      ┌─────────────────────────┐
│                    │      │                         │
│  setup_api_keys.py │◄────►│ KeychainManager (utils) │
│                    │      │                         │
└────────────────────┘      └─────────────────────────┘
         │                             │
         │                             │
         ▼                             ▼
┌────────────────────┐      ┌─────────────────────────┐
│                    │      │                         │
│     API Tests      │      │    macOS Keychain       │
│  (Rev.ai, Claude)  │      │                         │
│                    │      │                         │
└────────────────────┘      └─────────────────────────┘
```

## Usage

### Installation Requirements

The script has the following optional dependencies:
- `keyring`: For secure storage of API keys
- `requests`: For testing API keys
- `rich`: For enhanced terminal output

While all dependencies are included in the `requirements.txt` file, the script is designed to work even if some dependencies are missing, using fallback mechanisms.

### Command-Line Interface

```bash
# View help
./scripts/setup_api_keys.py --help

# Set an API key
./scripts/setup_api_keys.py set rev_ai
./scripts/setup_api_keys.py set claude --value "your_api_key"
./scripts/setup_api_keys.py set rev_ai --test

# Get an API key (masked)
./scripts/setup_api_keys.py get rev_ai

# List all API keys
./scripts/setup_api_keys.py list

# Delete an API key
./scripts/setup_api_keys.py delete rev_ai

# Test an API key
./scripts/setup_api_keys.py test claude
./scripts/setup_api_keys.py test rev_ai --value "your_api_key"

# Interactive setup
./scripts/setup_api_keys.py interactive
```

## Security Considerations

- API keys are stored securely in macOS Keychain
- API keys are masked when displayed (only first 4 characters shown)
- Input is hidden when entering API keys interactively
- Temporary storage in standalone mode is only used when Keychain is unavailable

## Integration Points

The script integrates with the following components:

1. **meet2obsidian.utils.security**: Uses the `KeychainManager` class for secure storage
2. **meet2obsidian.utils.logging**: Uses the logging utilities for consistent log output
3. **Rich library**: Uses Rich for enhanced terminal output when available
4. **Rev.ai API**: Tests Rev.ai API keys by making a simple request
5. **Claude API**: Tests Claude API keys by making a simple request

## Fallback Mechanisms

The script includes fallback mechanisms for when dependencies are missing:

1. **Keychain Fallback**: When the `keyring` package is not available, it uses a simple file-based storage solution
2. **Logging Fallback**: When the `meet2obsidian` logging utilities are not available, it uses Python's built-in logging
3. **Formatting Fallback**: When the `rich` package is not available, it falls back to plain text output
4. **API Testing Fallback**: When the `requests` package is not available, it provides a clear error message

## Testing

To test the script without interacting with the actual APIs:

```bash
# Test with mock API responses
./scripts/setup_api_keys.py set rev_ai --value "test_key" --no-test
./scripts/setup_api_keys.py list
./scripts/setup_api_keys.py delete rev_ai
```

## Error Handling

The script handles various error scenarios gracefully:

- Missing dependencies
- Invalid API keys
- Network errors
- Permission issues
- Empty or invalid input

## Future Improvements

- Add support for additional API keys
- Add validation of API key format before testing
- Add offline mode for environments without internet access
- Add batch import/export of API keys