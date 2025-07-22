"""Main CLI entry point and base command group."""

import click
import sys
from pathlib import Path
from typing import Optional

from .. import __version__
from ..config import Config, setup_logging
from ..ui import FormatterFactory

# Import command groups
from .config_commands import config
from .model_commands import models
from .code_commands import explain, review, refactor, debug, generate, test, document
from .task_commands import task, resume, tasks


@click.group()
@click.option('--model', '-m', help='Override the model to use')
@click.option('--temperature', '-t', type=float, help='Override temperature setting (0.0-1.0)')
@click.option('--context-length', '-c', type=int, help='Override context length')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--theme', type=click.Choice(['dark', 'light', 'auto']), help='Output theme')
@click.option('--no-color', is_flag=True, help='Disable colored output')
@click.pass_context
def main(ctx, model: Optional[str], temperature: Optional[float], context_length: Optional[int], 
         verbose: bool, theme: Optional[str], no_color: bool):
    """Olla CLI - A coding assistant command line tool.
    
    Use Olla CLI to explain, review, refactor, debug, generate, test, and document code
    using local language models through Ollama.
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


@main.command()
def version():
    """Show version information."""
    click.echo(f"Olla CLI version {__version__}")


@main.command()
@click.option('--session', '-s', help='Load a specific session by ID or name')
@click.option('--new-session', is_flag=True, help='Force create a new session')
@click.pass_context
def chat(ctx, session: Optional[str], new_session: bool):
    """Start interactive chat mode with conversation history."""
    try:
        from ..ui import InteractiveREPL
    except ImportError as e:
        click.echo("❌ Interactive mode requires additional dependencies.", err=True)
        click.echo("Please install: pip install prompt_toolkit pygments", err=True)
        sys.exit(1)
    
    config = ctx.obj['config']
    model = ctx.obj['model']
    temperature = ctx.obj['temperature']
    context_length = ctx.obj['context_length']
    verbose = ctx.obj['verbose']
    
    try:
        # Initialize REPL
        repl = InteractiveREPL(config, model, temperature, context_length, verbose)
        
        # Handle session loading
        if session and not new_session:
            # Session loading logic here
            pass
        
        # Start interactive mode
        repl.run()
        
    except KeyboardInterrupt:
        click.echo("\n👋 Chat mode interrupted.", err=True)
    except Exception as e:
        from ..utils import format_error_message
        click.echo(f"❌ Error in chat mode: {format_error_message(e)}", err=True)
        if verbose:
            import traceback
            click.echo(f"\nTraceback:\n{traceback.format_exc()}", err=True)
        sys.exit(1)


# Register command groups
main.add_command(config)
main.add_command(models)

# Register code commands
main.add_command(explain)
main.add_command(review)
main.add_command(refactor)
main.add_command(debug)
main.add_command(generate)
main.add_command(test)
main.add_command(document)

# Register task commands
main.add_command(task)
main.add_command(resume)
main.add_command(tasks)