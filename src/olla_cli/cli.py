"""Main CLI module for Olla CLI."""

import click
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .config import Config
from .ollama_client import OllamaClient
from .model_manager import ModelManager
from .utils import MessageBuilder, ResponseFormatter, parse_model_response, format_error_message
from .exceptions import (
    OllamaConnectionError, ModelNotFoundError, ContextLimitExceededError,
    StreamingError, OllamaServerError
)
from .logging_config import setup_logging
from .context_cli import context
from .command_implementations import (
    CommandImplementations, DetailLevel, ReviewFocus, RefactorType,
    ProgressIndicator, TemplateManager
)


@click.group()
@click.option('--model', '-m', help='Override the model to use')
@click.option('--temperature', '-t', type=float, help='Override temperature setting (0.0-1.0)')
@click.option('--context-length', '-c', type=int, help='Override context length')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def main(ctx, model: Optional[str], temperature: Optional[float], context_length: Optional[int], verbose: bool):
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


@main.command()
def version():
    """Show version information."""
    click.echo(f"Olla CLI version {__version__}")


@main.command()
@click.option('--session', '-s', help='Load a specific session by ID or name')
@click.option('--new-session', is_flag=True, help='Force create a new session')
@click.pass_context
def chat(ctx, session: Optional[str], new_session: bool):
    """Start interactive chat mode with conversation history.
    
    Enter a conversational REPL where you can chat with olla-cli, maintain
    context across commands, save sessions, and use special commands.
    
    Examples:
      olla-cli chat
      olla-cli chat --session my-session
      olla-cli chat --new-session
    
    Special commands in chat mode:
      /help      - Show available commands
      /clear     - Clear conversation history
      /save      - Save current session
      /sessions  - List all sessions
      /exit      - Exit chat mode
    """
    try:
        from .interactive_repl import InteractiveREPL
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
            # Try to load existing session
            sessions = repl.session_manager.list_sessions()
            
            # Search by name first
            matching_sessions = [s for s in sessions if s['name'].lower() == session.lower()]
            if not matching_sessions:
                # Search by ID prefix
                matching_sessions = [s for s in sessions if s['id'].startswith(session)]
            
            if len(matching_sessions) == 1:
                loaded_session = repl.session_manager.load_session(matching_sessions[0]['id'])
                if loaded_session:
                    repl.current_session = loaded_session
                    repl.model = loaded_session.context.model
                    repl.temperature = loaded_session.context.temperature
                    click.echo(f"✅ Loaded session: {loaded_session.name}")
                else:
                    click.echo(f"❌ Failed to load session: {session}", err=True)
                    sys.exit(1)
            elif len(matching_sessions) > 1:
                click.echo(f"❌ Multiple sessions match '{session}':", err=True)
                for s in matching_sessions[:5]:
                    click.echo(f"  {s['id'][:8]}: {s['name']}")
                sys.exit(1)
            else:
                click.echo(f"❌ Session not found: {session}", err=True)
                sys.exit(1)
        
        # Start interactive mode
        repl.run()
        
    except KeyboardInterrupt:
        click.echo("\n👋 Chat mode interrupted.", err=True)
    except Exception as e:
        click.echo(f"❌ Error in chat mode: {format_error_message(e)}", err=True)
        if verbose:
            import traceback
            click.echo(f"\nTraceback:\n{traceback.format_exc()}", err=True)
        sys.exit(1)


@main.group()
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


@main.group()
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


@main.command()
@click.argument('file_or_code', required=False)
@click.option('--stdin', is_flag=True, help='Read code from stdin')
@click.option('--line-range', help='Specific line range (e.g., "10-20")')
@click.option('--detail-level', type=click.Choice(['brief', 'normal', 'comprehensive']), 
              default='normal', help='Level of detail in explanation')
