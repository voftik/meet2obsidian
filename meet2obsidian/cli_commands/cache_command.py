"""
CLI commands for cache management.

This module provides commands for managing the meet2obsidian caching system,
including viewing cache information, cleaning up outdated cache, and
invalidating specific cache entries.
"""

import os
import click
import humanize
from typing import Dict, Any

from meet2obsidian.cache import CacheManager
from meet2obsidian.utils.logging import get_logger


@click.group(name="cache", help="Cache management commands")
def cache_command():
    """Group of commands for cache management."""
    pass

def register_commands(cli):
    """Register cache commands with the CLI."""
    cli.add_command(cache_command)


@cache_command.command(name="info", help="Show cache information")
@click.option("--detail", is_flag=True, help="Show detailed information")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def cache_info(detail, json_output):
    """Show information about the cache."""
    logger = get_logger("cache_info")
    cache_manager = CacheManager("~/.cache/meet2obsidian", logger=logger)
    
    if json_output:
        # For JSON output, include all details regardless of --detail flag
        import json
        info = cache_manager.get_cache_size()
        click.echo(json.dumps(info, indent=2))
        return
    
    if detail:
        # Get detailed information about the cache
        sizes = cache_manager.get_cache_size()
        
        # Format output
        click.echo(f"Cache Directory: {cache_manager.cache_dir}")
        click.echo(f"Retention Period: {cache_manager.retention_days} days")
        click.echo(f"Total Size: {humanize.naturalsize(sizes['total'])}")
        
        # Show breakdown by cache type
        click.echo("\nCache Types:")
        for cache_type, size in sorted(sizes.items()):
            if cache_type != "total" and size > 0:
                # Count files in this cache type
                type_dir = os.path.join(cache_manager.cache_dir, cache_type)
                if os.path.exists(type_dir):
                    file_count = len([f for f in os.listdir(type_dir) if os.path.isfile(os.path.join(type_dir, f))])
                    click.echo(f"  {cache_type}: {file_count} files, {humanize.naturalsize(size)}")
    else:
        # Simple size information
        sizes = cache_manager.get_cache_size()
        click.echo(f"Cache Size: {humanize.naturalsize(sizes['total'])}")


@cache_command.command(name="cleanup", help="Clean up outdated cache files")
@click.option("--retention", type=int, help="Override retention days")
@click.option("--type", "cache_type", help="Clean only specific cache type")
@click.option("--force", is_flag=True, help="Force cleanup all files")
def cache_cleanup(retention, cache_type, force):
    """Clean up outdated cache files."""
    logger = get_logger("cache_cleanup")
    cache_manager = CacheManager("~/.cache/meet2obsidian", logger=logger)
    
    if force:
        count = cache_manager.invalidate_all()
        click.echo(f"Forced cleanup: {count} files removed")
        return
    
    if cache_type:
        if retention:
            # Not directly implemented, so we use custom cleanup with custom retention
            count = cache_manager.cleanup_type(cache_type)
            click.echo(f"Cleaned up cache type '{cache_type}': {count} files removed")
        else:
            count = cache_manager.cleanup_type(cache_type)
            click.echo(f"Cleaned up cache type '{cache_type}': {count} files removed")
    else:
        if retention:
            count = cache_manager.cleanup_with_retention(retention)
            click.echo(f"Cleaned up cache with {retention} day retention: {count} files removed")
        else:
            count = cache_manager.cleanup()
            click.echo(f"Cleaned up cache with {cache_manager.retention_days} day retention: {count} files removed")


@cache_command.command(name="invalidate", help="Invalidate specific cache entries")
@click.option("--type", "cache_type", required=True, help="Cache type to invalidate")
@click.option("--key", help="Specific key to invalidate (optional)")
def cache_invalidate(cache_type, key):
    """Invalidate specific cache entries."""
    logger = get_logger("cache_invalidate")
    cache_manager = CacheManager("~/.cache/meet2obsidian", logger=logger)
    
    count = cache_manager.invalidate(cache_type, key)
    if key:
        click.echo(f"Invalidated {cache_type}/{key}: {count} files removed")
    else:
        click.echo(f"Invalidated all {cache_type} entries: {count} files removed")


@cache_command.command(name="clear", help="Clear all cache")
@click.confirmation_option(prompt="Are you sure you want to clear all cache?")
def cache_clear():
    """Clear the entire cache."""
    logger = get_logger("cache_clear")
    cache_manager = CacheManager("~/.cache/meet2obsidian", logger=logger)
    
    count = cache_manager.invalidate_all()
    click.echo(f"Cache cleared: {count} files removed")