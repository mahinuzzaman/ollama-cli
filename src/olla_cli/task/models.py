"""Core task management data models."""

import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Union, Set
from dataclasses import dataclass, field, asdict
from enum import Enum


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TaskType(Enum):
    """Types of tasks."""
    ADD_FEATURE = "add_feature"
    FIX_BUG = "fix_bug"
    REFACTOR = "refactor"
    OPTIMIZE = "optimize"
    ADD_TESTS = "add_tests"
    UPDATE_DOCS = "update_docs"
    CREATE_FILE = "create_file"
    ANALYZE = "analyze"
    CUSTOM = "custom"


class StepStatus(Enum):
    """Step execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActionType(Enum):
    """Types of actions that can be performed."""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    CREATE_FILE = "create_file"
    DELETE_FILE = "delete_file"
    ANALYZE_CODE = "analyze_code"
    GENERATE_CODE = "generate_code"
    RUN_COMMAND = "run_command"
    SEARCH_FILES = "search_files"
    VALIDATE = "validate"


@dataclass
class FileChange:
    """Represents a change to be made to a file."""
    file_path: Path
    action: ActionType
    content: Optional[str] = None
    old_content: Optional[str] = None
    line_range: Optional[tuple] = None
    description: str = ""
    backup_path: Optional[Path] = None


@dataclass
class TaskContext:
    """Context information for task execution."""
    working_directory: Path
    project_root: Optional[Path] = None
    language: Optional[str] = None
    framework: Optional[str] = None
    discovered_files: List[Path] = field(default_factory=list)
    related_files: List[Path] = field(default_factory=list)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    project_structure: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)


@dataclass
class TaskStep:
    """Represents a single step in a task."""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    action: ActionType = ActionType.ANALYZE_CODE
    status: StepStatus = StepStatus.PENDING
    files_to_read: List[Path] = field(default_factory=list)
    files_to_modify: List[Path] = field(default_factory=list)
    changes: List[FileChange] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Step IDs
    estimated_duration: Optional[int] = None  # seconds
    actual_duration: Optional[int] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error_message: Optional[str] = None
    ai_prompt: Optional[str] = None
    ai_response: Optional[str] = None
    validation_results: Dict[str, Any] = field(default_factory=dict)
    
    def start(self):
        """Mark step as started."""
        self.status = StepStatus.IN_PROGRESS
        self.started_at = time.time()
    
    def complete(self):
        """Mark step as completed."""
        self.status = StepStatus.COMPLETED
        self.completed_at = time.time()
        if self.started_at:
            self.actual_duration = int(self.completed_at - self.started_at)
    
    def fail(self, error_message: str):
        """Mark step as failed."""
        self.status = StepStatus.FAILED
        self.error_message = error_message
        self.completed_at = time.time()
        if self.started_at:
            self.actual_duration = int(self.completed_at - self.started_at)
    
    def skip(self, reason: str):
        """Mark step as skipped."""
        self.status = StepStatus.SKIPPED
        self.error_message = reason
    
    def get_duration(self) -> Optional[int]:
        """Get step duration in seconds."""
        if self.actual_duration:
            return self.actual_duration
        elif self.started_at and self.status == StepStatus.IN_PROGRESS:
            return int(time.time() - self.started_at)
        return None


@dataclass
class TaskResult:
    """Results of task execution."""
    success: bool = False
    files_modified: List[Path] = field(default_factory=list)
    files_created: List[Path] = field(default_factory=list)
    backup_files: List[Path] = field(default_factory=list)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class Task:
    """Represents a complete task to be executed."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    task_type: TaskType = TaskType.CUSTOM
    status: TaskStatus = TaskStatus.PENDING
    priority: str = "medium"  # low, medium, high
    
    # Steps and execution
    steps: List[TaskStep] = field(default_factory=list)
    current_step_index: int = 0
    
    # Context and metadata
    context: Optional[TaskContext] = None
    template_used: Optional[str] = None
    
    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    
    # Results and state
    result: Optional[TaskResult] = None
    user_confirmations: Dict[str, bool] = field(default_factory=dict)
    interrupt_point: Optional[Dict[str, Any]] = None  # For resuming
    
    # Metadata
    tags: Set[str] = field(default_factory=set)
    notes: str = ""
    model_used: str = "codellama"
    temperature: float = 0.7
    
    def add_step(self, step: TaskStep) -> None:
        """Add a step to the task."""
        self.steps.append(step)
    
    def get_current_step(self) -> Optional[TaskStep]:
        """Get the current step being executed."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
    
    def get_next_step(self) -> Optional[TaskStep]:
        """Get the next pending step."""
        for i, step in enumerate(self.steps[self.current_step_index:], self.current_step_index):
            if step.status == StepStatus.PENDING:
                return step
        return None
    
    def advance_step(self) -> bool:
        """Move to next step. Returns True if there are more steps."""
        self.current_step_index += 1
        return self.current_step_index < len(self.steps)
    
    def start(self):
        """Mark task as started."""
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = time.time()
    
    def complete(self, result: TaskResult):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.completed_at = time.time()
        if self.started_at:
            self.actual_duration = int(self.completed_at - self.started_at)
    
    def fail(self, error_message: str):
        """Mark task as failed."""
        self.status = TaskStatus.FAILED
        if not self.result:
            self.result = TaskResult()
        self.result.errors.append(error_message)
        self.completed_at = time.time()
        if self.started_at:
            self.actual_duration = int(self.completed_at - self.started_at)
    
    def pause(self, interrupt_point: Dict[str, Any]):
        """Pause task execution."""
        self.status = TaskStatus.PAUSED
        self.interrupt_point = interrupt_point
    
    def resume(self):
        """Resume task execution."""
        if self.status == TaskStatus.PAUSED:
            self.status = TaskStatus.IN_PROGRESS
            self.interrupt_point = None
    
    def get_progress(self) -> tuple:
        """Get task progress as (completed_steps, total_steps, percentage)."""
        completed = sum(1 for step in self.steps 
                       if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED])
        total = len(self.steps)
        percentage = (completed / total * 100) if total > 0 else 0
        return completed, total, percentage
    
    def get_duration(self) -> Optional[int]:
        """Get task duration in seconds."""
        if self.actual_duration:
            return self.actual_duration
        elif self.started_at and self.status == TaskStatus.IN_PROGRESS:
            return int(time.time() - self.started_at)
        return None
    
    def get_files_to_modify(self) -> Set[Path]:
        """Get all files that will be modified by this task."""
        files = set()
        for step in self.steps:
            files.update(step.files_to_modify)
            for change in step.changes:
                files.add(change.file_path)
        return files
    
    def get_files_to_read(self) -> Set[Path]:
        """Get all files that will be read by this task."""
        files = set()
        for step in self.steps:
            files.update(step.files_to_read)
        return files
    
    def has_pending_steps(self) -> bool:
        """Check if there are any pending steps."""
        return any(step.status == StepStatus.PENDING for step in self.steps)
    
    def can_resume(self) -> bool:
        """Check if task can be resumed."""
        return (self.status == TaskStatus.PAUSED and 
                self.interrupt_point is not None and
                self.has_pending_steps())
    
    def __str__(self) -> str:
        """String representation of task."""
        progress = self.get_progress()
        duration = self.get_duration()
        duration_str = f" ({duration}s)" if duration else ""
        
        return (f"Task({self.task_id[:8]}): {self.title} "
                f"[{self.status.value}] {progress[2]:.1f}%{duration_str}")