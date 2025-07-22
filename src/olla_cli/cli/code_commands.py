"""Code analysis and generation commands."""

import click
import sys
from pathlib import Path
from typing import Optional

from ..client import OllamaClient, ModelManager
from ..context import ContextBuilder
from ..commands import CommandImplementations, DetailLevel, ReviewFocus, RefactorType, ProgressIndicator
from ..core import OllamaConnectionError, ModelNotFoundError
from ..utils import format_error_message


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
    """Execute a code command using the CommandImplementations class."""
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
            context_manager = ContextBuilder()
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
            response_iter = _get_command_response(command_impl, command, code_or_description, 
                                                file_path, options, model, temperature, language)
            
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


def _get_command_response(command_impl, command, code_or_description, file_path, options, 
                         model, temperature, language):
    """Get response iterator for the specified command."""
    if command == 'explain':
        return command_impl.explain_code(
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
        return command_impl.review_code(
            code=code_or_description,
            file_path=file_path,
            focus=options.get('focus', ReviewFocus.ALL),
            model=model,
            temperature=temperature,
            stream=options.get('stream', True),
            language=language
        )
    
    elif command == 'refactor':
        return command_impl.refactor_code(
            code=code_or_description,
            file_path=file_path,
            refactor_type=options.get('refactor_type', RefactorType.GENERAL),
            model=model,
            temperature=temperature,
            stream=options.get('stream', True),
            language=language
        )
    
    elif command == 'debug':
        return command_impl.debug_code(
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
        return command_impl.generate_code(
            description=code_or_description,
            language=options.get('language', 'python'),
            framework=options.get('framework'),
            template=options.get('template'),
            model=model,
            temperature=temperature,
            stream=options.get('stream', True)
        )
    
    elif command == 'test':
        return command_impl.generate_tests(
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
        return command_impl.document_code(
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


@click.command()
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
    """Explain code functionality and logic with olla-cli intelligence."""
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


@click.command()
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
    """Review code for issues and improvements with olla-cli expertise."""
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


@click.command()
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
    """Refactor code with intelligent olla-cli suggestions."""
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


@click.command()
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
    """Debug code with olla-cli expert assistance."""
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


@click.command()
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
    """Generate code with olla-cli intelligence."""
    _execute_command(ctx, 'generate', description, None, {
        'language': language,
        'framework': framework,
        'template': template,
        'output_file': output_file,
        'no_syntax_highlighting': no_syntax_highlighting,
        'stream': stream
    })


@click.command()
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
    """Generate comprehensive tests with olla-cli intelligence."""
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


@click.command()
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
    """Generate comprehensive documentation with olla-cli expertise."""
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