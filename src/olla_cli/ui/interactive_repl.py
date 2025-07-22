"""Interactive REPL interface for olla-cli using prompt_toolkit."""

import os
import sys
import traceback
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime
import logging

# Import prompt_toolkit components
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.history import FileHistory
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.filters import Condition

# Import Pygments for syntax highlighting
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.formatters import Terminal256Formatter
from pygments.util import ClassNotFound

from .interactive_session import SessionManager, InteractiveSession, SessionContext
from ..commands import CommandImplementations, DetailLevel, ReviewFocus, RefactorType
from ..client import OllamaClient
from ..client import ModelManager
from ..context import ContextBuilder as ContextManager, ContextStrategy
from ..utils import TokenCounter, MessageBuilder, ResponseFormatter, format_error_message
from ..core import OllamaConnectionError, ModelNotFoundError

logger = logging.getLogger('olla-cli')


class OllaCompleter(Completer):
    """Auto-completer for olla-cli interactive mode."""
    
    def __init__(self):
        self.path_completer = PathCompleter()
        
        # Define completions for different contexts
        self.commands = [
            'explain', 'review', 'refactor', 'debug', 'generate', 'test', 'document',
            'models', 'config', 'context'
        ]
        
        self.interactive_commands = [
            '/clear', '/context', '/save', '/load', '/sessions', '/help', '/exit', '/quit',
            '/stats', '/model', '/temperature', '/history', '/search'
        ]
        
        self.options = [
            '--detail-level', '--focus', '--type', '--language', '--framework',
            '--template', '--output-file', '--stream', '--coverage', '--format',
            '--line-range', '--error', '--stack-trace', '--stdin'
        ]
        
        self.detail_levels = ['brief', 'normal', 'comprehensive']
        self.focus_areas = ['security', 'performance', 'style', 'bugs', 'all']
        self.refactor_types = ['simplify', 'optimize', 'modernize', 'general']
        self.languages = ['python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'rust', 'go']
        self.frameworks = ['flask', 'django', 'fastapi', 'react', 'vue', 'angular', 'express']
        self.templates = ['function', 'class', 'api_endpoint']
    
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        
        # Interactive commands (start with /)
        if text.startswith('/'):
            for cmd in self.interactive_commands:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
            return
        
        # File path completion
        if any(text.endswith(prefix) for prefix in ['./', '../', '/', '~/']):
            yield from self.path_completer.get_completions(document, complete_event)
            return
        
        words = text.split()
        if not words:
            # Suggest main commands
            for cmd in self.commands:
                yield Completion(cmd)
            return
        
        current_word = words[-1]
        
        # Command completion
        if len(words) == 1:
            for cmd in self.commands:
                if cmd.startswith(current_word):
                    yield Completion(cmd, start_position=-len(current_word))
        
        # Option completion
        elif current_word.startswith('--'):
            for option in self.options:
                if option.startswith(current_word):
                    yield Completion(option, start_position=-len(current_word))
        
        # Value completion for specific options
        elif len(words) >= 2:
            prev_word = words[-2]
            
            if prev_word == '--detail-level':
                for level in self.detail_levels:
                    if level.startswith(current_word):
                        yield Completion(level, start_position=-len(current_word))
            
            elif prev_word == '--focus':
                for focus in self.focus_areas:
                    if focus.startswith(current_word):
                        yield Completion(focus, start_position=-len(current_word))
            
            elif prev_word == '--type':
                for ref_type in self.refactor_types:
                    if ref_type.startswith(current_word):
                        yield Completion(ref_type, start_position=-len(current_word))
            
            elif prev_word == '--language':
                for lang in self.languages:
                    if lang.startswith(current_word):
                        yield Completion(lang, start_position=-len(current_word))
            
            elif prev_word == '--framework':
                for framework in self.frameworks:
                    if framework.startswith(current_word):
                        yield Completion(framework, start_position=-len(current_word))
            
            elif prev_word == '--template':
                for template in self.templates:
                    if template.startswith(current_word):
                        yield Completion(template, start_position=-len(current_word))


class InteractiveREPL:
    """Interactive REPL for olla-cli."""
    
    def __init__(self, config, model: str, temperature: float, context_length: int, verbose: bool = False):
        self.config = config
        self.model = model
        self.temperature = temperature
        self.context_length = context_length
        self.verbose = verbose
        
        # Initialize components
        self.session_manager = SessionManager()
        self.current_session: Optional[InteractiveSession] = None
        
        # Initialize olla-cli components
        api_url = config.get('api_url', 'http://localhost:11434')
        self.client = OllamaClient(host=api_url, timeout=30)
        self.model_manager = ModelManager(self.client)
        
        try:
            self.context_manager = ContextManager()
        except Exception as e:
            logger.warning(f"Could not initialize context manager: {e}")
            self.context_manager = None
        
        self.command_impl = CommandImplementations(
            self.client, self.model_manager, self.context_manager
        )
        
        # Setup prompt session
        self.setup_prompt_session()
        
        # Setup syntax highlighting
        self.formatter = Terminal256Formatter(style='monokai')
        
        # Interactive command handlers
        self.interactive_handlers = {
            '/clear': self._handle_clear,
            '/context': self._handle_context,
            '/save': self._handle_save,
            '/load': self._handle_load,
            '/sessions': self._handle_sessions,
            '/help': self._handle_help,
            '/exit': self._handle_exit,
            '/quit': self._handle_exit,
            '/stats': self._handle_stats,
            '/model': self._handle_model,
            '/temperature': self._handle_temperature,
            '/history': self._handle_history,
            '/search': self._handle_search
        }
    
    def setup_prompt_session(self):
        """Setup prompt_toolkit session with all features."""
        
        # History file
        history_file = Path.home() / '.olla-cli' / 'history.txt'
        history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Key bindings
        bindings = KeyBindings()
        
        @bindings.add('c-c')
        def _(event):
            """Handle Ctrl+C."""
            event.app.exit()
        
        @bindings.add('c-d')
        def _(event):
            """Handle Ctrl+D (EOF)."""
            if len(event.app.current_buffer.text) == 0:
                event.app.exit()
        
        # Multi-line condition
        @Condition
        def is_multiline():
            return False  # We'll handle this differently
        
        # Custom style
        style = Style.from_dict({
            'prompt': '#00aa00 bold',
            'path': '#ffaa00',
            'error': '#ff0066',
            'success': '#00aa00',
            'info': '#0066ff',
            'warning': '#ff8800',
            'code': '#ffffff bg:#333333',
        })
        
        # Create prompt session
        self.session = PromptSession(
            message=[('class:prompt', 'olla> ')],
            completer=OllaCompleter(),
            history=FileHistory(str(history_file)),
            key_bindings=bindings,
            style=style,
            multiline=False,
            wrap_lines=True
        )
    
    def print_welcome(self):
        """Print welcome message."""
        welcome_text = [
            ('class:success', '🚀 Welcome to Olla CLI Interactive Mode!\n'),
            ('', 'Type commands naturally or use these special commands:\n'),
            ('class:info', '  /help     '), ('', '- Show available commands\n'),
            ('class:info', '  /clear    '), ('', '- Clear conversation history\n'),
            ('class:info', '  /save     '), ('', '- Save current session\n'),
            ('class:info', '  /sessions '), ('', '- List all sessions\n'),
            ('class:info', '  /exit     '), ('', '- Exit interactive mode\n'),
            ('', '\nYou can use commands like: '),
            ('class:code', 'explain <code>'), ('', ', '),
            ('class:code', 'review file.py'), ('', ', '),
            ('class:code', 'generate "fibonacci function"'), ('', '\n\n')
        ]
        print_formatted_text(FormattedText(welcome_text))
    
    def print_session_info(self):
        """Print current session information."""
        if self.current_session:
            token_count = self.current_session.get_total_tokens()
            context_usage = f"{token_count}/{self.context_length}"
            
            info_text = [
                ('class:info', f'📋 Session: '), ('', f'{self.current_session.name}\n'),
                ('class:info', f'🤖 Model: '), ('', f'{self.model}\n'),
                ('class:info', f'🎛️  Temperature: '), ('', f'{self.temperature}\n'),
                ('class:info', f'📊 Tokens: '), ('', f'{context_usage}\n')
            ]
            
            if self.current_session.context.current_file:
                info_text.extend([
                    ('class:info', f'📄 File: '), 
                    ('class:path', f'{self.current_session.context.current_file}\n')
                ])
            
            print_formatted_text(FormattedText(info_text))
    
    def print_formatted_code(self, code: str, language: str = 'python'):
        """Print syntax-highlighted code."""
        try:
            lexer = get_lexer_by_name(language)
            formatted = self.formatter.format(lexer.get_tokens(code))
            print(formatted, end='')
        except ClassNotFound:
            print(code)
    
    def run(self):
        """Run the interactive REPL."""
        try:
            # Test connection
            self.client.test_connection()
        except OllamaConnectionError:
            print_formatted_text(FormattedText([
                ('class:error', '❌ Cannot connect to Ollama server.\n'),
                ('', 'Please ensure Ollama is running and accessible.\n')
            ]))
            return
        
        # Validate model
        try:
            self.model_manager.validate_model(self.model)
        except ModelNotFoundError:
            print_formatted_text(FormattedText([
                ('class:error', f'❌ Model "{self.model}" not found.\n'),
                ('', 'Use "models list" to see available models.\n')
            ]))
            return
        
        # Create initial session
        self.current_session = self.session_manager.create_session()
        self.current_session.context.model = self.model
        self.current_session.context.temperature = self.temperature
        self.current_session.context.context_length = self.context_length
        
        if self.context_manager:
            self.current_session.context.working_directory = self.context_manager.project_root
            self.current_session.context.language = self.context_manager.project_info.language
            self.current_session.context.framework = self.context_manager.project_info.framework
        
        # Print welcome and session info
        self.print_welcome()
        self.print_session_info()
        
        # Main REPL loop
        while True:
            try:
                # Get user input
                user_input = self.session.prompt().strip()
                
                if not user_input:
                    continue
                
                # Handle interactive commands
                if user_input.startswith('/'):
                    if self._handle_interactive_command(user_input):
                        break  # Exit requested
                    continue
                
                # Handle regular olla-cli commands
                self._handle_command(user_input)
                
            except KeyboardInterrupt:
                print_formatted_text(FormattedText([('class:warning', '\nInterrupted. Use /exit to quit.\n')]))
                continue
            
            except EOFError:
                print_formatted_text(FormattedText([('class:info', '\nGoodbye!\n')]))
                break
            
            except Exception as e:
                print_formatted_text(FormattedText([
                    ('class:error', f'❌ Unexpected error: {format_error_message(e)}\n')
                ]))
                if self.verbose:
                    print(traceback.format_exc())
        
        # Save session before exit
        if self.current_session:
            self.session_manager.save_session(self.current_session)
    
    def _handle_interactive_command(self, command: str) -> bool:
        """Handle interactive commands. Returns True if exit requested."""
        parts = command.split()
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd in self.interactive_handlers:
            return self.interactive_handlers[cmd](args)
        else:
            print_formatted_text(FormattedText([
                ('class:error', f'❌ Unknown command: {cmd}\n'),
                ('', 'Type /help for available commands.\n')
            ]))
        
        return False
    
    def _handle_command(self, command: str):
        """Handle regular olla-cli commands."""
        # Add user message to history
        user_message = self.current_session.add_message('user', command)
        
        # Parse command
        try:
            response_generator = self._execute_command(command)
            
            # Stream and display response
            response_content = []
            print_formatted_text(FormattedText([('class:success', '✨ Response:\n')]))
            
            for chunk in response_generator:
                print(chunk, end='', flush=True)
                response_content.append(chunk)
            
            print()  # Final newline
            
            # Add assistant response to history
            full_response = ''.join(response_content)
            self.current_session.add_message('assistant', full_response)
            
            # Show token usage
            token_count = self.current_session.get_total_tokens()
            usage_percent = (token_count / self.context_length) * 100
            
            print_formatted_text(FormattedText([
                ('class:info', f'📊 Tokens: {token_count}/{self.context_length} ({usage_percent:.1f}%)\n')
            ]))
            
        except Exception as e:
            print_formatted_text(FormattedText([
                ('class:error', f'❌ Error: {format_error_message(e)}\n')
            ]))
            if self.verbose:
                print(traceback.format_exc())
    
    def _execute_command(self, command: str):
        """Execute olla-cli command and return response generator."""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Simple command routing - in a full implementation, you'd use proper CLI parsing
        if cmd == 'explain':
            code = ' '.join(args) if args else ''
            return self.command_impl.explain_code(
                code=code,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
        
        elif cmd == 'review':
            code = ' '.join(args) if args else ''
            return self.command_impl.review_code(
                code=code,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
        
        elif cmd == 'refactor':
            code = ' '.join(args) if args else ''
            return self.command_impl.refactor_code(
                code=code,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
        
        elif cmd == 'debug':
            code = ' '.join(args) if args else ''
            return self.command_impl.debug_code(
                code=code,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
        
        elif cmd == 'generate':
            description = ' '.join(args) if args else ''
            return self.command_impl.generate_code(
                description=description,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
        
        elif cmd == 'test':
            code = ' '.join(args) if args else ''
            return self.command_impl.generate_tests(
                code=code,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
        
        elif cmd == 'document':
            code = ' '.join(args) if args else ''
            return self.command_impl.document_code(
                code=code,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
        
        else:
            # For free-form queries, use explain as default
            full_query = command
            return self.command_impl.explain_code(
                code=full_query,
                model=self.model,
                temperature=self.temperature,
                stream=True
            )
    
    # Interactive command handlers
    def _handle_clear(self, args: List[str]) -> bool:
        """Clear conversation history."""
        if self.current_session:
            self.current_session.clear_history()
            print_formatted_text(FormattedText([('class:success', '✅ Conversation history cleared.\n')]))
        return False
    
    def _handle_context(self, args: List[str]) -> bool:
        """Show current context."""
        if not self.current_session:
            print_formatted_text(FormattedText([('class:error', '❌ No active session.\n')]))
            return False
        
        ctx = self.current_session.context
        context_text = [
            ('class:info', '📋 Current Context:\n'),
            ('', f'  Model: {ctx.model}\n'),
            ('', f'  Temperature: {ctx.temperature}\n'),
            ('', f'  Context Length: {ctx.context_length}\n'),
        ]
        
        if ctx.current_file:
            context_text.append(('', f'  Current File: {ctx.current_file}\n'))
        
        if ctx.working_directory:
            context_text.append(('', f'  Working Directory: {ctx.working_directory}\n'))
        
        if ctx.language:
            context_text.append(('', f'  Language: {ctx.language}\n'))
        
        if ctx.framework:
            context_text.append(('', f'  Framework: {ctx.framework}\n'))
        
        print_formatted_text(FormattedText(context_text))
        return False
    
    def _handle_save(self, args: List[str]) -> bool:
        """Save current session."""
        if not self.current_session:
            print_formatted_text(FormattedText([('class:error', '❌ No active session to save.\n')]))
            return False
        
        if args:
            self.current_session.name = ' '.join(args)
        
        if self.session_manager.save_session(self.current_session):
            print_formatted_text(FormattedText([
                ('class:success', f'✅ Session saved: {self.current_session.name}\n')
            ]))
        else:
            print_formatted_text(FormattedText([('class:error', '❌ Failed to save session.\n')]))
        
        return False
    
    def _handle_load(self, args: List[str]) -> bool:
        """Load a session."""
        if not args:
            # Show available sessions
            sessions = self.session_manager.list_sessions()
            if not sessions:
                print_formatted_text(FormattedText([('class:info', '📋 No saved sessions found.\n')]))
                return False
            
            print_formatted_text(FormattedText([('class:info', '📋 Available sessions:\n')]))
            for session in sessions[:10]:  # Show last 10
                print_formatted_text(FormattedText([
                    ('', f'  {session["id"][:8]}: {session["name"]} ({session["updated_str"]})\n')
                ]))
            
            print_formatted_text(FormattedText([('', '\nUse: /load <session_id>\n')]))
            return False
        
        session_id = args[0]
        # If short ID provided, find matching session
        if len(session_id) < 32:
            sessions = self.session_manager.list_sessions()
            matching = [s for s in sessions if s['id'].startswith(session_id)]
            if len(matching) == 1:
                session_id = matching[0]['id']
            elif len(matching) > 1:
                print_formatted_text(FormattedText([
                    ('class:error', '❌ Multiple sessions match that ID:\n')
                ]))
                for session in matching:
                    print_formatted_text(FormattedText([
                        ('', f'  {session["id"][:8]}: {session["name"]}\n')
                    ]))
                return False
            else:
                print_formatted_text(FormattedText([('class:error', '❌ Session not found.\n')]))
                return False
        
        session = self.session_manager.load_session(session_id)
        if session:
            # Save current session first
            if self.current_session:
                self.session_manager.save_session(self.current_session)
            
            self.current_session = session
            self.model = session.context.model
            self.temperature = session.context.temperature
            
            print_formatted_text(FormattedText([
                ('class:success', f'✅ Loaded session: {session.name}\n')
            ]))
            self.print_session_info()
        else:
            print_formatted_text(FormattedText([('class:error', '❌ Failed to load session.\n')]))
        
        return False
    
    def _handle_sessions(self, args: List[str]) -> bool:
        """List all sessions."""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            print_formatted_text(FormattedText([('class:info', '📋 No saved sessions found.\n')]))
            return False
        
        print_formatted_text(FormattedText([('class:info', f'📋 Found {len(sessions)} sessions:\n')]))
        
        for i, session in enumerate(sessions[:20]):  # Show last 20
            current_marker = '●' if (self.current_session and 
                                   session['id'] == self.current_session.session_id) else '○'
            
            print_formatted_text(FormattedText([
                ('class:info', f'  {current_marker} '),
                ('', f'{session["id"][:8]}: '),
                ('class:path', f'{session["name"]}'),
                ('', f' ({session["updated_str"]})\n')
            ]))
        
        if len(sessions) > 20:
            print_formatted_text(FormattedText([('', f'  ... and {len(sessions) - 20} more\n')]))
        
        return False
    
    def _handle_help(self, args: List[str]) -> bool:
        """Show help information."""
        help_text = [
            ('class:success', '🔧 Olla CLI Interactive Commands:\n\n'),
            
            ('class:info', 'Session Management:\n'),
            ('', '  /save [name]     - Save current session with optional name\n'),
            ('', '  /load <id>       - Load a session by ID\n'),
            ('', '  /sessions        - List all saved sessions\n'),
            ('', '  /clear           - Clear conversation history\n\n'),
            
            ('class:info', 'Information:\n'),
            ('', '  /context         - Show current context\n'),
            ('', '  /stats           - Show session statistics\n'),
            ('', '  /history         - Show recent conversation\n\n'),
            
            ('class:info', 'Configuration:\n'),
            ('', '  /model <name>    - Change model\n'),
            ('', '  /temperature <n> - Set temperature (0.0-1.0)\n\n'),
            
            ('class:info', 'Utilities:\n'),
            ('', '  /search <query>  - Search sessions\n'),
            ('', '  /help            - Show this help\n'),
            ('', '  /exit, /quit     - Exit interactive mode\n\n'),
            
            ('class:info', 'Commands:\n'),
            ('', '  explain <code>           - Explain code functionality\n'),
            ('', '  review <code>            - Review code for issues\n'),
            ('', '  refactor <code>          - Suggest refactoring\n'),
            ('', '  debug <code>             - Help debug issues\n'),
            ('', '  generate <description>   - Generate code\n'),
            ('', '  test <code>              - Generate tests\n'),
            ('', '  document <code>          - Generate documentation\n\n'),
            
            ('', 'You can also ask free-form questions about code!\n')
        ]
        
        print_formatted_text(FormattedText(help_text))
        return False
    
    def _handle_exit(self, args: List[str]) -> bool:
        """Exit interactive mode."""
        print_formatted_text(FormattedText([('class:success', '👋 Goodbye!\n')]))
        return True
    
    def _handle_stats(self, args: List[str]) -> bool:
        """Show session statistics."""
        if not self.current_session:
            print_formatted_text(FormattedText([('class:error', '❌ No active session.\n')]))
            return False
        
        stats = self.session_manager.get_session_stats(self.current_session.session_id)
        if not stats:
            print_formatted_text(FormattedText([('class:error', '❌ Could not get session stats.\n')]))
            return False
        
        stats_text = [
            ('class:info', '📊 Session Statistics:\n'),
            ('', f'  Total Messages: {stats["total_messages"]}\n'),
            ('', f'  User Messages: {stats["user_messages"]}\n'),
            ('', f'  Assistant Messages: {stats["assistant_messages"]}\n'),
            ('', f'  Total Tokens: {stats["total_tokens"]}\n'),
            ('', f'  User Tokens: {stats["user_tokens"]}\n'),
            ('', f'  Assistant Tokens: {stats["assistant_tokens"]}\n'),
            ('', f'  Duration: {stats["duration_minutes"]:.1f} minutes\n'),
            ('', f'  Model: {stats["model"]}\n'),
            ('', f'  Context Length: {stats["context_length"]}\n')
        ]
        
        print_formatted_text(FormattedText(stats_text))
        return False
    
    def _handle_model(self, args: List[str]) -> bool:
        """Change model."""
        if not args:
            print_formatted_text(FormattedText([
                ('class:info', f'Current model: {self.model}\n'),
                ('', 'Use: /model <model_name>\n')
            ]))
            return False
        
        new_model = args[0]
        try:
            self.model_manager.validate_model(new_model)
            self.model = new_model
            
            if self.current_session:
                self.current_session.context.model = new_model
            
            print_formatted_text(FormattedText([
                ('class:success', f'✅ Model changed to: {new_model}\n')
            ]))
        except ModelNotFoundError:
            print_formatted_text(FormattedText([
                ('class:error', f'❌ Model "{new_model}" not found.\n')
            ]))
        
        return False
    
    def _handle_temperature(self, args: List[str]) -> bool:
        """Set temperature."""
        if not args:
            print_formatted_text(FormattedText([
                ('class:info', f'Current temperature: {self.temperature}\n'),
                ('', 'Use: /temperature <value> (0.0-1.0)\n')
            ]))
            return False
        
        try:
            new_temp = float(args[0])
            if not 0.0 <= new_temp <= 1.0:
                raise ValueError("Temperature must be between 0.0 and 1.0")
            
            self.temperature = new_temp
            
            if self.current_session:
                self.current_session.context.temperature = new_temp
            
            print_formatted_text(FormattedText([
                ('class:success', f'✅ Temperature set to: {new_temp}\n')
            ]))
        except ValueError as e:
            print_formatted_text(FormattedText([
                ('class:error', f'❌ Invalid temperature: {e}\n')
            ]))
        
        return False
    
    def _handle_history(self, args: List[str]) -> bool:
        """Show conversation history."""
        if not self.current_session or not self.current_session.messages:
            print_formatted_text(FormattedText([('class:info', '📝 No conversation history.\n')]))
            return False
        
        limit = 10  # Default to last 10 messages
        if args:
            try:
                limit = int(args[0])
            except ValueError:
                pass
        
        recent_messages = self.current_session.get_conversation_history(limit)
        
        print_formatted_text(FormattedText([('class:info', f'📝 Recent History (last {len(recent_messages)} messages):\n')]))
        
        for i, msg in enumerate(recent_messages):
            role_icon = '👤' if msg.role == 'user' else '🤖'
            timestamp = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M")
            
            print_formatted_text(FormattedText([
                ('class:info', f'{role_icon} [{timestamp}] '),
                ('', f'{msg.content[:100]}{"..." if len(msg.content) > 100 else ""}\n')
            ]))
        
        return False
    
    def _handle_search(self, args: List[str]) -> bool:
        """Search sessions."""
        if not args:
            print_formatted_text(FormattedText([
                ('class:error', '❌ Please provide a search query.\n'),
                ('', 'Use: /search <query>\n')
            ]))
            return False
        
        query = ' '.join(args)
        results = self.session_manager.search_sessions(query)
        
        if not results:
            print_formatted_text(FormattedText([('class:info', f'🔍 No sessions found for: "{query}"\n')]))
            return False
        
        print_formatted_text(FormattedText([('class:success', f'🔍 Found {len(results)} sessions:\n')]))
        
        for session in results:
            match_reason = '📝' if session['match_reason'] == 'content' else '📋'
            print_formatted_text(FormattedText([
                ('', f'  {match_reason} {session["id"][:8]}: '),
                ('class:path', f'{session["name"]}'),
                ('', f' ({session["updated_str"]})\n')
            ]))
        
        return False