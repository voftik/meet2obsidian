#!/bin/bash

# Скрипт для настройки автозапуска meet2obsidian через LaunchAgent в macOS

# Путь к Python интерпретатору
PYTHON_PATH=$(which python3)

# Путь к директории пользователя LaunchAgents
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.user.meet2obsidian.plist"

# Путь для логов
LOG_DIR="$HOME/Library/Logs/meet2obsidian"

# Создаем директории если не существуют
mkdir -p "$LAUNCH_AGENTS_DIR"
mkdir -p "$LOG_DIR"

# Создаем plist файл с точными путями для логов
cat > "$PLIST_FILE" << EOL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.meet2obsidian</string>
    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_PATH}</string>
        <string>-m</string>
        <string>meet2obsidian</string>
        <string>service</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/stderr.log</string>
</dict>
</plist>
EOL

# Устанавливаем правильные разрешения
chmod 644 "$PLIST_FILE"

# Загружаем LaunchAgent
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo "LaunchAgent успешно настроен и загружен:"
echo "$PLIST_FILE"

echo "Сервис будет автоматически запускаться при входе в систему."
echo "Логи сервиса будут доступны в директории: $LOG_DIR"