"""
=B5@D59A :><0=4=>9 AB@>:8 4;O meet2obsidian.

-B>B <>4C;L >?@545;O5B >A=>2=>9 8=B5@D59A :><0=4=>9 AB@>:8 4;O ?@8;>65=8O
meet2obsidian 8 @538AB@8@C5B 2A5 4>ABC?=K5 :><0=4K.
"""

import os
import sys
import click

from meet2obsidian.utils.logging import setup_logging, get_logger
from meet2obsidian.cli_commands import logs_command


@click.group()
@click.version_option(version="0.1.0")
@click.option("--verbose", "-v", is_flag=True, help=":;NG8BL ?>4@>1=K9 2K2>4.")
@click.option("--log-file", help="CBL : D09;C ;>30.")
@click.pass_context
def cli(ctx, verbose, log_file):
    """Meet2Obsidian - 02B><0B878@>20==K9 8=AB@C<5=B 4;O ?>43>B>2:8 70<5B>: 87 70?8A59 2AB@5G."""
    # 0AB@>9:0 :>=B5:AB0 4;O 2A5E :><0=4
    ctx.ensure_object(dict)
    ctx.obj["VERBOSE"] = verbose
    
    # 0AB@>9:0 ;>38@>20=8O
    log_level = "debug" if verbose else "info"
    
    if not log_file:
        # ?@545;5=85 ?CB8 : ;>3C ?> C<>;G0=8N
        log_dir = os.path.expanduser("~/Library/Logs/meet2obsidian")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "meet2obsidian.log")
    
    # 0AB@>9:0 ;>38@>20=8O
    setup_logging(log_level=log_level, log_file=log_file)
    ctx.obj["LOGGER"] = get_logger("cli")
    
    if verbose:
        click.echo(f">4@>1=K9 @568< 2:;NG5=. >38 70?8AK20NBAO 2: {log_file}")


@cli.command()
@click.pass_context
def start(ctx):
    """0?CAB8BL >1@01>B:C 2845> 87 48@5:B>@88."""
    logger = ctx.obj["LOGGER"]
    logger.info("><0=40 start 2K?>;=5=0")
    click.echo("0?CA: <>=8B>@8=30 2845>D09;>2...")


@cli.command()
@click.pass_context
def status(ctx):
    """>:070BL AB0BCA >1@01>B:8 2845>."""
    logger = ctx.obj["LOGGER"]
    logger.info("><0=40 status 2K?>;=5=0")
    click.echo("!B0BCA >1@01>B:8: 0:B82=>")


@cli.command()
@click.pass_context
def stop(ctx):
    """AB0=>28BL >1@01>B:C 2845>."""
    logger = ctx.obj["LOGGER"]
    logger.info("><0=40 stop 2K?>;=5=0")
    click.echo("AB0=>2:0 >1@01>B:8 2845>...")


@cli.command()
@click.option("--api", type=click.Choice(["rev_ai", "claude"]), help="@>25@8BL B>;L:> C:070==K9 API.")
@click.pass_context
def test(ctx, api):
    """@>25@8BL =0AB@>9:8 8 A>548=5=8O A API."""
    logger = ctx.obj["LOGGER"]
    logger.info("><0=40 test 2K?>;=5=0", api=api)
    
    if api:
        click.echo(f"@>25@:0 A>548=5=8O A {api}...")
    else:
        click.echo("@>25@:0 2A5E =0AB@>5: 8 A>548=5=89...")


#  538AB@0F8O 4>?>;=8B5;L=KE :><0=4 87 4@C38E <>4C;59
logs_command.register_commands(cli)


def main():
    """">G:0 2E>40 4;O CLI."""
    try:
        cli(obj={})
    except Exception as e:
        click.echo(f"H81:0: {str(e)}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()