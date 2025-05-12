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
@click.option('--keep-alive/--no-keep-alive', default=True,
              help='Whether to keep the service alive if it crashes.')
@click.option('--run-at-load/--no-run-at-load', default=True,
              help='Whether to run the service when the LaunchAgent is loaded.')
@click.option('--status', is_flag=True, help='Just show current autostart status.')
@click.pass_context
def autostart(ctx, enable, keep_alive, run_at_load, status):
    """Configure service autostart at login."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.service"))

    # Create application manager
    app_manager = ApplicationManager()

    # If status flag is set, show status and exit
    if status:
        is_active, info = app_manager.check_autostart_status()

        # Create a nice table to display the status
        status_table = Table(title="Autostart Status", show_header=True, header_style="bold cyan")
        status_table.add_column("Parameter", style="dim")
        status_table.add_column("Value")

        # Basic status - whether autostart is enabled and running
        if info and "installed" in info:
            status_installed = "[green]✓[/green]" if info["installed"] else "[red]✗[/red]"
            status_table.add_row("Installed", status_installed)

        status_running = "[green]✓[/green]" if is_active else "[red]✗[/red]"
        status_table.add_row("Running", status_running)

        # If we have detailed information, show it
        if info:
            # Plist file path
            if "plist_path" in info:
                status_table.add_row("Plist Path", info["plist_path"])

            # LaunchAgent configuration
            if "run_at_load" in info:
                value = "[green]✓[/green]" if info["run_at_load"] else "[red]✗[/red]"
                status_table.add_row("Run at Load", value)

            if "keep_alive" in info:
                value = "[green]✓[/green]" if info["keep_alive"] else "[red]✗[/red]"
                status_table.add_row("Keep Alive", value)

            # Process information
            if "pid" in info and info["pid"]:
                status_table.add_row("Process ID", str(info["pid"]))

            # Last modified
            if "last_modified" in info:
                from datetime import datetime
                modified_time = datetime.fromtimestamp(info["last_modified"])
                status_table.add_row("Last Modified", modified_time.strftime("%Y-%m-%d %H:%M:%S"))

        console.print(status_table)
        return

    # Configure autostart
    with console.status("[bold cyan]Configuring autostart...[/bold cyan]", spinner="dots"):
        success = app_manager.setup_autostart(enable, keep_alive, run_at_load)

    if success:
        action = "enabled" if enable else "disabled"
        console.print(f"[success]✓ Autostart {action} successfully[/success]")
        if enable:
            console.print(f"[info]Keep Alive: {'Yes' if keep_alive else 'No'}[/info]")
            console.print(f"[info]Run at Load: {'Yes' if run_at_load else 'No'}[/info]")
        logger.info(f"Autostart {action} with Keep alive: {keep_alive}, Run at load: {run_at_load}")
    else:
        console.print("[error]✗ Error configuring autostart[/error]")
        logger.error("Error configuring autostart")

def register_commands(cli):
    """Register service commands in the CLI."""
    cli.add_command(service)