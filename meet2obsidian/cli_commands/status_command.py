# meet2obsidian/cli_commands/status_command.py

import click
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from meet2obsidian.utils.logging import get_logger
from meet2obsidian.core import ApplicationManager
from meet2obsidian.utils.security import KeychainManager

@click.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed status information.')
@click.option('--format', '-f', 'format_type', type=click.Choice(['text', 'json', 'table']), 
             default='table', help='Output format.')
@click.pass_context
def status(ctx, detailed, format_type):
    """Show current status of the meet2obsidian service."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.status"))
    
    # Create application manager
    app_manager = ApplicationManager()
    keychain_manager = KeychainManager()
    
    # Check if service is running
    is_running = app_manager.is_running()
    
    # Basic status information
    status_data = {
        "running": is_running,
        "api_keys": keychain_manager.get_api_keys_status()
    }
    
    # If service is running, get additional information
    if is_running:
        status_data.update(app_manager.get_status())
    
    # Output information according to requested format
    if format_type == 'json':
        console.print(json.dumps(status_data, indent=2))
        return
    
    if format_type == 'text':
        _print_status_text(console, status_data, detailed)
    else:  # table
        _print_status_table(console, status_data, detailed)
    
    logger.info("Status information requested")

def _print_status_table(console, status_data, detailed):
    """Format status as a table."""
    # Main status table
    main_table = Table(title="Meet2Obsidian Status", show_header=True, header_style="bold cyan")
    main_table.add_column("Parameter", style="dim")
    main_table.add_column("Value")
    
    # Basic information
    status_text = "[bold green]Running[/bold green]" if status_data["running"] else "[bold red]Stopped[/bold red]"
    main_table.add_row("Status", status_text)
    
    if status_data["running"]:
        main_table.add_row("Uptime", status_data.get("uptime", "Unknown"))
        main_table.add_row("Processed files", str(status_data.get("processed_files", 0)))
        main_table.add_row("Pending files", str(status_data.get("pending_files", 0)))
    
    # API keys
    api_keys = status_data.get("api_keys", {})
    for key, exists in api_keys.items():
        key_status = "[green]✓[/green]" if exists else "[red]✗[/red]"
        main_table.add_row(f"API key {key}", key_status)
    
    console.print(main_table)
    
    # If detailed information is requested and service is running
    if detailed and status_data["running"]:
        _print_detailed_tables(console, status_data)

def _print_detailed_tables(console, status_data):
    """Print detailed status tables."""
    # Active jobs
    if "active_jobs" in status_data and status_data["active_jobs"]:
        jobs_table = Table(title="Active Jobs", show_header=True, header_style="bold cyan")
        jobs_table.add_column("File", style="dim")
        jobs_table.add_column("Stage")
        jobs_table.add_column("Progress")
        
        for job in status_data["active_jobs"]:
            jobs_table.add_row(
                job.get("info", {}).get("file", "Unknown"),
                job.get("info", {}).get("stage", "Unknown"),
                job.get("info", {}).get("progress", "0%")
            )
        
        console.print(jobs_table)
    
    # Recent errors
    if "last_errors" in status_data and status_data["last_errors"]:
        errors_table = Table(title="Recent Errors", show_header=True, header_style="bold red")
        errors_table.add_column("Time", style="dim")
        errors_table.add_column("Job ID")
        errors_table.add_column("Message")
        
        for error in status_data["last_errors"]:
            errors_table.add_row(
                error.get("time", "Unknown"),
                error.get("job_id", "Unknown"),
                error.get("message", "Unknown")
            )
        
        console.print(errors_table)
    
    # Components status
    if "components" in status_data:
        components_table = Table(title="Components Status", show_header=True, header_style="bold cyan")
        components_table.add_column("Component", style="dim")
        components_table.add_column("Status")
        
        for component, status in status_data["components"].items():
            status_text = "[green]Active[/green]" if status == "active" else "[yellow]Inactive[/yellow]"
            components_table.add_row(component, status_text)
        
        console.print(components_table)

def _print_status_text(console, status_data, detailed):
    """Format status as text."""
    status_text = "Running" if status_data["running"] else "Stopped"
    console.print(f"Status: [bold]{'[green]' if status_data['running'] else '[red]'}{status_text}[/]")
    
    if status_data["running"]:
        console.print(f"Uptime: {status_data.get('uptime', 'Unknown')}")
        console.print(f"Processed files: {status_data.get('processed_files', 0)}")
        console.print(f"Pending files: {status_data.get('pending_files', 0)}")
    
    # API keys
    console.print("\nAPI keys:")
    api_keys = status_data.get("api_keys", {})
    for key, exists in api_keys.items():
        status_mark = "[green]✓[/green]" if exists else "[red]✗[/red]"
        console.print(f"  {key}: {status_mark}")
    
    # Detailed information if requested
    if detailed and status_data["running"]:
        # Components status
        if "components" in status_data:
            console.print("\n[bold]Components:[/bold]")
            for component, status in status_data["components"].items():
                status_text = "[green]Active[/green]" if status == "active" else "[yellow]Inactive[/yellow]"
                console.print(f"  {component}: {status_text}")
        
        # Active jobs
        if "active_jobs" in status_data and status_data["active_jobs"]:
            console.print("\n[bold]Active jobs:[/bold]")
            for job in status_data["active_jobs"]:
                info = job.get("info", {})
                console.print(f"  File: {info.get('file', 'Unknown')}")
                console.print(f"    Stage: {info.get('stage', 'Unknown')}")
                console.print(f"    Progress: {info.get('progress', '0%')}")
        
        # Recent errors
        if "last_errors" in status_data and status_data["last_errors"]:
            console.print("\n[bold red]Recent errors:[/bold red]")
            for error in status_data["last_errors"]:
                console.print(f"  [{error.get('time', 'Unknown')}] {error.get('job_id', 'Unknown')}: {error.get('message', 'Unknown')}")

def register_commands(cli):
    """Register status command in CLI."""
    cli.add_command(status)