"""Olla CLI - A coding assistant command line tool.

A comprehensive CLI tool for code analysis, generation, and task management
using local language models through Ollama.
"""

__version__ = "0.3.0"
__author__ = "Olla CLI Team"
__description__ = "A coding assistant command line tool using Ollama"

# Core functionality exports
from .core import (
    OllamaConnectionError, ModelNotFoundError, ContextLimitExceededError,
    StreamingError, OllamaServerError
)

from .client import OllamaClient, ModelManager
from .config import Config, setup_logging
from .ui import OutputFormatter, FormatterFactory
from .utils import format_error_message, MessageBuilder, ResponseFormatter

# Task system exports
from .task import (
    Task, TaskStep, TaskResult, TaskStatus, TaskType,
    StepStatus, ActionType, TaskContext, FileChange,
    TaskParser, TaskExecutor, TaskHistoryManager
)

__all__ = [
    # Version info
    '__version__',
    '__author__', 
    '__description__',
    
    # Core exceptions
    'OllamaConnectionError',
    'ModelNotFoundError', 
    'ContextLimitExceededError',
    'StreamingError',
    'OllamaServerError',
    
    # Client and config
    'OllamaClient',
    'ModelManager',
    'Config',
    'setup_logging',
    
    # UI and formatting
    'OutputFormatter',
    'FormatterFactory',
    
    # Utilities
    'format_error_message',
    'MessageBuilder',
    'ResponseFormatter',
    
    # Task system
    'Task',
    'TaskStep', 
    'TaskResult',
    'TaskStatus',
    'TaskType',
    'StepStatus',
    'ActionType',
    'TaskContext',
    'FileChange',
    'TaskParser',
    'TaskExecutor',
    'TaskHistoryManager',
]