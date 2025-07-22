"""CLI command modules for olla-cli."""

from .main import main
cli = main  # Entry point alias
from .config_commands import config
from .model_commands import models  
from .code_commands import explain, review, refactor, debug, generate, test, document
from .task_commands import task, resume, tasks

__all__ = [
    'main', 'cli',
    'config',
    'models',
    'explain', 'review', 'refactor', 'debug', 'generate', 'test', 'document',
    'task', 'resume', 'tasks'
]