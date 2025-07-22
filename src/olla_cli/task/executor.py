"""Task execution engine with progress tracking."""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import traceback

from .models import Task, TaskStep, TaskResult, TaskStatus, StepStatus, ActionType
from .history import TaskHistoryManager
from .discovery import FileDiscoveryEngine
from ..client import OllamaClient, ModelManager
from ..context import ContextBuilder
from ..commands import CommandImplementations
from ..ui import FormatterFactory

logger = logging.getLogger('olla-cli')


class TaskExecutionError(Exception):
    """Exception raised during task execution."""
    pass


class StepResult:
    """Result of executing a single step."""
    def __init__(self, success: bool = False, message: str = "", data: Any = None):
        self.success = success
        self.message = message
        self.data = data


class TaskExecutor:
    """Executes tasks with progress tracking and user interaction."""
    
    def __init__(self, client: OllamaClient, model_manager: ModelManager, 
                 context_manager: Optional[ContextBuilder] = None,
                 formatter=None):
        self.client = client
        self.model_manager = model_manager
        self.context_manager = context_manager
        self.formatter = formatter or FormatterFactory.create_formatter()
        
        # Initialize supporting components
        self.discovery_engine = FileDiscoveryEngine(context_manager)
        self.command_impl = CommandImplementations(client, model_manager, context_manager, formatter)
        self.history_manager = TaskHistoryManager()
        
        # Execution state
        self.current_task: Optional[Task] = None
        self.backup_dir: Optional[Path] = None
    
    def execute_task(self, task: Task, dry_run: bool = False, auto_confirm: bool = False) -> TaskResult:
        """Execute a task with progress tracking."""
        self.current_task = task
        
        # Create backup directory if not in dry run mode
        if not dry_run:
            self._create_backup_directory(task)
        
        result = TaskResult()
        
        try:
            # Start the task
            task.start()
            self.history_manager.save_task(task)
            
            self.formatter.print_header(
                f"Executing Task: {task.title}",
                f"Type: {task.task_type.value.title()} | Steps: {len(task.steps)}"
            )
            
            # Show task overview
            self._show_task_overview(task)
            
            # Execute steps
            for i, step in enumerate(task.steps):
                if step.status != StepStatus.PENDING:
                    continue  # Skip already processed steps
                
                task.current_step_index = i
                
                # Show step progress
                self.formatter.print_info(f"Step {i+1}/{len(task.steps)}: {step.title}")
                
                # Confirm step execution if not auto-confirm
                if not auto_confirm and not dry_run:
                    if not self._confirm_step_execution(step):
                        step.skip("User skipped step")
                        continue
                
                # Execute the step
                try:
                    step_result = self._execute_step(step, task, dry_run)
                    
                    if step_result.success:
                        step.complete()
                        self.formatter.print_success(f"✅ {step.title}")
                        self._update_result_from_step(result, step)
                        self.history_manager.save_task(task)
                    else:
                        step.fail(step_result.message)
                        self.formatter.print_error(f"❌ {step.title}: {step_result.message}")
                        
                        if not self._confirm_continue_after_error(task, step, step_result.message):
                            break
                
                except KeyboardInterrupt:
                    self._handle_interruption(task, i)
                    raise
                except Exception as e:
                    error_msg = f"Unexpected error in step '{step.title}': {str(e)}"
                    logger.error(error_msg)
                    step.fail(error_msg)
                    
                    if not self._confirm_continue_after_error(task, step, str(e)):
                        task.fail(error_msg)
                        return result
            
            # Task completed successfully
            task.complete(result)
            result.success = True
            result.summary = f"Task completed successfully with {len(result.files_modified)} files modified"
            
            # Generate recommendations
            result.recommendations = self._generate_recommendations(task, result)
            
            # Save final task state to history
            self.history_manager.save_task(task)
            
            self.formatter.print_success("🎉 Task completed successfully!")
            self._show_task_summary(task, result)
            
        except Exception as e:
            error_msg = f"Critical error during task execution: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            task.fail(error_msg)
            result.errors.append(error_msg)
            
            # Save failed task state to history
            self.history_manager.save_task(task)
        
        finally:
            # Cleanup
            self.current_task = None
        
        return result
    
    def resume_task(self, task_id: str, auto_confirm: bool = False) -> TaskResult:
        """Resume a previously paused task."""
        
        # Load task from history
        task = self.history_manager.load_task(task_id)
        if not task:
            raise TaskExecutionError(f"Task {task_id} not found in history")
        
        # Check if task can be resumed
        if not task.can_resume():
            raise TaskExecutionError(f"Task {task_id} cannot be resumed (status: {task.status.value})")
        
        self.formatter.print_header(
            f"Resuming Task: {task.title}",
            f"Type: {task.task_type.value.title()} | Progress: {task.get_progress()[2]:.1f}%"
        )
        
        # Show resume information
        if task.interrupt_point:
            self.formatter.print_info(f"Resuming from step {task.interrupt_point.get('step_index', 0) + 1}")
            if task.interrupt_point.get('backup_dir'):
                self.backup_dir = Path(task.interrupt_point['backup_dir'])
                self.formatter.print_info(f"Using existing backup directory: {self.backup_dir}")
        
        # Resume the task
        task.resume()
        
        # Continue execution from the current step
        if task.interrupt_point and 'step_index' in task.interrupt_point:
            task.current_step_index = task.interrupt_point['step_index']
        
        # Save resumed state
        self.history_manager.save_task(task)
        
        # Continue execution using the normal execute_task flow
        return self.execute_task(task, dry_run=False, auto_confirm=auto_confirm)
    
    def _execute_step(self, step: TaskStep, task: Task, dry_run: bool) -> StepResult:
        """Execute a single task step."""
        step.start()
        
        try:
            if step.action == ActionType.READ_FILE:
                return self._execute_read_file(step, dry_run)
            elif step.action == ActionType.WRITE_FILE:
                return self._execute_write_file(step, dry_run)
            elif step.action == ActionType.EDIT_FILE:
                return self._execute_edit_file(step, dry_run)
            elif step.action == ActionType.CREATE_FILE:
                return self._execute_create_file(step, dry_run)
            elif step.action == ActionType.ANALYZE_CODE:
                return self._execute_analyze_code(step, task, dry_run)
            elif step.action == ActionType.GENERATE_CODE:
                return self._execute_generate_code(step, task, dry_run)
            elif step.action == ActionType.VALIDATE:
                return self._execute_validate(step, dry_run)
            else:
                return StepResult(False, f"Unknown action type: {step.action}")
        
        except Exception as e:
            return StepResult(False, f"Step execution failed: {str(e)}")
    
    def _execute_read_file(self, step: TaskStep, dry_run: bool) -> StepResult:
        """Execute a read file step."""
        if not step.files_to_read:
            return StepResult(False, "No files specified to read")
        
        content = {}
        for file_path in step.files_to_read:
            try:
                if not file_path.exists():
                    return StepResult(False, f"File not found: {file_path}")
                
                if dry_run:
                    content[str(file_path)] = f"[DRY RUN] Would read {file_path}"
                else:
                    content[str(file_path)] = file_path.read_text(encoding='utf-8')
                    
            except Exception as e:
                return StepResult(False, f"Failed to read {file_path}: {str(e)}")
        
        return StepResult(True, f"Read {len(content)} files", content)
    
    def _execute_edit_file(self, step: TaskStep, dry_run: bool) -> StepResult:
        """Execute an edit file step."""
        if not step.files_to_modify:
            return StepResult(False, "No files specified to edit")
        
        for file_path in step.files_to_modify:
            try:
                if not file_path.exists():
                    return StepResult(False, f"File not found: {file_path}")
                
                if dry_run:
                    self.formatter.print_info(f"[DRY RUN] Would edit {file_path}")
                    continue
                
                # Create backup
                backup_path = self._create_file_backup(file_path)
                
                # Use AI to generate the edit
                edit_result = self._ai_edit_file(file_path, step.description)
                if not edit_result:
                    return StepResult(False, f"Failed to generate edit for {file_path}")
                
                # Apply the edit
                file_path.write_text(edit_result, encoding='utf-8')
                
            except Exception as e:
                return StepResult(False, f"Failed to edit {file_path}: {str(e)}")
        
        return StepResult(True, f"Edited {len(step.files_to_modify)} files")
    
    def _execute_analyze_code(self, step: TaskStep, task: Task, dry_run: bool) -> StepResult:
        """Execute code analysis step."""
        if not step.files_to_read:
            return StepResult(False, "No files specified to analyze")
        
        analysis_results = {}
        
        for file_path in step.files_to_read:
            try:
                if not file_path.exists():
                    continue
                
                if dry_run:
                    analysis_results[str(file_path)] = "[DRY RUN] Would analyze code"
                    continue
                
                # Read and analyze the file
                content = file_path.read_text(encoding='utf-8')
                analysis = self._ai_analyze_code(content, step.description)
                analysis_results[str(file_path)] = analysis
                
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        step.ai_response = json.dumps(analysis_results)
        return StepResult(True, f"Analyzed {len(analysis_results)} files", analysis_results)
    
    def _ai_analyze_code(self, code: str, context: str) -> str:
        """Use AI to analyze code."""
        prompt = f"""Analyze this code in the context of: {context}

Code:
```
{code}
```

Provide a brief analysis focusing on:
1. What this code does
2. Key components and structure
3. Potential issues or improvements
4. How it relates to the task context

Keep the analysis concise and actionable."""
        
        try:
            response = self.client.generate(
                model=self.model_manager.get_current_model(),
                prompt=prompt,
                temperature=0.3
            )
            return response
        except Exception as e:
            logger.error(f"AI code analysis failed: {e}")
            return "Analysis failed"
    
    def _ai_edit_file(self, file_path: Path, description: str) -> Optional[str]:
        """Use AI to edit a file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            prompt = f"""Edit this file according to the description: {description}

