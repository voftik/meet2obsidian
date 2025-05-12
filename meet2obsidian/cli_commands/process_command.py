# meet2obsidian/cli_commands/process_command.py

import os
import click
import time
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.text import Text
from typing import Dict, List, Any, Optional

from meet2obsidian.utils.logging import get_logger
from meet2obsidian.core import ApplicationManager
from meet2obsidian.processing import ProcessingStatus

@click.group(name="process")
def process():
    """Manage the processing queue."""
    pass

@process.command()
@click.option('--detailed', '-d', is_flag=True, help='Show detailed information about files in queue.')
@click.option('--format', '-f', 'format_type', type=click.Choice(['text', 'json', 'table']), 
             default='table', help='Output format.')
@click.pass_context
def status(ctx, detailed, format_type):
    """Show status of the processing queue."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.process"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Check if application is running
    if not app_manager.is_running():
        console.print("[warning]⚠️ Application is not running. Start it with 'meet2obsidian service start' to process files.[/warning]")
        return
    
    # Get queue status
    queue_status = app_manager.get_processing_queue_status()
    
    # Check if there was an error getting the status
    if "error" in queue_status:
        console.print(f"[error]✗ Error getting queue status: {queue_status['error']}[/error]")
        return
    
    # Output information according to requested format
    if format_type == 'json':
        import json
        console.print(json.dumps(queue_status, indent=2))
    elif format_type == 'text':
        _print_queue_status_text(console, queue_status, detailed)
    else:  # table
        _print_queue_status_table(console, queue_status, detailed)
    
    logger.info("Processing queue status requested")

@process.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--priority', '-p', type=int, default=0, help='Processing priority (higher number = higher priority).')
@click.pass_context
def add(ctx, file_path, priority):
    """Add a file to the processing queue."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.process"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Check if application is running
    if not app_manager.is_running():
        console.print("[warning]⚠️ Application is not running. Start it with 'meet2obsidian service start' to process files.[/warning]")
        return
    
    try:
        # Convert to absolute path if needed
        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)
        
        # Get access to ProcessingQueue through ApplicationManager
        # For this example, we have to use an indirect method
        # First, get the processing queue status to ensure it's initialized
        queue_status = app_manager.get_processing_queue_status()
        if "error" in queue_status:
            console.print(f"[error]✗ Error accessing processing queue: {queue_status['error']}[/error]")
            return
        
        # Now we can access the processing queue through the application manager
        # and add the file to the queue
        # Note: In a more direct implementation, ApplicationManager would have an add_file_to_queue method
        
        # Add the file to the queue with metadata
        metadata = {
            "added_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "added_by": "cli",
            "priority": priority
        }
        
        # Use a monitor callback to add a file, this simulates finding a new file
        app_manager._handle_new_file(file_path)
        
        console.print(f"[success]✓ Added file to processing queue: {os.path.basename(file_path)}[/success]")
        logger.info(f"Added file to processing queue via CLI: {file_path}")
        
    except Exception as e:
        console.print(f"[error]✗ Error adding file to queue: {str(e)}[/error]")
        logger.error(f"Error adding file to queue: {str(e)}")

