# meet2obsidian/cli_commands/service_command.py

import click
import time
import subprocess
from pathlib import Path
from rich.console import Console
from rich.spinner import Spinner
from meet2obsidian.utils.logging import get_logger
from meet2obsidian.core import ApplicationManager

@click.group(name="service")
@click.pass_context
def service(ctx):
    """Manage the meet2obsidian service."""
    pass

@service.command()
@click.option('--autostart/--no-autostart', default=None, help='Configure autostart at login.')
@click.pass_context
def start(ctx, autostart):
    """Start the meet2obsidian service."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Check if service is already running
    if app_manager.is_running():
        console.print("[warning]Service is already running[/warning]")
        return
    
    # Start animation
    with console.status("[bold cyan]Starting service...[/bold cyan]", spinner="dots") as status:
        success = app_manager.start()
        # Give it some time to start
        time.sleep(1.5)
    
    if success:
        console.print("[success]✓ Service started successfully[/success]")
        logger.info("Service started successfully")
    else:
        console.print("[error]✗ Error starting service[/error]")
        logger.error("Error starting service")
        return
    
    # Configure autostart if option is provided
    if autostart is not None:
        with console.status("[bold cyan]Configuring autostart...[/bold cyan]", spinner="dots"):
            autostart_success = app_manager.setup_autostart(autostart)
        
        if autostart_success:
            action = "enabled" if autostart else "disabled"
            console.print(f"[success]✓ Autostart {action}[/success]")
            logger.info(f"Autostart {action}")
        else:
            console.print("[error]✗ Error configuring autostart[/error]")
            logger.error("Error configuring autostart")

@service.command()
@click.option('--force', is_flag=True, help='Force stop the service.')
@click.pass_context
def stop(ctx, force):
    """Stop the meet2obsidian service."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Check if service is running
    if not app_manager.is_running():
        console.print("[warning]Service is not running[/warning]")
        return
    
    # Stop animation
    with console.status("[bold cyan]Stopping service...[/bold cyan]", spinner="dots") as status:
        success = app_manager.stop(force=force)
        # Give it some time to stop
        time.sleep(1.5)
    
    if success:
        console.print("[success]✓ Service stopped successfully[/success]")
        logger.info("Service stopped successfully")
    else:
        console.print("[error]✗ Error stopping service[/error]")
        logger.error("Error stopping service")

@service.command()
@click.option('--force', is_flag=True, help='Force restart the service.')
@click.pass_context
def restart(ctx, force):
    """Restart the meet2obsidian service."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Restart animation
    with console.status("[bold cyan]Restarting service...[/bold cyan]", spinner="dots") as status:
        success = app_manager.restart(force=force)
        # Give it some time to restart
        time.sleep(2)
    
    if success:
        console.print("[success]✓ Service restarted successfully[/success]")
        logger.info("Service restarted successfully")
    else:
        console.print("[error]✗ Error restarting service[/error]")
        logger.error("Error restarting service")

@service.command()
@click.option('--enable/--disable', required=True, help='Enable or disable autostart.')
@click.pass_context
def autostart(ctx, enable):
    """Configure service autostart at login."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Configure autostart
    with console.status("[bold cyan]Configuring autostart...[/bold cyan]", spinner="dots"):
        success = app_manager.setup_autostart(enable)
    
    if success:
        action = "enabled" if enable else "disabled"
        console.print(f"[success]✓ Autostart {action} successfully[/success]")
        logger.info(f"Autostart {action}")
    else:
        console.print("[error]✗ Error configuring autostart[/error]")
        logger.error("Error configuring autostart")

def register_commands(cli):
    """Register service commands in the CLI."""
    cli.add_command(service)