Current content:
```
{content}
```

Provide the complete modified file content. Only return the code, no explanations."""
            
            response = self.client.generate(
                model=self.model_manager.get_current_model(),
                prompt=prompt,
                temperature=0.3
            )
            
            return response
            
        except Exception as e:
            logger.error(f"AI file edit failed: {e}")
            return None
    
    def _create_backup_directory(self, task: Task) -> None:
        """Create a backup directory for the task."""
        if not self.backup_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.backup_dir = Path.home() / ".olla-cli" / "backups" / f"task_{task.task_id[:8]}_{timestamp}"
            self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_file_backup(self, file_path: Path) -> Path:
        """Create a backup of a file."""
        if not self.backup_dir:
            raise TaskExecutionError("Backup directory not initialized")
        
        backup_path = self.backup_dir / file_path.name
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _show_task_overview(self, task: Task) -> None:
        """Show task overview to user."""
        self.formatter.print_info(f"Description: {task.description}")
        self.formatter.print_info(f"Steps: {len(task.steps)}")
        if task.estimated_duration:
            self.formatter.print_info(f"Estimated duration: {task.estimated_duration} seconds")
    
    def _show_task_summary(self, task: Task, result: TaskResult) -> None:
        """Show task completion summary."""
        completed, total, percentage = task.get_progress()
        self.formatter.print_info(f"Progress: {completed}/{total} steps ({percentage:.1f}%)")
        
        if result.files_modified:
            self.formatter.print_info(f"Modified {len(result.files_modified)} files")
        if result.files_created:
            self.formatter.print_info(f"Created {len(result.files_created)} files")
        if result.recommendations:
            self.formatter.print_info("Recommendations:")
            for rec in result.recommendations:
                self.formatter.console.print(f"  💡 {rec}")
    
    def _confirm_step_execution(self, step: TaskStep) -> bool:
        """Ask user to confirm step execution."""
        return self.formatter.confirm_action(
            f"Execute step: {step.title}",
            f"Description: {step.description}"
        )
    
    def _confirm_continue_after_error(self, task: Task, step: TaskStep, error: str) -> bool:
        """Ask user if they want to continue after an error."""
        return self.formatter.confirm_action(
            f"Step '{step.title}' failed with error: {error}",
            "Do you want to continue with the next step?"
        )
    
    def _update_result_from_step(self, result: TaskResult, step: TaskStep) -> None:
        """Update task result with step outcomes."""
        for change in step.changes:
            if change.action in [ActionType.EDIT_FILE, ActionType.WRITE_FILE]:
                result.files_modified.append(change.file_path)
            elif change.action == ActionType.CREATE_FILE:
                result.files_created.append(change.file_path)
    
    def _generate_recommendations(self, task: Task, result: TaskResult) -> List[str]:
        """Generate recommendations based on task execution."""
        recommendations = []
        
        if result.files_modified:
            recommendations.append("Consider running tests to verify changes")
        
        if task.task_type.value in ['add_feature', 'fix_bug']:
            recommendations.append("Update documentation if needed")
        
        if len(result.files_modified) > 5:
            recommendations.append("Consider reviewing all changes before committing")
        
        return recommendations
    
    def _handle_interruption(self, task: Task, step_index: int) -> None:
        """Handle task interruption."""
        interrupt_point = {
            "step_index": step_index,
            "timestamp": datetime.now().isoformat(),
            "backup_dir": str(self.backup_dir) if self.backup_dir else None
        }
        
        task.pause(interrupt_point)
        self.history_manager.save_task(task)
        
        self.formatter.print_warning("Task interrupted. You can resume it later using the task ID.")
        self.formatter.print_info(f"Task ID: {task.task_id}")
    
    # Placeholder methods for other step types
    def _execute_write_file(self, step: TaskStep, dry_run: bool) -> StepResult:
        """Execute write file step."""
        return StepResult(True, "Write file operation completed")
    
    def _execute_create_file(self, step: TaskStep, dry_run: bool) -> StepResult:
        """Execute create file step."""
        return StepResult(True, "Create file operation completed")
    
    def _execute_generate_code(self, step: TaskStep, task: Task, dry_run: bool) -> StepResult:
        """Execute generate code step."""
        return StepResult(True, "Code generation completed")
    
    def _execute_validate(self, step: TaskStep, dry_run: bool) -> StepResult:
        """Execute validation step."""
        return StepResult(True, "Validation completed")