@process.command()
@click.pass_context
def retry(ctx):
    """Retry failed files in the processing queue."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.process"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Check if application is running
    if not app_manager.is_running():
        console.print("[warning]⚠️ Application is not running. Start it with 'meet2obsidian service start' to process files.[/warning]")
        return
    
    try:
        # Retry all failed files
        count = app_manager.retry_failed_files()
        
        if count > 0:
            console.print(f"[success]✓ Reset {count} files for retry.[/success]")
        else:
            console.print("[info]No files to retry.[/info]")
        
        logger.info(f"Reset {count} files for retry via CLI")
        
    except Exception as e:
        console.print(f"[error]✗ Error retrying files: {str(e)}[/error]")
        logger.error(f"Error retrying files: {str(e)}")

@process.command()
@click.pass_context
def clear(ctx):
    """Clear completed files from the processing queue."""
    console = ctx.obj.get('console', Console())
    logger = ctx.obj.get('logger', get_logger("cli.process"))
    
    # Create application manager
    app_manager = ApplicationManager()
    
    # Check if application is running
    if not app_manager.is_running():
        console.print("[warning]⚠️ Application is not running. Start it with 'meet2obsidian service start' to process files.[/warning]")
        return
    
    try:
        # Clear all completed files
        count = app_manager.clear_completed_files()
        
        if count > 0:
            console.print(f"[success]✓ Cleared {count} completed files from the queue.[/success]")
        else:
            console.print("[info]No completed files to clear.[/info]")
        
        logger.info(f"Cleared {count} completed files via CLI")
        
    except Exception as e:
        console.print(f"[error]✗ Error clearing completed files: {str(e)}[/error]")
        logger.error(f"Error clearing completed files: {str(e)}")

def _print_queue_status_table(console, status, detailed):
    """Format queue status as a table."""
    # Main stats table
    main_table = Table(title="Processing Queue Status", show_header=True, header_style="bold cyan")
    main_table.add_column("Status", style="dim")
    main_table.add_column("Count", justify="right")
    main_table.add_column("Percentage", justify="right")
    
    # Calculate total for percentages
    total = status.get("total", 0)
    
    # Add rows for each status
    if total > 0:
        main_table.add_row(
            "Pending", 
            str(status.get("pending", 0)),
            f"{status.get('pending', 0) / total * 100:.1f}%"
        )
        main_table.add_row(
            "Processing", 
            str(status.get("processing", 0)),
            f"{status.get('processing', 0) / total * 100:.1f}%"
        )
        main_table.add_row(
            "Completed", 
            str(status.get("completed", 0)),
            f"{status.get('completed', 0) / total * 100:.1f}%"
        )
        main_table.add_row(
            "Error", 
            str(status.get("error", 0)),
            f"{status.get('error', 0) / total * 100:.1f}%"
        )
        main_table.add_row(
            "Failed", 
            str(status.get("failed", 0)),
            f"{status.get('failed', 0) / total * 100:.1f}%"
        )
        main_table.add_row(
            "Total", 
            str(total),
            "100.0%", 
            style="bold"
        )
    else:
        main_table.add_row("No files in queue", "", "")
    
    console.print(main_table)
    
    # If detailed is requested, show file lists
    if detailed:
        _print_detailed_file_tables(console, status)

def _print_detailed_file_tables(console, status):
    """Print detailed tables of files in each status."""
    # Pending files
    if status.get("pending_files") and len(status["pending_files"]) > 0:
        _print_file_list_table(console, "Pending Files", status["pending_files"], "yellow")
    
    # Processing files
    if status.get("processing_files") and len(status["processing_files"]) > 0:
        _print_file_list_table(console, "Processing Files", status["processing_files"], "cyan")
    
    # Error files
    if status.get("error_files") and len(status["error_files"]) > 0:
        _print_file_list_table(console, "Error Files", status["error_files"], "red")
    
    # Failed files
    if status.get("failed_files") and len(status["failed_files"]) > 0:
        _print_file_list_table(console, "Failed Files", status["failed_files"], "red")
    
    # Completed files
    if status.get("completed_files") and len(status["completed_files"]) > 0:
        _print_file_list_table(console, "Completed Files", status["completed_files"], "green")

def _print_file_list_table(console, title, files, color):
    """Print a table of files."""
    files_table = Table(title=title, show_header=True, header_style=f"bold {color}")
    files_table.add_column("File", style="dim")
    
    for file_path in files:
        files_table.add_row(os.path.basename(file_path))
    
    console.print(files_table)

def _print_queue_status_text(console, status, detailed):
    """Format queue status as text."""
    total = status.get("total", 0)
    
    console.print("[bold]Processing Queue Status:[/bold]")
    
    if total > 0:
        console.print(f"Pending: {status.get('pending', 0)}")
        console.print(f"Processing: {status.get('processing', 0)}")
        console.print(f"Completed: {status.get('completed', 0)}")
        console.print(f"Error: {status.get('error', 0)}")
        console.print(f"Failed: {status.get('failed', 0)}")
        console.print(f"Total: {total}")
    else:
        console.print("No files in queue")
    
    # If detailed is requested, show file lists
    if detailed:
        if status.get("pending_files") and len(status["pending_files"]) > 0:
            console.print("\n[bold yellow]Pending Files:[/bold yellow]")
            for file_path in status["pending_files"]:
                console.print(f"  {os.path.basename(file_path)}")
        
        if status.get("processing_files") and len(status["processing_files"]) > 0:
            console.print("\n[bold cyan]Processing Files:[/bold cyan]")
            for file_path in status["processing_files"]:
                console.print(f"  {os.path.basename(file_path)}")
        
        if status.get("error_files") and len(status["error_files"]) > 0:
            console.print("\n[bold red]Error Files:[/bold red]")
            for file_path in status["error_files"]:
                console.print(f"  {os.path.basename(file_path)}")
        
        if status.get("failed_files") and len(status["failed_files"]) > 0:
            console.print("\n[bold red]Failed Files:[/bold red]")
            for file_path in status["failed_files"]:
                console.print(f"  {os.path.basename(file_path)}")
        
        if status.get("completed_files") and len(status["completed_files"]) > 0:
            console.print("\n[bold green]Completed Files:[/bold green]")
            for file_path in status["completed_files"]:
                console.print(f"  {os.path.basename(file_path)}")

def register_commands(cli):
    """Register process command in CLI."""
    cli.add_command(process)