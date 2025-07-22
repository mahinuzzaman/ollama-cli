"""Task management commands."""

import click
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..task import TaskParser, TaskExecutor, TaskExecutionError, TaskType, TaskHistoryManager, TaskStatus
from ..client import OllamaClient, ModelManager
from ..context import ContextBuilder
from ..core import OllamaConnectionError, ModelNotFoundError
from ..utils import format_error_message


@click.command()
@click.argument('description')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.option('--auto-confirm', is_flag=True, help='Automatically confirm all steps')
@click.option('--context-path', type=click.Path(exists=True, file_okay=False, dir_okay=True),
              help='Specify working directory context')
@click.option('--output-file', '-o', help='Save task execution log to file')
@click.pass_context
def task(ctx, description: str, dry_run: bool, auto_confirm: bool, 
         context_path: Optional[str], output_file: Optional[str]):
    """Execute complex tasks with AI assistance and step-by-step progress."""
    config = ctx.obj['config']
    model = ctx.obj['model']
    temperature = ctx.obj['temperature']
    verbose = ctx.obj['verbose']
    logger = ctx.obj['logger']
    formatter = ctx.obj['formatter']
    
    try:
        # Initialize components
        api_url = config.get('api_url', 'http://localhost:11434')
        client = OllamaClient(host=api_url, timeout=60)
        model_manager = ModelManager(client)
        
        # Initialize context manager
        try:
            context_manager = ContextBuilder(Path(context_path) if context_path else None)
        except Exception as e:
            logger.warning(f"Could not initialize context manager: {e}")
            context_manager = None
        
        # Test connection and validate model
        _test_connection_and_model(client, model_manager, model, formatter, verbose)
        
        # Initialize task system
        task_parser = TaskParser(client, model_manager, context_manager)
        task_executor = TaskExecutor(client, model_manager, context_manager, formatter)
        
        formatter.print_header("🎯 Task Manager", f"Processing: {description}")
        
        # Parse and execute task
        parsed_task = _parse_and_validate_task(task_parser, description, context_path, formatter, verbose)
        result = task_executor.execute_task(parsed_task, dry_run=dry_run, auto_confirm=auto_confirm)
        
        # Show results and save log
        _handle_task_results(result, formatter, output_file, parsed_task)
        
    except KeyboardInterrupt:
        formatter.print_warning("🛑 Task interrupted by user")
    except Exception as e:
        _handle_task_error(e, logger, formatter, verbose)


@click.command()
@click.argument('task_id')
@click.option('--auto-confirm', is_flag=True, help='Automatically confirm all remaining steps')
@click.pass_context
def resume(ctx, task_id: str, auto_confirm: bool):
    """Resume a previously paused task."""
    config = ctx.obj['config']
    verbose = ctx.obj['verbose']
    logger = ctx.obj['logger']
    formatter = ctx.obj['formatter']
    
    try:
        # Initialize components
        api_url = config.get('api_url', 'http://localhost:11434')
        client = OllamaClient(host=api_url, timeout=60)
        model_manager = ModelManager(client)
        context_manager = ContextBuilder()
        
        # Test connection
        client.test_connection()
        
        # Initialize task executor
        task_executor = TaskExecutor(client, model_manager, context_manager, formatter)
        
        formatter.print_header("🔄 Task Resume", f"Resuming task: {task_id}")
        
        result = task_executor.resume_task(task_id, auto_confirm=auto_confirm)
        
        if result.success:
            formatter.print_success("✅ Task resumed and completed successfully!")
        else:
            formatter.print_error("❌ Task resume failed")
            for error in result.errors:
                formatter.console.print(f"  🔸 {error}")
    
    except TaskExecutionError as e:
        formatter.print_error("Task resume error", str(e))
        sys.exit(1)
    except Exception as e:
        _handle_task_error(e, logger, formatter, verbose)


@click.group()
@click.pass_context
def tasks(ctx):
    """Manage task history and execution."""
    pass


@tasks.command('list')
@click.option('--limit', '-n', type=int, default=20, help='Number of tasks to show')
@click.option('--status', type=click.Choice(['pending', 'in_progress', 'completed', 'failed', 'cancelled', 'paused']),
              help='Filter by task status')
@click.option('--type', 'task_type', type=click.Choice(['add_feature', 'fix_bug', 'refactor', 'optimize', 'add_tests', 'update_docs', 'create_file', 'analyze', 'custom']),
              help='Filter by task type')
