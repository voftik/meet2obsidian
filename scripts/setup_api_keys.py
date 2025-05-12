#!/usr/bin/env python3
"""
Script for setting up API keys for meet2obsidian.

This script provides a command-line interface for managing API keys used by meet2obsidian,
including setting, testing, listing, and deleting API keys for Rev.ai and Claude services.
"""

import os
import sys
import json
import argparse
import getpass
import logging
from typing import Optional, Dict, Any, List, Tuple

# Try to import requests, which may not be installed
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Add parent directory to path to import from meet2obsidian
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, parent_dir)

# Try to import necessary modules with graceful degradation
HAS_KEYCHAIN = True
HAS_LOGGING = True
HAS_RICH = False

try:
    try:
        from meet2obsidian.utils.security import KeychainManager
    except ImportError as e:
        print(f"Warning: Cannot import KeychainManager: {e}")
        print("Falling back to local implementation...")
        HAS_KEYCHAIN = False

    try:
        from meet2obsidian.utils.logging import setup_logging, get_logger
    except ImportError:
        print("Warning: Cannot import logging utilities")
        HAS_LOGGING = False

    # Try to import Rich for better formatting if available
    try:
        from rich.console import Console
        from rich.table import Table
        from rich.prompt import Prompt
        HAS_RICH = True
    except ImportError:
        HAS_RICH = False
except Exception as e:
    print(f"Error setting up environment: {e}")
    HAS_KEYCHAIN = False
    HAS_LOGGING = False
    HAS_RICH = False

# Local implementation of KeychainManager if the main one is not available
if not HAS_KEYCHAIN:
    class KeychainManager:
        """Simple local implementation of KeychainManager for testing purposes."""

        def __init__(self, logger=None):
            self.logger = logger or logging.getLogger(__name__)
            self.keys = {}
            self._storage_file = os.path.expanduser("~/.meet2obsidian_temp_keys.json")
            self._load_from_file()

        def _load_from_file(self):
            """Load keys from a temporary JSON file."""
            if os.path.exists(self._storage_file):
                try:
                    with open(self._storage_file, 'r') as f:
                        self.keys = json.load(f)
                except Exception as e:
                    print(f"Warning: Failed to load keys from file: {e}")

        def _save_to_file(self):
            """Save keys to a temporary JSON file."""
            try:
                with open(self._storage_file, 'w') as f:
                    json.dump(self.keys, f)
            except Exception as e:
                print(f"Warning: Failed to save keys to file: {e}")

        def store_api_key(self, key_name, api_key):
            """Store an API key (in memory only)."""
            self.keys[key_name] = api_key
            self._save_to_file()
            return True

        def get_api_key(self, key_name):
            """Get an API key."""
            return self.keys.get(key_name)

        def delete_api_key(self, key_name):
            """Delete an API key."""
            if key_name in self.keys:
                del self.keys[key_name]
                self._save_to_file()
                return True
            return False

        def key_exists(self, key_name):
            """Check if a key exists."""
            return key_name in self.keys

        def get_api_keys_status(self):
            """Get the status of all API keys."""
            return {key: True for key in ["rev_ai", "claude"] if key in self.keys}

        def mask_api_key(self, api_key, visible_chars=4):
            """Mask an API key for display."""
            if not api_key:
                return ""

            if len(api_key) <= visible_chars:
                return api_key

            return api_key[:visible_chars] + "*" * (len(api_key) - visible_chars)

# Set up logging
if HAS_LOGGING:
    setup_logging(level="info")
    logger = get_logger("api_keys_setup")
else:
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger("api_keys_setup")

# Initialize KeychainManager
keychain = KeychainManager(logger=logger)

# Initialize Rich console if available
console = Console() if HAS_RICH else None


def setup_args() -> argparse.Namespace:
    """Set up command line arguments."""
    parser = argparse.ArgumentParser(description='Set up API keys for meet2obsidian')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Set API key command
    set_parser = subparsers.add_parser('set', help='Set an API key')
    set_parser.add_argument('key_name', choices=['rev_ai', 'claude'], 
                          help='Name of the API key to set')
    set_parser.add_argument('--value', help='API key value (if not provided, will prompt securely)')
    set_parser.add_argument('--test', action='store_true', 
                          help='Test the API key before storing')
    
    # Get API key command
    get_parser = subparsers.add_parser('get', help='Get an API key (masked)')
    get_parser.add_argument('key_name', help='Name of the API key to get')
    
    # List API keys command
    list_parser = subparsers.add_parser('list', help='List all API keys')
    
    # Delete API key command
    delete_parser = subparsers.add_parser('delete', help='Delete an API key')
    delete_parser.add_argument('key_name', help='Name of the API key to delete')
    
    # Test API key command
    test_parser = subparsers.add_parser('test', help='Test an API key')
    test_parser.add_argument('key_name', choices=['rev_ai', 'claude'], 
                           help='Name of the API key to test')
    test_parser.add_argument('--value', help='API key value to test (if not provided, will use stored key)')
    
    # Interactive setup
    subparsers.add_parser('interactive', help='Interactive setup of API keys')
    
    return parser.parse_args()


