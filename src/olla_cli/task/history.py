"""Task history and persistence management."""

import json
import time
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import asdict
import logging
from datetime import datetime, timezone

from .models import Task, TaskStatus, TaskType, TaskResult
from ..config import Config

logger = logging.getLogger('olla-cli')


class TaskHistoryManager:
    """Manages task history and persistence using SQLite database."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        
        # Setup data directory
        self.data_dir = Path.home() / ".olla-cli" / "tasks"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "task_history.db"
        
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Main tasks table
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT NOT NULL,
                        task_type TEXT NOT NULL,
                        status TEXT NOT NULL,
                        priority TEXT DEFAULT 'medium',
                        created_at REAL NOT NULL,
                        started_at REAL,
                        completed_at REAL,
                        actual_duration INTEGER,
                        model_used TEXT DEFAULT 'codellama',
                        temperature REAL DEFAULT 0.7,
                        tags TEXT,  -- JSON array
                        notes TEXT DEFAULT '',
                        context_data TEXT,  -- JSON serialized context
                        interrupt_point TEXT,  -- JSON for resumption
                        user_confirmations TEXT,  -- JSON object
                        steps_data TEXT,  -- JSON serialized steps
                        result_data TEXT  -- JSON serialized result
                    )
                ''')
                
                # Create indexes
                conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks (created_at)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)')
                conn.execute('CREATE INDEX IF NOT EXISTS idx_tasks_type ON tasks (task_type)')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to initialize task history database: {e}")
            raise
    
    def save_task(self, task: Task) -> bool:
        """Save a task to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                task_dict = task.to_dict() if hasattr(task, 'to_dict') else asdict(task)
                
                # Prepare data for storage
                task_data = {
                    'id': task.task_id,
                    'title': task.title,
                    'description': task.description,
                    'task_type': task.task_type.value,
                    'status': task.status.value,
                    'priority': task.priority,
                    'created_at': task.created_at,
                    'started_at': task.started_at,
                    'completed_at': task.completed_at,
                    'actual_duration': task.actual_duration,
                    'model_used': task.model_used,
                    'temperature': task.temperature,
                    'tags': json.dumps(list(task.tags)) if task.tags else '[]',
                    'notes': task.notes,
                    'context_data': json.dumps(asdict(task.context)) if task.context else None,
                    'interrupt_point': json.dumps(task.interrupt_point) if task.interrupt_point else None,
                    'user_confirmations': json.dumps(task.user_confirmations) if task.user_confirmations else '{}',
                    'steps_data': json.dumps([asdict(step) for step in task.steps]),
                    'result_data': json.dumps(asdict(task.result)) if task.result else None
                }
                
                # Convert Path objects to strings in JSON data
                if task_data['context_data']:
                    context = json.loads(task_data['context_data'])
                    if context.get('working_directory'):
                        context['working_directory'] = str(context['working_directory'])
                    if context.get('project_root'):
                        context['project_root'] = str(context['project_root'])
                    if context.get('discovered_files'):
                        context['discovered_files'] = [str(p) for p in context['discovered_files']]
                    if context.get('related_files'):
                        context['related_files'] = [str(p) for p in context['related_files']]
                    task_data['context_data'] = json.dumps(context)
                
                if task_data['steps_data']:
                    steps = json.loads(task_data['steps_data'])
                    for step in steps:
                        step['files_to_read'] = [str(p) for p in step.get('files_to_read', [])]
                        step['files_to_modify'] = [str(p) for p in step.get('files_to_modify', [])]
                        for change in step.get('changes', []):
                            if change.get('file_path'):
                                change['file_path'] = str(change['file_path'])
                            if change.get('backup_path'):
                                change['backup_path'] = str(change['backup_path'])
                    task_data['steps_data'] = json.dumps(steps)
                
                if task_data['result_data']:
                    result = json.loads(task_data['result_data'])
                    result['files_modified'] = [str(p) for p in result.get('files_modified', [])]
                    result['files_created'] = [str(p) for p in result.get('files_created', [])]
                    result['backup_files'] = [str(p) for p in result.get('backup_files', [])]
                    task_data['result_data'] = json.dumps(result)
                
                # Insert or update task
                conn.execute('''
                    INSERT OR REPLACE INTO tasks 
                    (id, title, description, task_type, status, priority, created_at, 
                     started_at, completed_at, actual_duration, model_used, temperature, 
                     tags, notes, context_data, interrupt_point, user_confirmations,
                     steps_data, result_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    task_data['id'], task_data['title'], task_data['description'],
                    task_data['task_type'], task_data['status'], task_data['priority'],
                    task_data['created_at'], task_data['started_at'], task_data['completed_at'],
                    task_data['actual_duration'], task_data['model_used'], task_data['temperature'],
                    task_data['tags'], task_data['notes'], task_data['context_data'],
                    task_data['interrupt_point'], task_data['user_confirmations'],
                    task_data['steps_data'], task_data['result_data']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save task {task.task_id}: {e}")
            return False
    
    def load_task(self, task_id: str) -> Optional[Task]:
        """Load a task from the database by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                cursor = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                # Reconstruct task from stored data
                from .models import TaskContext, TaskStep, TaskResult, StepStatus, ActionType, FileChange
                
                task_data = dict(row)
                
                # Parse JSON fields
                task_data['tags'] = set(json.loads(task_data['tags'] or '[]'))
                task_data['user_confirmations'] = json.loads(task_data['user_confirmations'] or '{}')
                task_data['interrupt_point'] = json.loads(task_data['interrupt_point']) if task_data['interrupt_point'] else None
                
                # Reconstruct context
                if task_data['context_data']:
                    context_dict = json.loads(task_data['context_data'])
                    if context_dict.get('working_directory'):
                        context_dict['working_directory'] = Path(context_dict['working_directory'])
                    if context_dict.get('project_root'):
                        context_dict['project_root'] = Path(context_dict['project_root'])
                    if context_dict.get('discovered_files'):
                        context_dict['discovered_files'] = [Path(p) for p in context_dict['discovered_files']]
                    if context_dict.get('related_files'):
                        context_dict['related_files'] = [Path(p) for p in context_dict['related_files']]
                    task_data['context'] = TaskContext(**context_dict)
                else:
                    task_data['context'] = None
                
                # Reconstruct steps
                if task_data['steps_data']:
                    steps_list = json.loads(task_data['steps_data'])
                    steps = []
                    for step_dict in steps_list:
                        step_dict['status'] = StepStatus(step_dict['status'])
                        step_dict['action'] = ActionType(step_dict['action'])
                        step_dict['files_to_read'] = [Path(p) for p in step_dict.get('files_to_read', [])]
                        step_dict['files_to_modify'] = [Path(p) for p in step_dict.get('files_to_modify', [])]
                        
                        # Reconstruct changes
                        changes = []
                        for change_dict in step_dict.get('changes', []):
                            change_dict['file_path'] = Path(change_dict['file_path'])
                            change_dict['action'] = ActionType(change_dict['action'])
                            if change_dict.get('backup_path'):
                                change_dict['backup_path'] = Path(change_dict['backup_path'])
                            changes.append(FileChange(**change_dict))
                        step_dict['changes'] = changes
                        
                        steps.append(TaskStep(**step_dict))
                    task_data['steps'] = steps
                else:
                    task_data['steps'] = []
                
                # Reconstruct result
                if task_data['result_data']:
                    result_dict = json.loads(task_data['result_data'])
                    result_dict['files_modified'] = [Path(p) for p in result_dict.get('files_modified', [])]
                    result_dict['files_created'] = [Path(p) for p in result_dict.get('files_created', [])]
                    result_dict['backup_files'] = [Path(p) for p in result_dict.get('backup_files', [])]
                    task_data['result'] = TaskResult(**result_dict)
                else:
                    task_data['result'] = None
                
                # Convert enums
                task_data['status'] = TaskStatus(task_data['status'])
                task_data['task_type'] = TaskType(task_data['task_type'])
                
                # Clean up database-specific fields
                task_data['task_id'] = task_data['id']
                del task_data['id']
                del task_data['context_data']
                del task_data['steps_data']
                del task_data['result_data']
                
                return Task(**task_data)
                
        except Exception as e:
            logger.error(f"Failed to load task {task_id}: {e}")
            return None
    
    def list_tasks(self, limit: int = 50, status: Optional[TaskStatus] = None,
                   task_type: Optional[TaskType] = None, 
                   days_back: Optional[int] = None) -> List[Dict[str, Any]]:
        """List recent tasks with optional filtering."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM tasks"
                params = []
                conditions = []
                
                if status:
                    conditions.append("status = ?")
                    params.append(status.value)
                
                if task_type:
                    conditions.append("task_type = ?")
                    params.append(task_type.value)
                
                if days_back:
                    cutoff_time = time.time() - (days_back * 24 * 60 * 60)
                    conditions.append("created_at >= ?")
                    params.append(cutoff_time)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)
                
                cursor = conn.execute(query, params)
                
                tasks = []
                for row in cursor.fetchall():
                    task_dict = dict(row)
                    task_dict['created_at'] = datetime.fromtimestamp(task_dict['created_at'], tz=timezone.utc)
                    if task_dict['started_at']:
                        task_dict['started_at'] = datetime.fromtimestamp(task_dict['started_at'], tz=timezone.utc)
                    if task_dict['completed_at']:
                        task_dict['completed_at'] = datetime.fromtimestamp(task_dict['completed_at'], tz=timezone.utc)
                    
                    task_dict['tags'] = json.loads(task_dict['tags'] or '[]')
                    tasks.append(task_dict)
                
                return tasks
                
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get task execution statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                stats = {}
                
                # Total tasks
                cursor = conn.execute("SELECT COUNT(*) as total FROM tasks")
                stats['total_tasks'] = cursor.fetchone()['total']
                
                # Tasks by status
                cursor = conn.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status")
                stats['by_status'] = dict(cursor.fetchall())
                
                # Tasks by type
                cursor = conn.execute("SELECT task_type, COUNT(*) as count FROM tasks GROUP BY task_type")
                stats['by_type'] = dict(cursor.fetchall())
                
                # Recent activity
                recent_cutoff = time.time() - (7 * 24 * 60 * 60)
                cursor = conn.execute("SELECT COUNT(*) as recent FROM tasks WHERE created_at >= ?", (recent_cutoff,))
                stats['recent_tasks'] = cursor.fetchone()['recent']
                
                # Average duration
                cursor = conn.execute("SELECT AVG(actual_duration) as avg_duration FROM tasks WHERE actual_duration IS NOT NULL")
                avg_duration = cursor.fetchone()['avg_duration']
                stats['average_duration'] = int(avg_duration) if avg_duration else 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get task statistics: {e}")
            return {}
    
    def search_tasks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search tasks by title, description, or notes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                search_query = f"%{query}%"
                cursor = conn.execute('''
                    SELECT * FROM tasks 
                    WHERE title LIKE ? OR description LIKE ? OR notes LIKE ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (search_query, search_query, search_query, limit))
                
                tasks = []
                for row in cursor.fetchall():
                    task_dict = dict(row)
                    task_dict['created_at'] = datetime.fromtimestamp(task_dict['created_at'], tz=timezone.utc)
                    if task_dict['started_at']:
                        task_dict['started_at'] = datetime.fromtimestamp(task_dict['started_at'], tz=timezone.utc)
                    if task_dict['completed_at']:
                        task_dict['completed_at'] = datetime.fromtimestamp(task_dict['completed_at'], tz=timezone.utc)
                    
                    task_dict['tags'] = json.loads(task_dict['tags'] or '[]')
                    tasks.append(task_dict)
                
                return tasks
                
        except Exception as e:
            logger.error(f"Failed to search tasks: {e}")
            return []