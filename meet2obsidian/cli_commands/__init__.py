"""
Пакет CLI команд для приложения meet2obsidian.

Этот пакет содержит модули, определяющие различные команды командной строки
для взаимодействия с приложением meet2obsidian.
"""

# Импорт всех модулей команд для регистрации
from . import logs_command
from . import apikeys_command
from . import service_command
from . import status_command
from . import config_command
from . import completion