@click.option('--days', type=int, help='Show tasks from last N days')
@click.pass_context
def tasks_list(ctx, limit: int, status: Optional[str], task_type: Optional[str], days: Optional[int]):
    """List recent tasks with optional filtering."""
    config = ctx.obj['config']
    formatter = ctx.obj['formatter']
    
    try:
        history_manager = TaskHistoryManager(config)
        
        # Convert string enums to objects
        status_filter = TaskStatus(status) if status else None
        type_filter = TaskType(task_type) if task_type else None
        
        tasks = history_manager.list_tasks(
            limit=limit,
            status=status_filter,
            task_type=type_filter,
            days_back=days
        )
        
        if not tasks:
            formatter.print_info("No tasks found matching the criteria.")
            return
        
        # Display tasks in a table
        _display_tasks_table(tasks, formatter)
        
        # Show resumable tasks if any
        resumable = [t for t in tasks if t['status'] == 'paused']
        if resumable:
            formatter.print_info(f"💡 {len(resumable)} task(s) can be resumed using 'olla-cli resume <task-id>'")
    
    except Exception as e:
        formatter.print_error("Failed to list tasks", format_error_message(e))
        sys.exit(1)


@tasks.command('show')
@click.argument('task_id')
@click.pass_context
def tasks_show(ctx, task_id: str):
    """Show detailed information about a specific task."""
    config = ctx.obj['config']
    formatter = ctx.obj['formatter']
    
    try:
        history_manager = TaskHistoryManager(config)
        task = history_manager.load_task(task_id)
        
        if not task:
            formatter.print_error(f"Task not found: {task_id}")
            sys.exit(1)
        
        _display_task_details(task, formatter)
    
    except Exception as e:
        formatter.print_error("Failed to show task details", format_error_message(e))
        sys.exit(1)


@tasks.command('stats')
@click.pass_context
def tasks_stats(ctx):
    """Show task execution statistics."""
    config = ctx.obj['config']
    formatter = ctx.obj['formatter']
    
    try:
        history_manager = TaskHistoryManager(config)
        stats = history_manager.get_task_statistics()
        
        if not stats:
            formatter.print_info("No task statistics available.")
            return
        
        _display_task_statistics(stats, formatter)
    
    except Exception as e:
        formatter.print_error("Failed to get task statistics", format_error_message(e))
        sys.exit(1)


@tasks.command('search')
@click.argument('query')
@click.option('--limit', '-n', type=int, default=10, help='Number of results to show')
@click.pass_context
def tasks_search(ctx, query: str, limit: int):
    """Search tasks by title, description, or notes."""
    config = ctx.obj['config']
    formatter = ctx.obj['formatter']
    
    try:
        history_manager = TaskHistoryManager(config)
        tasks = history_manager.search_tasks(query, limit)
        
        if not tasks:
            formatter.print_info(f"No tasks found matching '{query}'.")
            return
        
        _display_search_results(tasks, query, formatter)
    
    except Exception as e:
        formatter.print_error("Failed to search tasks", format_error_message(e))
        sys.exit(1)


# Helper functions
def _test_connection_and_model(client, model_manager, model, formatter, verbose):
    """Test connection and validate model."""
    if verbose:
        formatter.print_info("Testing connection to Ollama...")
    
    try:
        client.test_connection()
    except OllamaConnectionError as e:
        formatter.print_error("Cannot connect to Ollama server", str(e))
        formatter.print_info("Please ensure Ollama is running and accessible.")
        sys.exit(1)
    
    try:
        model_info = model_manager.validate_model(model)
        if verbose:
            formatter.print_success(f"Using model: {model} (context: {model_info.context_length})")
    except ModelNotFoundError:
        formatter.print_error(f"Model '{model}' not found")
        formatter.print_info("Use 'olla-cli models list' to see available models")
        sys.exit(1)


