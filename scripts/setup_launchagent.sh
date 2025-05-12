#!/bin/bash

# Script for setting up meet2obsidian autostart through LaunchAgent on macOS
# This script provides a manual alternative to using the CLI command:
# meet2obsidian service autostart --enable

# Default configuration
LABEL="com.user.meet2obsidian"
WORKING_DIRECTORY=""
KEEP_ALIVE=true
RUN_AT_LOAD=true

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --no-keep-alive)
            KEEP_ALIVE=false
            shift
            ;;
        --no-run-at-load)
            RUN_AT_LOAD=false
            shift
            ;;
        --working-dir)
            WORKING_DIRECTORY="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --no-keep-alive      Disable automatic restart if service crashes"
            echo "  --no-run-at-load     Don't run the service when LaunchAgent loads"
            echo "  --working-dir DIR    Set working directory for the service"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help to see available options"
            exit 1
            ;;
    esac
done

# Path to Python interpreter
PYTHON_PATH=$(which python3)

# Path to user's LaunchAgents directory
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/$LABEL.plist"

# Path for logs
LOG_DIR="$HOME/Library/Logs/meet2obsidian"

# Create directories if they don't exist
mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$LOG_DIR"

# Create plist file with exact paths for logs
cat > "$PLIST_FILE" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>-m</string>
        <string>meet2obsidian</string>
        <string>service</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <${RUN_AT_LOAD}/>
    <key>KeepAlive</key>
    <${KEEP_ALIVE}/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/stderr.log</string>
EOL

# Add working directory if specified
if [ -n "$WORKING_DIRECTORY" ]; then
    cat >> "$PLIST_FILE" << EOL
    <key>WorkingDirectory</key>
    <string>${WORKING_DIRECTORY}</string>
EOL
fi

# Close the plist file
cat >> "$PLIST_FILE" << EOL
</dict>
</plist>
EOL

# Set correct permissions
chmod 644 "$PLIST_FILE"

# Load the LaunchAgent
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo "LaunchAgent successfully configured and loaded:"
echo "$PLIST_FILE"

echo "The service will automatically start at login."
echo "Service logs will be available in directory: $LOG_DIR"