@click.option('--output-file', '-o', help='Save output to file')
@click.option('--no-syntax-highlighting', is_flag=True, help='Disable syntax highlighting')
@click.option('--stream', is_flag=True, default=True, help='Stream output in real-time')
@click.pass_context
def explain(ctx, file_or_code: Optional[str], stdin: bool, line_range: Optional[str], 
           detail_level: str, output_file: Optional[str], no_syntax_highlighting: bool, stream: bool):
    """Explain code functionality and logic with olla-cli intelligence.
    
    Provide detailed explanations of what code does, how it works, and why it's designed that way.
    Supports file paths, code snippets, and stdin input with intelligent context awareness.
    
    Examples:
      olla-cli explain main.py --detail-level comprehensive
      olla-cli explain "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
      olla-cli explain src/utils.py --line-range "50-80" --output-file explanation.md
      cat algorithm.py | olla-cli explain --stdin --detail-level brief
    """
    code = _get_code_input(file_or_code, stdin)
    if not code:
        click.echo("❌ Error: No code provided", err=True)
        click.echo("Use a file path, code snippet, or pipe input via stdin", err=True)
        sys.exit(1)
    
    # Parse line range
    parsed_line_range = None
    if line_range:
        try:
            start, end = map(int, line_range.split('-'))
            parsed_line_range = (start, end)
        except ValueError:
            click.echo(f"❌ Invalid line range format: {line_range}. Use format '10-20'", err=True)
            sys.exit(1)
    
    _execute_command(ctx, 'explain', code, file_or_code, {
        'line_range': parsed_line_range,
        'detail_level': DetailLevel(detail_level),
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


@main.command()
@click.argument('file_or_code', required=False)
@click.option('--stdin', is_flag=True, help='Read code from stdin')
@click.option('--focus', type=click.Choice(['security', 'performance', 'style', 'bugs', 'all']), 
              default='all', help='Focus area for review')
@click.option('--output-file', '-o', help='Save output to file')
@click.option('--no-syntax-highlighting', is_flag=True, help='Disable syntax highlighting')
@click.option('--stream', is_flag=True, default=True, help='Stream output in real-time')
@click.pass_context
def review(ctx, file_or_code: Optional[str], stdin: bool, focus: str, 
          output_file: Optional[str], no_syntax_highlighting: bool, stream: bool):
    """Review code for issues and improvements with olla-cli expertise.
    
    Analyze code for potential problems, security vulnerabilities, performance issues,
    and style improvements. Provides severity-rated findings with actionable suggestions.
    
    Examples:
      olla-cli review main.py --focus security
      olla-cli review algorithm.py --focus performance --output-file review.md
      olla-cli review "password = input(); exec(password)" --focus security
      cat src/api.py | olla-cli review --stdin --focus all
    """
    code = _get_code_input(file_or_code, stdin)
    if not code:
        click.echo("❌ Error: No code provided", err=True)
        sys.exit(1)
    
    _execute_command(ctx, 'review', code, file_or_code, {
        'focus': ReviewFocus(focus),
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


@main.command()
@click.argument('file_or_code', required=False)
@click.option('--stdin', is_flag=True, help='Read code from stdin')
@click.option('--type', 'refactor_type', type=click.Choice(['simplify', 'optimize', 'modernize', 'general']), 
              default='general', help='Type of refactoring to focus on')
@click.option('--output-file', '-o', help='Save output to file')
@click.option('--no-syntax-highlighting', is_flag=True, help='Disable syntax highlighting')
@click.option('--stream', is_flag=True, default=True, help='Stream output in real-time')
@click.pass_context
def refactor(ctx, file_or_code: Optional[str], stdin: bool, refactor_type: str,
            output_file: Optional[str], no_syntax_highlighting: bool, stream: bool):
    """Refactor code with intelligent olla-cli suggestions.
    
    Analyze code and suggest improvements for better structure, readability, and maintainability.
    Shows before/after comparisons with detailed explanations of benefits.
    
    Examples:
      olla-cli refactor legacy_code.py --type modernize
      olla-cli refactor "if x == True: return True" --type simplify
      olla-cli refactor algorithm.py --type optimize --output-file refactored.md
      cat messy_code.py | olla-cli refactor --stdin --type general
    """
    code = _get_code_input(file_or_code, stdin)
    if not code:
        click.echo("❌ Error: No code provided", err=True)
        sys.exit(1)
    
    _execute_command(ctx, 'refactor', code, file_or_code, {
        'refactor_type': RefactorType(refactor_type),
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


@main.command()
@click.argument('file_or_code', required=False)
@click.option('--stdin', is_flag=True, help='Read code from stdin')
@click.option('--error', help='Error message you encountered')
@click.option('--stack-trace', help='Full stack trace of the error')
@click.option('--output-file', '-o', help='Save output to file')
@click.option('--no-syntax-highlighting', is_flag=True, help='Disable syntax highlighting')
@click.option('--stream', is_flag=True, default=True, help='Stream output in real-time')
@click.pass_context
def debug(ctx, file_or_code: Optional[str], stdin: bool, error: Optional[str], 
         stack_trace: Optional[str], output_file: Optional[str], 
         no_syntax_highlighting: bool, stream: bool):
    """Debug code with olla-cli expert assistance.
    
    Get step-by-step debugging help, error analysis, and concrete solutions.
    Analyzes error messages, stack traces, and code context for comprehensive debugging.
    
    Examples:
      olla-cli debug broken_script.py --error "KeyError: 'missing_key'"
      olla-cli debug "users[0]" --error "IndexError" --stack-trace "Traceback..."
      cat buggy_code.py | olla-cli debug --stdin --error "AttributeError: 'NoneType'"
    """
    code = _get_code_input(file_or_code, stdin)
    if not code:
        click.echo("❌ Error: No code provided", err=True)
        sys.exit(1)
    
    _execute_command(ctx, 'debug', code, file_or_code, {
        'error_message': error,
        'stack_trace': stack_trace,
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


@main.command()
@click.argument('description')
@click.option('--language', '-l', default='python', help='Programming language (default: python)')
@click.option('--framework', '-f', help='Framework to use (e.g., flask, react, express)')
@click.option('--template', type=click.Choice(['function', 'class', 'api_endpoint']), 
              help='Code template to follow')
@click.option('--output-file', '-o', help='Save output to file')
@click.option('--no-syntax-highlighting', is_flag=True, help='Disable syntax highlighting')
@click.option('--stream', is_flag=True, default=True, help='Stream output in real-time')
@click.pass_context
def generate(ctx, description: str, language: str, framework: Optional[str], 
            template: Optional[str], output_file: Optional[str], 
            no_syntax_highlighting: bool, stream: bool):
    """Generate code with olla-cli intelligence.
    
    Create production-ready code from natural language descriptions with proper documentation,
    error handling, and best practices. Supports templates and framework-specific patterns.
    
    Examples:
      olla-cli generate "user authentication system" --language python --framework flask
      olla-cli generate "binary search tree" --template class --output-file tree.py
      olla-cli generate "REST API for blog posts" --language javascript --framework express
      olla-cli generate "data validation function" --template function --language typescript
    """
    _execute_command(ctx, 'generate', description, None, {
        'language': language,
        'framework': framework,
        'template': template,
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


@main.command()
@click.argument('file_or_code', required=False)
@click.option('--stdin', is_flag=True, help='Read code from stdin')
@click.option('--framework', default='pytest', help='Testing framework (default: pytest)')
@click.option('--coverage', is_flag=True, help='Generate comprehensive edge case coverage')
@click.option('--output-file', '-o', help='Save output to file')
@click.option('--no-syntax-highlighting', is_flag=True, help='Disable syntax highlighting')
@click.option('--stream', is_flag=True, default=True, help='Stream output in real-time')
@click.pass_context
def test(ctx, file_or_code: Optional[str], stdin: bool, framework: str, coverage: bool,
         output_file: Optional[str], no_syntax_highlighting: bool, stream: bool):
    """Generate comprehensive tests with olla-cli intelligence.
    
    Create thorough unit tests with edge cases, error handling, and proper test structure.
    Supports multiple testing frameworks and comprehensive coverage strategies.
    
    Examples:
      olla-cli test calculator.py --framework pytest --coverage
      olla-cli test "def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
      olla-cli test api_handler.py --framework unittest --output-file tests.py
      cat utils.py | olla-cli test --stdin --coverage
    """
    code = _get_code_input(file_or_code, stdin)
    if not code:
        click.echo("❌ Error: No code provided", err=True)
        sys.exit(1)
    
    _execute_command(ctx, 'test', code, file_or_code, {
        'framework': framework,
        'coverage': coverage,
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


@main.command()
@click.argument('file_or_code', required=False)
@click.option('--stdin', is_flag=True, help='Read code from stdin')
@click.option('--format', 'doc_format', default='docstring', 
              type=click.Choice(['docstring', 'markdown', 'rst', 'google', 'numpy']),
              help='Documentation format (default: docstring)')
@click.option('--type', 'doc_type', default='api',
              type=click.Choice(['api', 'readme', 'inline']),
              help='Documentation type (default: api)')
@click.option('--output-file', '-o', help='Save output to file')
@click.option('--no-syntax-highlighting', is_flag=True, help='Disable syntax highlighting')
@click.option('--stream', is_flag=True, default=True, help='Stream output in real-time')
@click.pass_context
def document(ctx, file_or_code: Optional[str], stdin: bool, doc_format: str, doc_type: str,
            output_file: Optional[str], no_syntax_highlighting: bool, stream: bool):
    """Generate comprehensive documentation with olla-cli expertise.
    
    Create professional documentation including docstrings, API docs, and usage examples.
    Supports multiple documentation formats and styles with intelligent context awareness.
    
    Examples:
      olla-cli document api_module.py --format google --type api
      olla-cli document "class Calculator:" --format markdown --output-file docs.md
      olla-cli document utils.py --format numpy --type readme
      cat complex_algorithm.py | olla-cli document --stdin --format rst
    """
    code = _get_code_input(file_or_code, stdin)
    if not code:
        click.echo("❌ Error: No code provided", err=True)
        sys.exit(1)
    
    _execute_command(ctx, 'document', code, file_or_code, {
        'doc_format': doc_format,
        'doc_type': doc_type,
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


def _get_code_input(file_or_code: Optional[str], stdin: bool) -> Optional[str]:
    """Get code input from file, argument, or stdin."""
    if stdin:
        return sys.stdin.read().strip()
    
    if not file_or_code:
        return None
    
    try:
        with open(file_or_code, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return file_or_code
    except Exception:
        return file_or_code


def _execute_command(ctx, command: str, code_or_description: str, file_path: Optional[str], options: dict):
    """Execute a command using the CommandImplementations class."""
    config = ctx.obj['config']
    model = ctx.obj['model']
    temperature = ctx.obj['temperature']
    context_length = ctx.obj['context_length']
    verbose = ctx.obj['verbose']
    logger = ctx.obj['logger']
    
    try:
        # Initialize components
        api_url = config.get('api_url', 'http://localhost:11434')
        client = OllamaClient(host=api_url, timeout=30)
        model_manager = ModelManager(client)
        
        # Initialize context manager if we have a project
        try:
            from .context_builder import ContextManager
            context_manager = ContextManager()
        except Exception as e:
            logger.warning(f"Could not initialize context manager: {e}")
            context_manager = None
        
        command_impl = CommandImplementations(client, model_manager, context_manager)
        
        # Test connection
        if verbose:
            click.echo("🔗 Testing connection to Ollama...", err=True)
        
        try:
            client.test_connection()
        except OllamaConnectionError as e:
            click.echo(f"\n❌ Cannot connect to Ollama server at {api_url}", err=True)
            click.echo("Please ensure Ollama is running and accessible.", err=True)
            sys.exit(1)
        
        # Validate model
        try:
            model_info = model_manager.validate_model(model)
            if verbose:
                click.echo(f"✅ Using model: {model} (context: {model_info.context_length})", err=True)
        except ModelNotFoundError:
            click.echo(f"\n❌ Model '{model}' not found", err=True)
            sys.exit(1)
        
        # Show progress indicator
        progress_messages = {
            'explain': f"🔍 Analyzing code with {model}",
            'review': f"🔬 Reviewing code with {model}",
            'refactor': f"🔧 Refactoring code with {model}",
            'debug': f"🐛 Debugging code with {model}",
            'generate': f"⚡ Generating code with {model}",
            'test': f"🧪 Generating tests with {model}",
            'document': f"📝 Generating documentation with {model}"
        }
        
        progress = ProgressIndicator(progress_messages.get(command, f"Processing with {model}"))
        if not options.get('stream', True):
            progress.start()
        
        # Determine language for syntax highlighting
        language = None
        if file_path:
            language = Path(file_path).suffix[1:] if Path(file_path).suffix else None
        
        # Execute command
        try:
            if command == 'explain':
                response_iter = command_impl.explain_code(
                    code=code_or_description,
                    file_path=file_path,
                    line_range=options.get('line_range'),
                    detail_level=options.get('detail_level', DetailLevel.NORMAL),
                    model=model,
                    temperature=temperature,
                    stream=options.get('stream', True),
                    language=language
                )
            
            elif command == 'review':
                response_iter = command_impl.review_code(
                    code=code_or_description,
                    file_path=file_path,
                    focus=options.get('focus', ReviewFocus.ALL),
                    model=model,
                    temperature=temperature,
                    stream=options.get('stream', True),
                    language=language
                )
            
            elif command == 'refactor':
                response_iter = command_impl.refactor_code(
                    code=code_or_description,
                    file_path=file_path,
                    refactor_type=options.get('refactor_type', RefactorType.GENERAL),
                    model=model,
                    temperature=temperature,
                    stream=options.get('stream', True),
                    language=language
                )
            
            elif command == 'debug':
                response_iter = command_impl.debug_code(
                    code=code_or_description,
                    error_message=options.get('error_message'),
                    stack_trace=options.get('stack_trace'),
                    file_path=file_path,
                    model=model,
                    temperature=temperature,
                    stream=options.get('stream', True),
                    language=language
                )
            
            elif command == 'generate':
                response_iter = command_impl.generate_code(
                    description=code_or_description,
                    language=options.get('language', 'python'),
                    framework=options.get('framework'),
                    template=options.get('template'),
                    model=model,
                    temperature=temperature,
                    stream=options.get('stream', True)
                )
            
            elif command == 'test':
                response_iter = command_impl.generate_tests(
                    code=code_or_description,
                    file_path=file_path,
                    framework=options.get('framework', 'pytest'),
                    coverage=options.get('coverage', False),
                    model=model,
                    temperature=temperature,
                    stream=options.get('stream', True),
                    language=language
                )
            
            elif command == 'document':
                response_iter = command_impl.document_code(
                    code=code_or_description,
                    file_path=file_path,
                    doc_format=options.get('doc_format', 'docstring'),
                    doc_type=options.get('doc_type', 'api'),
                    model=model,
                    temperature=temperature,
                    stream=options.get('stream', True),
                    language=language
                )
            
            else:
                raise ValueError(f"Unknown command: {command}")
            
            # Handle output
            output_content = []
            
            if options.get('stream', True):
                progress.stop()
                click.echo(f"\n✨ {command.title()} Results:\n")
                
                for chunk in response_iter:
                    click.echo(chunk, nl=False)
                    output_content.append(chunk)
                click.echo()  # Final newline
            else:
                # Non-streaming: collect all content
                for chunk in response_iter:
                    output_content.append(chunk)
                progress.stop()
                
                full_content = ''.join(output_content)
                click.echo(f"\n✨ {command.title()} Results:\n")
                click.echo(full_content)
            
            # Save to file if requested
            if options.get('output_file'):
                try:
                    with open(options['output_file'], 'w') as f:
                        f.write(''.join(output_content))
                    click.echo(f"\n💾 Results saved to: {options['output_file']}")
                except Exception as e:
                    click.echo(f"\n⚠️ Could not save to file: {e}", err=True)
        
        finally:
            progress.stop()
    
    except KeyboardInterrupt:
        click.echo("\n\n⏹️ Operation cancelled by user.", err=True)
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error in {command} command: {e}")
        click.echo(f"\n❌ Error: {format_error_message(e)}", err=True)
        if verbose:
            import traceback
            click.echo(f"\nTraceback:\n{traceback.format_exc()}", err=True)
        sys.exit(1)


# Register the context management commands
main.add_command(context)


if __name__ == '__main__':
    main()