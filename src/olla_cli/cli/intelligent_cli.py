"""Intelligent CLI Interface with Claude-like capabilities."""

import click
import os
import sys
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..mcp.registry import ToolRegistry
from ..mcp.tools import FileSystemTool, CodeAnalysisTool, WebTool
from ..routing.router import ToolRouter
from ..intelligence.decision_engine import DecisionEngine
from ..intelligence.session_memory import SessionManager
from ..config import Config
from ..utils import format_error_message


class IntelligentCLI:
    """Claude-like intelligent CLI interface."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session_manager = SessionManager()
        self.tool_registry = ToolRegistry()
        self.decision_engine = DecisionEngine()
        self.router = None
        self.current_session = None
        self._setup_tools()
    
    def _setup_tools(self):
        """Initialize and register tools."""
        # Register core tools
        filesystem_tool = FileSystemTool()
        code_tool = CodeAnalysisTool(self.config)
        web_tool = WebTool()
        
        self.tool_registry.register_tool(filesystem_tool)
        self.tool_registry.register_tool(code_tool)
        self.tool_registry.register_tool(web_tool)
        
        # Initialize router with tools
        self.router = ToolRouter(self.tool_registry)
    
    async def initialize_session(self, session_id: Optional[str] = None) -> None:
        """Initialize a new session."""
        self.current_session = await self.session_manager.start_session(session_id)
    
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> List[str]:
        """Process a user request intelligently like Claude CLI."""
        if not self.current_session:
            await self.initialize_session()
        
        # Build context
        if context is None:
            context = {
                'current_directory': os.getcwd(),
                'recent_files': await self._get_recent_files()
            }
        
        try:
            # Route the request through the intelligent system
            results = await self.router.route_request(user_input, context)
            
            # Process results into user-friendly output
            output_lines = []
            for result in results:
                if result.success:
                    if result.data:
                        if isinstance(result.data, str):
                            output_lines.append(result.data)
                        elif isinstance(result.data, dict):
                            output_lines.append(self._format_dict_output(result.data))
                        else:
                            output_lines.append(str(result.data))
                    else:
                        output_lines.append("✅ Operation completed successfully")
                else:
                    error_msg = result.error or "Unknown error occurred"
                    output_lines.append(f"❌ Error: {error_msg}")
            
            # Record interaction for learning
            await self.current_session.record_interaction({
                'type': 'user_request',
                'input': user_input,
                'context': context,
                'results': [{'success': r.success, 'error': r.error} for r in results],
                'output_length': len('\n'.join(output_lines))
            })
            
            # Learn from successful interactions
            if any(r.success for r in results):
                # This would normally include the intent and parameters used
                pass
            
            return output_lines
            
        except Exception as e:
            error_output = [f"❌ Processing error: {format_error_message(e)}"]
            
            # Record failed interaction
            await self.current_session.record_interaction({
                'type': 'error',
                'input': user_input,
                'error': str(e)
            })
            
            return error_output
    
    async def _get_recent_files(self, limit: int = 5) -> List[str]:
        """Get recently modified files in current directory."""
        try:
            current_dir = Path(os.getcwd())
            files = []
            
            for file_path in current_dir.rglob('*'):
                if file_path.is_file() and not self._should_ignore_file(file_path):
                    try:
                        files.append((str(file_path), file_path.stat().st_mtime))
                    except:
                        continue
            
            # Sort by modification time and return most recent
            files.sort(key=lambda x: x[1], reverse=True)
            return [f[0] for f in files[:limit]]
            
        except Exception:
            return []
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        ignore_patterns = {
            '.git', '__pycache__', 'node_modules', '.pytest_cache',
            'venv', 'env', '.vscode', '.idea', 'dist', 'build'
        }
        
        path_str = str(file_path).lower()
        for pattern in ignore_patterns:
            if pattern in path_str:
                return True
        
        return False
    
    def _format_dict_output(self, data: Dict[str, Any]) -> str:
        """Format dictionary data for user-friendly output."""
        lines = []
        for key, value in data.items():
            if isinstance(value, (list, tuple)) and len(value) > 0:
                lines.append(f"{key}: {', '.join(map(str, value[:3]))}")
                if len(value) > 3:
                    lines.append(f"  ... and {len(value) - 3} more")
            elif isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in list(value.items())[:3]:
                    lines.append(f"  {sub_key}: {sub_value}")
            else:
                lines.append(f"{key}: {value}")
        return '\n'.join(lines)
    
    async def get_suggestions(self, partial_input: str) -> List[str]:
        """Get intelligent suggestions for partial input."""
        # This would use the intent classifier to provide suggestions
        suggestions = [
            "explain this code",
            "review this file for bugs",
            "generate a function that...",
            "refactor this code to be cleaner",
            "debug this error",
            "create tests for this code",
            "document this function"
        ]
        
        # Filter suggestions based on partial input
        if partial_input:
            suggestions = [s for s in suggestions if partial_input.lower() in s.lower()]
        
        return suggestions[:5]
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        if not self.router:
            return {'status': 'not_initialized'}
        
        return await self.router.health_check()
    
    async def debug_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Debug how a request would be processed."""
        if not self.router:
            return {'error': 'Router not initialized'}
        
        if context is None:
            context = {
                'current_directory': os.getcwd(),
                'recent_files': await self._get_recent_files()
            }
        
        return await self.router.debug_routing(user_input, context)
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.current_session:
            await self.session_manager.end_session()


