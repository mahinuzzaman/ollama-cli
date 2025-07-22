"""Configuration management commands."""

import click
import sys


@click.group()
@click.pass_context
def config(ctx):
    """Manage configuration settings."""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    config_obj = ctx.obj['config']
    config_data = config_obj.show()
    
    click.echo("Current configuration:")
    for key, value in config_data.items():
        click.echo(f"  {key}: {value}")


@config.command('set')
@click.argument('key')
@click.argument('value')
@click.pass_context
def config_set(ctx, key: str, value: str):
    """Set a configuration value."""
    config_obj = ctx.obj['config']
    
    if key in ['temperature']:
        try:
            value = float(value)
        except ValueError:
            click.echo(f"Error: {key} must be a number", err=True)
            sys.exit(1)
    elif key in ['context_length']:
        try:
            value = int(value)
        except ValueError:
            click.echo(f"Error: {key} must be an integer", err=True)
            sys.exit(1)
    
    try:
        config_obj.set(key, value)
        click.echo(f"Set {key} = {value}")
    except Exception as e:
        click.echo(f"Error saving configuration: {e}", err=True)
        sys.exit(1)


@config.command('reset')
@click.pass_context
def config_reset(ctx):
    """Reset configuration to defaults."""
    config_obj = ctx.obj['config']
    try:
        config_obj.reset()
        click.echo("Configuration reset to defaults")
    except Exception as e:
        click.echo(f"Error resetting configuration: {e}", err=True)
        sys.exit(1)