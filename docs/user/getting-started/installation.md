Installing meet2obsidian
Prerequisites

macOS 11 (Big Sur) or higher
Python 3.9 or higher
FFmpeg (for audio processing)
Obsidian (installed and configured)

Installation via Homebrew
The recommended way to install meet2obsidian is through Homebrew:
bashbrew install meet2obsidian
Installation from Source
Alternatively, you can install meet2obsidian from source:
bashgit clone https://github.com/voftik/meet2obsidian.git
cd meet2obsidian
pip install -e .
Verifying the Installation
After installation, verify that meet2obsidian was installed successfully:
bashmeet2obsidian --version
Next Steps
After successful installation, check out the configuration guide to set up the application.

# Setting Up API Keys

## Prerequisites

Meet2Obsidian requires API keys from two services to function properly:

1. **Rev.ai** - For transcribing audio from meeting recordings
2. **Claude** (Anthropic) - For analyzing transcriptions and generating structured notes

You'll need to obtain these API keys before using the application.

## Obtaining API Keys

### Rev.ai API Key

1. Sign up at [Rev.ai](https://www.rev.ai/)
2. Choose a subscription plan based on your transcription needs
3. Navigate to your account settings or developer dashboard
4. Generate a new API key
5. Copy the API key for use with Meet2Obsidian

### Claude API Key

1. Sign up at [Anthropic](https://console.anthropic.com/)
2. Navigate to the API section in your account
3. Create a new API key
4. Set appropriate usage limits if desired
5. Copy the API key for use with Meet2Obsidian

## Setting Up API Keys in Meet2Obsidian

Meet2Obsidian securely stores your API keys in macOS Keychain, so you never need to include them in configuration files.

### Using the Setup Tool

1. Open Terminal
2. Navigate to your Meet2Obsidian installation directory
3. Run the setup script with your API keys:

```bash
# Activate the virtual environment (if using one)
source venv/bin/activate

# Set both API keys
python scripts/setup_api_keys.py --revai YOUR_REVAI_API_KEY --claude YOUR_CLAUDE_API_KEY
```

Replace `YOUR_REVAI_API_KEY` and `YOUR_CLAUDE_API_KEY` with your actual API keys.

### Setting Keys Individually

If you want to set only one of the keys:

```bash
# Set only Rev.ai key
python scripts/setup_api_keys.py --revai YOUR_REVAI_API_KEY

# Set only Claude key
python scripts/setup_api_keys.py --claude YOUR_CLAUDE_API_KEY
```

### Testing Your API Keys

To verify that your API keys are correctly stored and working:

```bash
python scripts/setup_api_keys.py --test
```

This command will check if the keys are available in Keychain and validate them against the respective services.

## Managing API Keys

### Updating Keys

To update an API key, simply run the setup script again with the new key:

```bash
python scripts/setup_api_keys.py --revai NEW_REVAI_API_KEY
```

### Security Information

- Your API keys are stored securely in macOS Keychain
- Keys are never stored in plain text configuration files
- Keys are accessible only to your user account
- The application accesses keys automatically without requiring password input

## Troubleshooting

### "API key not found" Error

If you see this error when running Meet2Obsidian:

1. Ensure you've correctly set up the API keys using the setup script
2. Run the test command to verify key accessibility:
   ```bash
   python scripts/setup_api_keys.py --test
   ```
3. If the test fails, try setting the keys again

### Authentication Failures

If Meet2Obsidian can't authenticate with the services:

1. Check if your API keys are still valid by testing them
2. Ensure you haven't exceeded API usage limits or quotas
3. Check if the services are operational
4. Try regenerating your API keys and updating them in Meet2Obsidian

### Permission Issues

If you see Keychain permission dialogs:

1. Always allow Meet2Obsidian to access the Keychain items
2. If you denied access initially, you may need to reset permissions in Keychain Access application

## Best Practices

- Periodically rotate your API keys for better security
- Monitor your API usage to avoid unexpected charges
- Keep your Meet2Obsidian application updated to ensure compatibility with API changes