def prompt_api_key(key_name: str) -> str:
    """
    Prompt the user for an API key with secure input.
    
    Args:
        key_name: Name of the API key (for display purposes)
        
    Returns:
        str: The entered API key
    """
    prompt_message = f"Enter {key_name} API key: "
    
    if HAS_RICH:
        # Use Rich's secure prompt
        return Prompt.ask(prompt_message, password=True)
    else:
        # Fall back to getpass
        return getpass.getpass(prompt_message)


def test_rev_ai_key(api_key: str) -> Tuple[bool, str]:
    """
    Test the Rev.ai API key by making a simple API call.

    Args:
        api_key: Rev.ai API key to test

    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not HAS_REQUESTS:
        return False, "The 'requests' module is not installed. Install it with: pip install requests"

    try:
        # Make a simple call to get account details
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get("https://api.rev.ai/speechtotext/v1/account", headers=headers)

        if response.status_code == 200:
            account_info = response.json()
            return True, f"Success! Account email: {account_info.get('email')}"
        else:
            return False, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def test_claude_key(api_key: str) -> Tuple[bool, str]:
    """
    Test the Claude API key by making a simple API call.

    Args:
        api_key: Claude API key to test

    Returns:
        Tuple[bool, str]: (success, message)
    """
    if not HAS_REQUESTS:
        return False, "The 'requests' module is not installed. Install it with: pip install requests"

    try:
        # Make a simple call to list models (a lightweight API call)
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        response = requests.get("https://api.anthropic.com/v1/models", headers=headers)

        if response.status_code == 200:
            models_info = response.json()
            model_names = [model.get("name") for model in models_info.get("data", [])]
            model_str = ", ".join(model_names[:3]) + ("..." if len(model_names) > 3 else "")
            return True, f"Success! Available models: {model_str}"
        else:
            return False, f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def display_api_keys_status() -> None:
    """Display the status of all required API keys."""
    status = keychain.get_api_keys_status()
    
    if HAS_RICH:
        table = Table(title="API Keys Status")
        table.add_column("API Service", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Key Preview", style="yellow")
        
        for key_name, exists in status.items():
            status_text = "[green]Set[/green]" if exists else "[red]Not Set[/red]"
            preview = ""
            if exists:
                api_key = keychain.get_api_key(key_name)
                if api_key:
                    preview = keychain.mask_api_key(api_key)
                    
            table.add_row(key_name, status_text, preview)
            
        console.print(table)
    else:
        print("\nAPI Keys Status:")
        print("-" * 50)
        for key_name, exists in status.items():
            status_text = "Set" if exists else "Not Set"
            preview = ""
            if exists:
                api_key = keychain.get_api_key(key_name)
                if api_key:
                    preview = keychain.mask_api_key(api_key)
            print(f"{key_name:10} | {status_text:10} | {preview}")
        print("-" * 50)


def set_api_key(key_name: str, value: Optional[str] = None, test: bool = False) -> None:
    """
    Set an API key.
    
    Args:
        key_name: Name of the API key to set
        value: Value of the API key (if None, will prompt)
        test: Whether to test the key before storing
    """
    # Get the API key value if not provided
    api_key = value
    if api_key is None:
        api_key = prompt_api_key(key_name)
    
    if not api_key:
        print_error("API key cannot be empty")
        return
    
    # Test the API key if requested
    if test:
        print_info(f"Testing {key_name} API key...")
        
        success = False
        message = ""
        
        if key_name == "rev_ai":
            success, message = test_rev_ai_key(api_key)
        elif key_name == "claude":
            success, message = test_claude_key(api_key)
        
        if success:
            print_success(message)
        else:
            print_error(f"API key test failed: {message}")
            confirm = input("Store the key anyway? (y/n): ").lower()
            if confirm != 'y':
                print_info("Operation cancelled")
                return
    
    # Store the API key
    if keychain.store_api_key(key_name, api_key):
        print_success(f"API key for {key_name} stored successfully")
    else:
        print_error(f"Failed to store API key for {key_name}")


def test_api_key(key_name: str, value: Optional[str] = None) -> None:
    """
    Test an API key.
    
    Args:
        key_name: Name of the API key to test
        value: Value of the API key (if None, will use stored key)
    """
    # Get the API key value if not provided
    api_key = value
    if api_key is None:
        api_key = keychain.get_api_key(key_name)
        if not api_key:
            print_error(f"No API key found for {key_name}. Use 'set' command to set it first.")
            return
    
    print_info(f"Testing {key_name} API key...")
    
    success = False
    message = ""
    
    if key_name == "rev_ai":
        success, message = test_rev_ai_key(api_key)
    elif key_name == "claude":
        success, message = test_claude_key(api_key)
    
    if success:
        print_success(message)
    else:
        print_error(f"API key test failed: {message}")


def interactive_setup() -> None:
    """Run interactive setup for all required API keys."""
    print_info("Welcome to meet2obsidian API key setup!\n")
    print_info("This script will help you set up the required API keys for meet2obsidian.")
    print_info("You will need:")
    print_info("1. A Rev.ai API key for speech-to-text services")
    print_info("2. A Claude API key from Anthropic for AI analysis")
    print_info("\nYou can skip any key by pressing Enter when prompted.\n")
    
    # Set up Rev.ai API key
    print_info("Setting up Rev.ai API key:")
    print_info("Get your Rev.ai API key from: https://www.rev.ai/access_token")
    api_key = prompt_api_key("Rev.ai")
    
    if api_key:
        print_info("Testing Rev.ai API key...")
        success, message = test_rev_ai_key(api_key)
        
        if success:
            print_success(message)
            keychain.store_api_key("rev_ai", api_key)
            print_success("Rev.ai API key stored successfully")
        else:
            print_error(f"API key test failed: {message}")
            confirm = input("Store the key anyway? (y/n): ").lower()
            if confirm == 'y':
                keychain.store_api_key("rev_ai", api_key)
                print_success("Rev.ai API key stored successfully")
    else:
        print_info("Skipped Rev.ai API key setup")
    
    print("\n" + "-" * 50 + "\n")
    
    # Set up Claude API key
    print_info("Setting up Claude API key:")
    print_info("Get your Claude API key from: https://console.anthropic.com/")
    api_key = prompt_api_key("Claude")
    
    if api_key:
        print_info("Testing Claude API key...")
        success, message = test_claude_key(api_key)
        
        if success:
            print_success(message)
            keychain.store_api_key("claude", api_key)
            print_success("Claude API key stored successfully")
        else:
            print_error(f"API key test failed: {message}")
            confirm = input("Store the key anyway? (y/n): ").lower()
            if confirm == 'y':
                keychain.store_api_key("claude", api_key)
                print_success("Claude API key stored successfully")
    else:
        print_info("Skipped Claude API key setup")
    
    print("\n" + "-" * 50 + "\n")
    
    # Show final status
    print_info("API key setup complete!")
    display_api_keys_status()


# Formatted output functions
def print_success(message: str) -> None:
    """Print a success message."""
    if HAS_RICH:
        console.print(f"[green]✓ {message}[/green]")
    else:
        print(f"✓ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    if HAS_RICH:
        console.print(f"[red]✗ {message}[/red]")
    else:
        print(f"✗ {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    if HAS_RICH:
        console.print(f"[blue]ℹ {message}[/blue]")
    else:
        print(f"ℹ {message}")


def main():
    """Main function."""
    # Check if the required Python packages are installed
    if not HAS_REQUESTS and len(sys.argv) > 1 and sys.argv[1] in ['test', 'set', 'interactive']:
        print_error("The 'requests' package is required for API testing.")
        print_info("Please install it using: pip install requests")
        print_info("You can still use 'list', 'get', and 'delete' commands without requests.")
        if len(sys.argv) > 1 and sys.argv[1] in ['test', 'set']:
            return 1

    args = setup_args()

    # If no command provided, show help
    if not args.command:
        print_info("No command provided. Use one of the available commands:")
        print_info("  set, get, list, delete, test, interactive")
        print_info("Run with --help for more information.")
        return 1
    
    # Execute the requested command
    if args.command == 'set':
        set_api_key(args.key_name, args.value, args.test)
    
    elif args.command == 'get':
        api_key = keychain.get_api_key(args.key_name)
        if api_key:
            masked_key = keychain.mask_api_key(api_key)
            print_info(f"{args.key_name}: {masked_key}")
        else:
            print_error(f"No API key found for {args.key_name}")
    
    elif args.command == 'list':
        display_api_keys_status()
    
    elif args.command == 'delete':
        if keychain.delete_api_key(args.key_name):
            print_success(f"API key for {args.key_name} deleted")
        else:
            print_error(f"Failed to delete API key for {args.key_name}")
    
    elif args.command == 'test':
        test_api_key(args.key_name, args.value)
    
    elif args.command == 'interactive':
        interactive_setup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())