"""Task management system for olla-cli.

Simple, organized task management with:
- Natural language task parsing
- File discovery and execution
- Progress tracking and history
- Task resumption
"""

from .models import (
    Task, TaskStep, TaskResult, TaskStatus, TaskType, 
    StepStatus, ActionType, TaskContext, FileChange
)
from .parser import TaskParser
from .discovery import FileDiscoveryEngine
from .executor import TaskExecutor, TaskExecutionError
from .history import TaskHistoryManager

__all__ = [
    # Core models
    'Task', 'TaskStep', 'TaskResult', 'TaskStatus', 'TaskType',
    'StepStatus', 'ActionType', 'TaskContext', 'FileChange',
    
    # Main components  
    'TaskParser', 'FileDiscoveryEngine', 'TaskExecutor', 'TaskExecutionError',
    'TaskHistoryManager',
]