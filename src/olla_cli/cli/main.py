"""Main CLI entry point and base command group."""

import click
import sys
from pathlib import Path
from typing import Optional

from .. import __version__
from ..config import Config, setup_logging
from ..ui import FormatterFactory

# Import essential command groups only
from .config_commands import config
from .intelligent_cli import smart


@click.group(invoke_without_command=True)
@click.option('--model', '-m', help='Override the model to use')
@click.option('--temperature', '-t', type=float, help='Override temperature setting (0.0-1.0)')
@click.option('--context-length', '-c', type=int, help='Override context length')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--theme', type=click.Choice(['dark', 'light', 'auto']), help='Output theme')
@click.option('--no-color', is_flag=True, help='Disable colored output')
@click.pass_context
def main(ctx, model: Optional[str], temperature: Optional[float], context_length: Optional[int], 
         verbose: bool, theme: Optional[str], no_color: bool):
    """Olla CLI - Your AI coding assistant with interactive mode.
    
    Olla CLI runs in interactive mode by default. Just tell it what you want
    to do in natural language and it will intelligently execute the actions.
    
    Available commands:
      olla-cli            # Start interactive mode (default)
      olla-cli config     # Manage configuration
      olla-cli version    # Show version
    """
    ctx.ensure_object(dict)
    
    # Setup logging
    logger = setup_logging(
        level="DEBUG" if verbose else "INFO",
        verbose=verbose
    )
    
    try:
        config = Config()
    except Exception as e:
        click.echo(f"Error loading configuration: {e}", err=True)
        sys.exit(1)
    
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    ctx.obj['logger'] = logger
    
    if model:
        ctx.obj['model'] = model
    else:
        ctx.obj['model'] = config.get('model')
    
    if temperature is not None:
        if not 0.0 <= temperature <= 1.0:
            click.echo("Error: Temperature must be between 0.0 and 1.0", err=True)
            sys.exit(1)
        ctx.obj['temperature'] = temperature
    else:
        ctx.obj['temperature'] = config.get('temperature')
    
    if context_length is not None:
        if context_length <= 0:
            click.echo("Error: Context length must be positive", err=True)
            sys.exit(1)
        ctx.obj['context_length'] = context_length
    else:
        ctx.obj['context_length'] = config.get('context_length')
    
    # Store formatting options
    ctx.obj['theme'] = theme
    ctx.obj['no_color'] = no_color
    
    # Create formatter
    formatter_options = {}
    if theme:
        formatter_options['theme_override'] = theme
    if no_color:
        formatter_options['syntax_highlight'] = False
    
    ctx.obj['formatter'] = FormatterFactory.create_formatter(config, **formatter_options)
    
    # Start interactive mode by default if no subcommand is invoked
    if ctx.invoked_subcommand is None:
        # Use the smart command in interactive mode
        ctx.invoke(smart, request=None, debug=False, health=False, interactive=True)
        return


@main.command()
def version():
    """Show version information."""
    click.echo(f"Olla CLI version {__version__}")


# Register essential commands only
main.add_command(config)