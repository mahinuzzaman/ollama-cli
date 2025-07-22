"""Model management commands."""

import click
import sys

from ..client import OllamaClient, ModelManager
from ..core import OllamaConnectionError, ModelNotFoundError
from ..utils import format_error_message


@click.group()
@click.pass_context
def models(ctx):
    """Manage Ollama models."""
    pass


@models.command('list')
@click.pass_context
def models_list(ctx):
    """List available models."""
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    
    try:
        api_url = config.get('api_url', 'http://localhost:11434')
        client = OllamaClient(host=api_url)
        model_manager = ModelManager(client)
        
        click.echo("📋 Available models:")
        models = model_manager.get_available_models(refresh=True)
        
        if not models:
            click.echo("No models found. Use 'olla-cli models pull <model>' to download a model.")
            return
        
        for model_info in models:
            size_mb = model_info.size / (1024 * 1024) if model_info.size > 0 else 0
            click.echo(f"  • {model_info.name}")
            if verbose:
                click.echo(f"    Family: {model_info.family}")
                click.echo(f"    Size: {size_mb:.1f}MB")
                click.echo(f"    Parameters: {model_info.parameter_size}")
                click.echo(f"    Context Length: {model_info.context_length}")
                if model_info.capabilities:
                    click.echo(f"    Capabilities: {', '.join(model_info.capabilities)}")
                click.echo()
    
    except Exception as e:
        click.echo(f"Error listing models: {format_error_message(e)}", err=True)
        sys.exit(1)


@models.command('pull')
@click.argument('model_name')
@click.option('--progress', is_flag=True, default=True, help='Show pull progress')
@click.pass_context
def models_pull(ctx, model_name: str, progress: bool):
    """Pull a model from Ollama registry."""
    config = ctx.obj['config']
    
    try:
        api_url = config.get('api_url', 'http://localhost:11434')
        client = OllamaClient(host=api_url)
        
        click.echo(f"📥 Pulling model: {model_name}")
        
        if progress:
            # Stream progress updates
            for chunk in client.pull_model(model_name, stream=True):
                if 'status' in chunk:
                    status = chunk['status']
                    if 'completed' in chunk and 'total' in chunk:
                        completed = chunk['completed']
                        total = chunk['total']
                        percent = (completed / total) * 100 if total > 0 else 0
                        click.echo(f"\r{status}: {percent:.1f}%", nl=False)
                    else:
                        click.echo(f"\r{status}", nl=False)
            click.echo()  # Final newline
        else:
            client.pull_model(model_name, stream=False)
        
        click.echo(f"✅ Successfully pulled model: {model_name}")
    
    except Exception as e:
        click.echo(f"\n❌ Error pulling model: {format_error_message(e)}", err=True)
        sys.exit(1)


@models.command('info')
@click.argument('model_name')
@click.pass_context
def models_info(ctx, model_name: str):
    """Show information about a specific model."""
    config = ctx.obj['config']
    
    try:
        api_url = config.get('api_url', 'http://localhost:11434')
        client = OllamaClient(host=api_url)
        model_manager = ModelManager(client)
        
        # Get model info
        model_info = model_manager.validate_model(model_name)
        raw_info = client.get_model_info(model_name)
        
        click.echo(f"📊 Model Information: {model_name}")
        click.echo(f"  Family: {model_info.family}")
        click.echo(f"  Parameters: {model_info.parameter_size}")
        click.echo(f"  Quantization: {model_info.quantization_level}")
        click.echo(f"  Context Length: {model_info.context_length}")
        
        if model_info.size > 0:
            size_mb = model_info.size / (1024 * 1024)
            size_gb = size_mb / 1024
            if size_gb >= 1:
                click.echo(f"  Size: {size_gb:.1f}GB")
            else:
                click.echo(f"  Size: {size_mb:.1f}MB")
        
        if model_info.capabilities:
            click.echo(f"  Capabilities: {', '.join(model_info.capabilities)}")
        
        if 'details' in raw_info:
            details = raw_info['details']
            if 'parent_model' in details:
                click.echo(f"  Parent Model: {details['parent_model']}")
            if 'format' in details:
                click.echo(f"  Format: {details['format']}")
        
        click.echo(f"  Digest: {model_info.digest[:16]}...")
    
    except ModelNotFoundError as e:
        click.echo(f"❌ {format_error_message(e)}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error getting model info: {format_error_message(e)}", err=True)
        sys.exit(1)