# CLI Command Integration
@click.command()
@click.argument('request', required=False)
@click.option('--debug', is_flag=True, help='Show debug information about request processing')
@click.option('--health', is_flag=True, help='Show system health status')
@click.option('--interactive', '-i', is_flag=True, help='Start interactive mode')
@click.pass_context
def smart(ctx, request: Optional[str], debug: bool, health: bool, interactive: bool):
    """Intelligent assistant that processes natural language requests like Claude CLI."""
    
    async def run_smart_cli():
        config = ctx.obj['config']
        verbose = ctx.obj.get('verbose', False)
        
        # Initialize intelligent CLI
        intelligent_cli = IntelligentCLI(config)
        
        try:
            # Health check mode
            if health:
                health_status = await intelligent_cli.get_health_status()
                click.echo("🏥 System Health Status:")
                click.echo(f"  Router: {health_status.get('router_status', 'unknown')}")
                click.echo(f"  Tools: {len(health_status.get('tool_registry', {}).get('registered_tools', []))} registered")
                click.echo(f"  Memory: {health_status.get('tool_registry', {}).get('memory_usage_mb', 0):.2f} MB")
                return
            
            # Debug mode
            if debug and request:
                debug_info = await intelligent_cli.debug_request(request)
                click.echo("🔍 Debug Information:")
                click.echo(f"  Input: {debug_info.get('user_input', '')}")
                click.echo(f"  Intent: {debug_info.get('intent', {}).get('type', 'unknown')} "
                          f"(confidence: {debug_info.get('intent', {}).get('confidence', 0):.2f})")
                click.echo(f"  Available tools: {len(debug_info.get('available_tools', []))}")
                
                if 'execution_plan' in debug_info:
                    plan = debug_info['execution_plan']
                    click.echo(f"  Execution plan: {plan.get('total_steps', 0)} steps")
                
                return
            
            # Interactive mode
            if interactive:
                click.echo("🤖 Interactive Intelligent Assistant")
                click.echo("Type your requests in natural language. Type 'exit' to quit.\n")
                
                await intelligent_cli.initialize_session()
                
                while True:
                    try:
                        user_input = click.prompt("You", type=str)
                        
                        if user_input.lower() in ['exit', 'quit', 'bye']:
                            click.echo("👋 Goodbye!")
                            break
                        
                        if not user_input.strip():
                            continue
                        
                        # Show processing indicator
                        click.echo("🤔 Processing...", err=True)
                        
                        # Process request
                        results = await intelligent_cli.process_request(user_input)
                        
                        # Show results
                        click.echo("\n🤖 Assistant:")
                        for line in results:
                            click.echo(f"  {line}")
                        click.echo()
                        
                    except KeyboardInterrupt:
                        click.echo("\n👋 Goodbye!")
                        break
                    except Exception as e:
                        click.echo(f"❌ Error: {format_error_message(e)}", err=True)
                        if verbose:
                            import traceback
                            click.echo(f"Traceback: {traceback.format_exc()}", err=True)
                
                return
            
            # Single request mode
            if request:
                await intelligent_cli.initialize_session()
                results = await intelligent_cli.process_request(request)
                
                for line in results:
                    click.echo(line)
            else:
                click.echo("❌ No request provided. Use --interactive for interactive mode or provide a request.")
                click.echo("Example: olla-cli smart 'explain this Python file: main.py'")
                sys.exit(1)
        
        finally:
            await intelligent_cli.cleanup()
    
    # Run async function
    try:
        asyncio.run(run_smart_cli())
    except KeyboardInterrupt:
        click.echo("\n⏹️ Operation cancelled.", err=True)
    except Exception as e:
        click.echo(f"❌ Error: {format_error_message(e)}", err=True)
        if ctx.obj.get('verbose'):
            import traceback
            click.echo(f"Traceback: {traceback.format_exc()}", err=True)
        sys.exit(1)


@click.command()
@click.argument('request')
@click.pass_context
def ask(ctx, request: str):
    """Quick intelligent assistant for single requests (shorthand for smart)."""
    # Reuse the smart command logic
    ctx.invoke(smart, request=request, debug=False, health=False, interactive=False)