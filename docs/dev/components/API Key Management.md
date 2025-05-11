# API Key Management

## Overview

Meet2Obsidian uses the macOS Keychain to securely store API keys for Rev.ai and Claude. This approach ensures that sensitive credentials are never stored in plain text configuration files while still allowing automatic access from the application.

## Components

### KeychainManager

The `KeychainManager` class handles all interactions with the macOS Keychain, providing methods to store, retrieve, and delete API keys.

**Location**: `meet2obsidian/utils/security.py`

**Usage**:

```python
from meet2obsidian.utils.security import KeychainManager

# Initialize the manager
keychain = KeychainManager()

# Store an API key
keychain.store_api_key("rev_ai", "your-api-key")

# Retrieve an API key
api_key = keychain.get_api_key("rev_ai")

# Delete an API key
keychain.delete_api_key("rev_ai")
```

### API Key Setup Tool

A command-line utility is provided for managing API keys, including validation and storage.

**Location**: `scripts/setup_api_keys.py`

**Usage**:

```bash
# Set API keys
python scripts/setup_api_keys.py --revai YOUR_REVAI_API_KEY --claude YOUR_CLAUDE_API_KEY

# Test existing API keys
python scripts/setup_api_keys.py --test

# Get help
python scripts/setup_api_keys.py --help
```

## Key Storage Architecture

1. **Service Name**: All keys are stored under the service name "meet2obsidian"
2. **Key Identifiers**:
   - `rev_ai` - For Rev.ai transcription service
   - `claude` - For Claude AI text analysis service
3. **Access Control**: Keys are accessible only to the user who stored them

## API Key Validation

Before storing API keys, Meet2Obsidian validates them to ensure they're working correctly:

1. **Rev.ai Keys**: Validated by making a request to the account information endpoint
2. **Claude Keys**: Validated by sending a simple test message to the API

Only valid keys are stored in the Keychain.

## Integration with API Clients

API clients in Meet2Obsidian automatically retrieve the appropriate keys from the Keychain, requiring zero configuration from the user beyond the initial setup.

**Rev.ai Client Integration**:
```python
from meet2obsidian.utils.security import KeychainManager

class RevAiClient:
    def __init__(self):
        keychain = KeychainManager()
        self.api_key = keychain.get_api_key("rev_ai")
        # Initialize Rev.ai client with the retrieved key
```

**Claude Client Integration**:
```python
from meet2obsidian.utils.security import KeychainManager

class ClaudeClient:
    def __init__(self):
        keychain = KeychainManager()
        self.api_key = keychain.get_api_key("claude")
        # Initialize Claude client with the retrieved key
```

## Security Considerations

1. **No Plain Text Storage**: API keys are never stored in configuration files or source code
2. **System-Level Protection**: macOS Keychain provides encryption and access control
3. **No Logging**: API key values are never logged, only operation results
4. **Automatic Access**: No password prompts during normal operation
5. **Isolation**: Keys are stored with a unique service name to avoid conflicts

## Technical Requirements

1. **Dependencies**:
   - `keyring` Python package for Keychain access
   - macOS operating system
   - Access to user's Keychain

2. **Potential Issues**:
   - First-time access to Keychain may trigger a system permission dialog
   - Application must run under the same user account that stored the keys

## Troubleshooting

If you encounter issues with API key access:

1. **Check Key Existence**:
   ```bash
   python scripts/setup_api_keys.py --test
   ```

2. **Keychain Access Issues**:
   - Ensure the application has access to Keychain (check System Preferences)
   - Try re-saving the keys with the setup script

3. **Invalid Keys**:
   - Keys may have expired or been revoked
   - API services may be experiencing issues
   - Re-save valid keys using the setup script

## Key Rotation Best Practices

For optimal security, consider:

1. Rotating API keys periodically (every 3-6 months)
2. Immediately rotating keys if you suspect they've been compromised
3. Using the setup script to validate and store new keys after rotation