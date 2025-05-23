# meet2obsidian/cli_commands/completion.py

import click
import os
import sys
from rich.console import Console
from meet2obsidian.utils.logging import get_logger

try:
    import click_completion
    # Включаем поддержку автодополнения для всех поддерживаемых оболочек
    click_completion.init()
    COMPLETION_AVAILABLE = True
except ImportError:
    COMPLETION_AVAILABLE = False

@click.command()
@click.option('--shell', '-s', type=click.Choice(['bash', 'zsh', 'fish', 'powershell']), 
             help='Тип оболочки, для которой генерировать скрипт автодополнения.')
@click.option('--install', is_flag=True, help='Установить автодополнение в профиль оболочки.')
@click.pass_context
def completion(ctx, shell, install):
    """Управление автодополнением команд в оболочке."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.completion"))
    
    if not COMPLETION_AVAILABLE:
        console.print("[error]✗ click_completion library is not installed. Install it for autocompletion support:[/error]")
        console.print("  pip install click-completion")
        return 1
    
    # Если оболочка не указана, пытаемся определить ее автоматически
    if not shell:
        shell = click_completion.get_auto_shell()
    
    if not shell:
        console.print("[error]✗ Could not determine shell type. Specify it explicitly with the --shell option[/error]")
        return 1
    
    # Генерируем скрипт автодополнения
    completion_script = click_completion.get_code(shell, prog_name='meet2obsidian')
    
    if install:
        # Устанавливаем автодополнение в профиль оболочки
        shell_config_file = _get_shell_config_file(shell)
        
        if not shell_config_file:
            console.print(f"[error]✗ Could not determine configuration file for shell {shell}[/error]")
            return 1
        
        # Проверяем, что скрипт автодополнения еще не установлен
        try:
            with open(shell_config_file, 'r') as f:
                if completion_script in f.read():
                    console.print(f"[warning]Autocompletion already installed in {shell_config_file}[/warning]")
                    return
        except Exception:
            pass
        
        # Добавляем скрипт автодополнения в файл конфигурации
        try:
            with open(shell_config_file, 'a') as f:
                f.write(f"\n# meet2obsidian completion\n{completion_script}\n")
            
            console.print(f"[success]✓ Autocompletion successfully installed in [bold]{shell_config_file}[/bold][/success]")
            console.print(f"Restart your shell or run:")
            console.print(f"  source {shell_config_file}")
            logger.info(f"Autocompletion successfully installed in {shell_config_file}")
        except Exception as e:
            console.print(f"[error]✗ Error installing autocompletion: {str(e)}[/error]")
            logger.error(f"Error installing autocompletion: {str(e)}")
            return 1
    else:
        # Просто выводим скрипт автодополнения
        console.print(completion_script)

def _get_shell_config_file(shell):
    """Получение пути к файлу конфигурации для указанной оболочки."""
    home = os.path.expanduser("~")
    
    if shell == 'bash':
        # Проверяем наличие файлов в порядке приоритета
        for filename in ['.bashrc', '.bash_profile']:
            path = os.path.join(home, filename)
            if os.path.exists(path):
                return path
    elif shell == 'zsh':
        return os.path.join(home, '.zshrc')
    elif shell == 'fish':
        return os.path.join(home, '.config/fish/config.fish')
    
    # Для powershell и других оболочек возвращаем None
    return None

def register_commands(cli):
    """Регистрация команды автодополнения в CLI."""
    cli.add_command(completion)