def _parse_and_validate_task(task_parser, description, context_path, formatter, verbose):
    """Parse and validate task description."""
    formatter.print_info("📋 Parsing task description...")
    try:
        parsed_task = task_parser.parse_task_description(
            description, 
            Path(context_path) if context_path else None
        )
    except Exception as e:
        formatter.print_error("Failed to parse task description", str(e))
        if verbose:
            import traceback
            formatter.print_info(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
    
    # Validate the parsed task
    warnings = task_parser.validate_task(parsed_task)
    if warnings:
        formatter.print_warning("Task validation warnings:")
        for warning in warnings:
            formatter.console.print(f"  ⚠️ {warning}")
    
    # Show suggestions for improvement
    suggestions = task_parser.suggest_improvements(parsed_task)
    if suggestions:
        formatter.print_info("💡 Suggestions:")
        for suggestion in suggestions:
            formatter.console.print(f"  💡 {suggestion}")
    
    return parsed_task


def _handle_task_results(result, formatter, output_file, task):
    """Handle task execution results."""
    if result.success:
        formatter.print_success("✅ Task completed successfully!")
    else:
        formatter.print_error("❌ Task execution failed")
        for error in result.errors:
            formatter.console.print(f"  🔸 {error}")
    
    # Save execution log if requested
    if output_file:
        try:
            log_content = _generate_task_log(task, result)
            with open(output_file, 'w') as f:
                f.write(log_content)
            formatter.print_success(f"💾 Task log saved to: {output_file}")
        except Exception as e:
            formatter.print_warning(f"Could not save log file: {e}")


def _handle_task_error(error, logger, formatter, verbose):
    """Handle task execution errors."""
    logger.error(f"Error in task command: {error}")
    formatter.print_error("Task command failed", format_error_message(error))
    if verbose:
        import traceback
        formatter.print_info(f"Traceback: {traceback.format_exc()}")
    sys.exit(1)


def _display_tasks_table(tasks, formatter):
    """Display tasks in table format."""
    table_data = []
    for task in tasks:
        table_data.append({
            "ID": task['id'][:8],
            "Title": task['title'][:50] + "..." if len(task['title']) > 50 else task['title'],
            "Type": task['task_type'].replace('_', ' ').title(),
            "Status": task['status'].title(),
            "Created": task['created_at'].strftime("%m/%d %H:%M") if hasattr(task['created_at'], 'strftime') else str(task['created_at'])[:16],
            "Duration": f"{task['actual_duration']}s" if task.get('actual_duration') else "N/A"
        })
    
    formatter.print_table(table_data, f"📋 Recent Tasks ({len(tasks)} found)")


def _display_task_details(task, formatter):
    """Display detailed task information."""
    formatter.print_header(f"Task Details: {task.title}", task.task_id)
    
    details = [
        {"Property": "ID", "Value": task.task_id},
        {"Property": "Type", "Value": task.task_type.value.title()},
        {"Property": "Status", "Value": task.status.value.title()},
        {"Property": "Priority", "Value": task.priority.title()},
        {"Property": "Created", "Value": datetime.fromtimestamp(task.created_at).strftime("%Y-%m-%d %H:%M:%S")},
    ]
    
    if task.started_at:
        details.append({"Property": "Started", "Value": datetime.fromtimestamp(task.started_at).strftime("%Y-%m-%d %H:%M:%S")})
    
    if task.completed_at:
        details.append({"Property": "Completed", "Value": datetime.fromtimestamp(task.completed_at).strftime("%Y-%m-%d %H:%M:%S")})
    
    if task.get_duration():
        details.append({"Property": "Duration", "Value": f"{task.get_duration()} seconds"})
    
    formatter.print_table(details, "Task Information")
    
    # Show description and progress
    formatter.print_info("Description:")
    formatter.console.print(f"  {task.description}")
    
    completed, total, percentage = task.get_progress()
    formatter.print_info(f"Progress: {completed}/{total} steps ({percentage:.1f}%)")
    
    # Show resume option if paused
    if task.can_resume():
        formatter.print_info(f"💡 This task can be resumed using: olla-cli resume {task.task_id}")


def _display_task_statistics(stats, formatter):
    """Display task statistics."""
    formatter.print_header("📊 Task Statistics")
    
    overview_data = [
        {"Metric": "Total Tasks", "Value": str(stats.get('total_tasks', 0))},
        {"Metric": "Recent Tasks (7 days)", "Value": str(stats.get('recent_tasks', 0))},
        {"Metric": "Average Duration", "Value": f"{stats.get('average_duration', 0)} seconds"},
    ]
    formatter.print_table(overview_data, "Overview")


def _display_search_results(tasks, query, formatter):
    """Display search results."""
    table_data = []
    for task in tasks:
        table_data.append({
            "ID": task['id'][:8],
            "Title": task['title'][:50] + "..." if len(task['title']) > 50 else task['title'],
            "Type": task['task_type'].replace('_', ' ').title(),
            "Status": task['status'].title(),
            "Created": task['created_at'].strftime("%m/%d %H:%M") if hasattr(task['created_at'], 'strftime') else str(task['created_at'])[:16]
        })
    
    formatter.print_table(table_data, f"🔍 Search Results for '{query}' ({len(tasks)} found)")


def _generate_task_log(task, result):
    """Generate task execution log."""
    log_lines = [
        "# Task Execution Log",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"## Task Details",
        f"- **ID**: {task.task_id}",
        f"- **Title**: {task.title}",
        f"- **Description**: {task.description}",
        "",
        f"## Results",
        f"- **Success**: {'Yes' if result.success else 'No'}",
        f"- **Files Modified**: {len(result.files_modified)}",
        f"- **Files Created**: {len(result.files_created)}",
        ""
    ]
    
    if result.summary:
        log_lines.extend([
            f"## Summary",
            result.summary
        ])
    
    return "\n".join(log_lines)