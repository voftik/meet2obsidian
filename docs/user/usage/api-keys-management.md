# API Keys Management

## Overview

Meet2Obsidian uses external services for speech-to-text transcription and text analysis. To use these services, you need to configure the appropriate API keys. This guide explains how to obtain, configure, and manage the API keys required for meet2obsidian.

## Required API Keys

Meet2Obsidian requires the following API keys:

1. **Rev.ai API Key**: Used for converting speech to text from meeting audio recordings.
2. **Claude API Key**: Used for analyzing transcripts and creating structured notes.

## Obtaining API Keys

### Rev.ai API Key

1. Go to the [Rev.ai](https://www.rev.ai/) website and create an account.
2. Navigate to your account settings or developer dashboard.
3. Create a new API key.
4. Copy the API key for configuration in meet2obsidian.

### Claude API Key

1. Go to [Anthropic's Claude](https://console.anthropic.com/) website and create an account.
2. Navigate to the API section in your account dashboard.
3. Create a new API key.
4. Copy the API key for configuration in meet2obsidian.

## Setting Up API Keys

Meet2Obsidian provides several ways to configure API keys:

### Using the CLI Setup Command

The easiest way to set up all required API keys at once:

```bash
meet2obsidian apikeys setup
```

This command will prompt you to enter both API keys securely (input will be hidden).

### Setting Individual API Keys

You can set each API key individually using the following commands:

```bash
# Set Rev.ai API key
meet2obsidian apikeys set rev_ai

# Set Claude API key
meet2obsidian apikeys set claude
```

You will be prompted to enter the API key value securely.

### Using the Setup Script

Alternatively, you can use the included setup script with expanded functionality:

```bash
# View help and available commands
./scripts/setup_api_keys.py --help

# Interactive setup (guided process)
./scripts/setup_api_keys.py interactive

# Set a specific API key
./scripts/setup_api_keys.py set rev_ai
./scripts/setup_api_keys.py set claude --value "your_api_key"

# Set and test an API key
./scripts/setup_api_keys.py set rev_ai --test
```

The setup script provides additional features not available through the CLI:
- API key validation before storing
- Interactive guided setup
- Detailed error messages
- Rich formatted output

## Checking API Keys

You can verify if your API keys are configured and valid:

### Checking Configuration Status

```bash
# Show a list of all required API keys and their setup status
meet2obsidian apikeys list

# Using the setup script
./scripts/setup_api_keys.py list
```

Example output:
```
API Keys Status:
------------------------
rev_ai      : Set      : abcd***
claude      : Not Set
```

### Testing API Keys

To verify that your API keys are not only configured but also valid:

```bash
# Test specific API key
./scripts/setup_api_keys.py test rev_ai

# Test provided API key value
./scripts/setup_api_keys.py test claude --value "your_api_key"
```

This will check each configured API key by making a simple test API call.

## Managing API Keys

### Viewing API Keys

You can check a specific API key:

```bash
# View masked API key (default)
meet2obsidian apikeys get rev_ai

# Using the setup script
./scripts/setup_api_keys.py get rev_ai
```

### Deleting API Keys

If you need to remove an API key:

```bash
meet2obsidian apikeys delete rev_ai

# Using the setup script
./scripts/setup_api_keys.py delete rev_ai
```

You will be prompted to confirm this action.

## Updating API Keys

If you need to update an API key (for example, when creating a new key), simply set it again:

```bash
meet2obsidian apikeys set rev_ai

# Or using the setup script
./scripts/setup_api_keys.py set rev_ai
```

The new value will replace the old one.

## API Key Security

Meet2Obsidian takes security seriously and implements the following measures to protect your API keys:

1. **Secure Storage**: API keys are stored in your operating system's secure credential store (macOS Keychain).
2. **Encryption**: Keys are encrypted at rest using the OS security mechanisms.
3. **Minimal Disclosure**: Full API key values are never logged or displayed unless explicitly requested.
4. **Local Only**: Your API keys never leave your computer except for direct API calls to the respective services.

## Troubleshooting

### API Key Not Found

If you receive an error indicating that an API key is not found:

1. Check if the key is configured using `meet2obsidian apikeys list`
2. If not configured, set up the key using `meet2obsidian apikeys set KEY_NAME`

### Invalid API Key

If you receive an error indicating that an API key is invalid:

1. Check the correctness of the API key by verifying in the respective service's dashboard
2. Update the API key if necessary using `meet2obsidian apikeys set KEY_NAME`
3. Test the API key using `./scripts/setup_api_keys.py test KEY_NAME`

### Keychain Access Issues

If you have problems accessing the keychain:

1. Ensure you have the appropriate access to the keychain
2. The system may request your password when accessing the keychain
3. Make sure your keychain is unlocked

## Best Practices

1. **Rotate Keys Regularly**: Periodically create new API keys and update them in meet2obsidian.
2. **Use Dedicated Keys**: When possible, create API keys specifically for meet2obsidian rather than sharing keys with other applications.
3. **Monitor Usage**: Regularly check your API usage on the respective service dashboards to ensure there's no unauthorized use.
4. **Set Appropriate Limits**: Where possible, configure usage limits on the API provider side to prevent unexpected costs.

## API Quotas and Pricing

Remember that Rev.ai and Claude API services have their own pricing models and usage quotas:

- **Rev.ai**: Typically charges per minute of transcribed audio.
- **Claude API**: Typically charges per token of input and output.

Be sure to check the current pricing models on the respective websites and monitor your usage to avoid unexpected costs.

## Frequently Asked Questions

**Q: Can I use meet2obsidian without API keys?**

A: No, the Rev.ai and Claude API keys are necessary for the core functionalities of meet2obsidian to work. Without them, the application will not be able to perform transcription or content analysis.

**Q: Can I use alternative services instead of Rev.ai or Claude?**

A: Currently, meet2obsidian only supports the Rev.ai and Claude APIs. Support for alternative services may be added in future versions.

**Q: How long are my API keys valid?**

A: API key validity depends on each API provider's policy. Some keys have no expiration, while others may require renewal after certain periods. Check your API provider's policy for specific information.

**Q: What should I do if I suspect my API key has been compromised?**

A: Immediately revoke the key on the API provider's website and create a new one. Then update the new key in meet2obsidian using the appropriate `apikeys set` command.