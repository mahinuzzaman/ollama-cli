"""Task parser for converting natural language descriptions into structured tasks."""

import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
import logging

from .models import Task, TaskStep, TaskType, TaskContext, ActionType, StepStatus
from ..client import OllamaClient, ModelManager
from ..context import ContextBuilder
from ..utils import MessageBuilder

logger = logging.getLogger('olla-cli')


class TaskParser:
    """Parses natural language task descriptions into structured tasks."""
    
    def __init__(self, client: OllamaClient, model_manager: ModelManager, 
                 context_manager: Optional[ContextBuilder] = None):
        self.client = client
        self.model_manager = model_manager
        self.context_manager = context_manager
        
        # Task type detection keywords
        self.task_type_keywords = {
            TaskType.ADD_FEATURE: ["add", "implement", "create", "build", "feature", "functionality"],
            TaskType.FIX_BUG: ["fix", "resolve", "debug", "bug", "error", "issue", "problem"],
            TaskType.REFACTOR: ["refactor", "restructure", "reorganize", "clean", "improve", "redesign"],
            TaskType.ADD_TESTS: ["test", "testing", "coverage", "unit test", "integration test"],
            TaskType.UPDATE_DOCS: ["document", "documentation", "docs", "readme", "comment"],
            TaskType.CREATE_FILE: ["create file", "new file", "generate file", "make file"],
            TaskType.ANALYZE: ["analyze", "review", "examine", "investigate", "understand"]
        }
    
    def parse_task_description(self, description: str, 
                             context_path: Optional[Path] = None) -> Task:
        """Parse a natural language task description into a structured Task."""
        
        # Basic task creation
        task = Task()
        task.description = description.strip()
        task.title = self._generate_title(description)
        task.task_type = self._identify_task_type(description)
        
        # Set up context
        if context_path or self.context_manager:
            task.context = self._build_task_context(context_path)
        
        # Generate steps using AI or templates
        try:
            task.steps = self._generate_steps_with_ai(task)
        except Exception as e:
            logger.warning(f"AI step generation failed: {e}, falling back to template")
            task.steps = self._generate_steps_from_template(task)
        
        # Estimate duration
        task.estimated_duration = self._estimate_task_duration(task)
        
        return task
    
    def _identify_task_type(self, description: str) -> TaskType:
        """Identify the task type from description."""
        description_lower = description.lower()
        
        # Score each task type based on keyword matches
        scores = {}
        for task_type, keywords in self.task_type_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                scores[task_type] = score
        
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        
        return TaskType.CUSTOM
    
    def _generate_title(self, description: str) -> str:
        """Generate a concise title from description."""
        # Take first sentence or first 60 characters
        sentences = description.split('.')
        if sentences:
            title = sentences[0].strip()
            if len(title) <= 60:
                return title.capitalize()
        
        # Fallback to truncated description
        return (description[:57] + "...") if len(description) > 60 else description.capitalize()
    
    def _build_task_context(self, context_path: Optional[Path] = None) -> TaskContext:
        """Build task context from available information."""
        if context_path:
            working_dir = context_path
        elif self.context_manager:
            working_dir = self.context_manager.working_directory
        else:
            working_dir = Path.cwd()
        
        context = TaskContext(working_directory=working_dir)
        
        # Add project root detection
        if self.context_manager:
            context.project_root = self._find_project_root(working_dir)
            context.language = self._detect_primary_language(working_dir)
            context.framework = self._detect_framework(working_dir)
        
        return context
    
    def _generate_steps_with_ai(self, task: Task) -> List[TaskStep]:
        """Generate task steps using AI."""
        prompt = self._build_step_generation_prompt(task)
        
        try:
            response = self.client.generate(
                model=self.model_manager.get_current_model(),
                prompt=prompt,
                temperature=0.3
            )
            
            return self._parse_ai_generated_steps(response, task)
            
        except Exception as e:
            logger.error(f"AI step generation failed: {e}")
            raise
    
    def _build_step_generation_prompt(self, task: Task) -> str:
        """Build prompt for AI step generation."""
        context_info = ""
        if task.context:
            context_info = f"""
Context:
- Working directory: {task.context.working_directory}
- Language: {task.context.language or 'Unknown'}
- Framework: {task.context.framework or 'None'}
"""
        
        return f"""Break down this task into clear, actionable steps:

Task: {task.description}
Type: {task.task_type.value}
{context_info}

Generate 3-7 specific steps that can be executed programmatically. For each step, provide:
1. Title (brief, action-oriented)
2. Description (what needs to be done)
3. Action type (read_file, edit_file, create_file, analyze_code, etc.)
4. Files that need to be read or modified

Format as JSON:
{{
  "steps": [
    {{
      "title": "Step title",
      "description": "Detailed description",
      "action": "action_type",
      "files_to_read": ["path1", "path2"],
      "files_to_modify": ["path1"]
    }}
  ]
}}"""
    
    def _parse_ai_generated_steps(self, response: str, task: Task) -> List[TaskStep]:
        """Parse AI-generated step response into TaskStep objects."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in AI response")
            
            data = json.loads(json_match.group())
            steps = []
            
            for i, step_data in enumerate(data.get('steps', [])):
                step = TaskStep()
                step.title = step_data.get('title', f'Step {i+1}')
                step.description = step_data.get('description', '')
                
                # Parse action type
                action_str = step_data.get('action', 'analyze_code').upper()
                try:
                    step.action = ActionType(action_str.lower())
                except ValueError:
                    step.action = ActionType.ANALYZE_CODE
                
                # Parse file paths
                step.files_to_read = [Path(f) for f in step_data.get('files_to_read', [])]
                step.files_to_modify = [Path(f) for f in step_data.get('files_to_modify', [])]
                
                steps.append(step)
            
            return steps
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            # Fallback to template-based generation
            return self._generate_steps_from_template(task)
    
    def _generate_steps_from_template(self, task: Task) -> List[TaskStep]:
        """Generate steps based on task type templates."""
        base_steps = {
            TaskType.ADD_FEATURE: [
                ("Analyze existing code", "Understand current implementation", ActionType.ANALYZE_CODE),
                ("Plan feature implementation", "Design the new feature", ActionType.GENERATE_CODE),
                ("Implement feature", "Write the feature code", ActionType.EDIT_FILE),
                ("Add tests", "Create tests for the feature", ActionType.CREATE_FILE),
            ],
            TaskType.FIX_BUG: [
                ("Identify bug location", "Find where the bug occurs", ActionType.SEARCH_FILES),
                ("Analyze bug cause", "Understand the root cause", ActionType.ANALYZE_CODE),
                ("Implement fix", "Apply the bug fix", ActionType.EDIT_FILE),
                ("Test fix", "Verify the fix works", ActionType.VALIDATE),
            ],
            TaskType.REFACTOR: [
                ("Analyze current structure", "Review existing code", ActionType.ANALYZE_CODE),
                ("Plan refactoring", "Design improved structure", ActionType.GENERATE_CODE),
                ("Apply refactoring", "Restructure the code", ActionType.EDIT_FILE),
                ("Validate changes", "Ensure functionality is preserved", ActionType.VALIDATE),
            ],
            TaskType.ADD_TESTS: [
                ("Analyze code to test", "Identify testable components", ActionType.ANALYZE_CODE),
                ("Generate test cases", "Create comprehensive test scenarios", ActionType.GENERATE_CODE),
                ("Create test files", "Write test implementations", ActionType.CREATE_FILE),
                ("Run tests", "Execute and validate tests", ActionType.RUN_COMMAND),
            ]
        }
        
        template_steps = base_steps.get(task.task_type, [
            ("Analyze task", "Understand requirements", ActionType.ANALYZE_CODE),
            ("Plan implementation", "Design solution approach", ActionType.GENERATE_CODE),
            ("Execute changes", "Implement the solution", ActionType.EDIT_FILE),
        ])
        
        steps = []
        for title, description, action in template_steps:
            step = TaskStep()
            step.title = title
            step.description = description
            step.action = action
            step.estimated_duration = 60  # 1 minute default
            steps.append(step)
        
        return steps
    
    def _estimate_task_duration(self, task: Task) -> int:
        """Estimate task duration based on complexity."""
        base_duration = len(task.steps) * 60  # 1 minute per step
        
        # Adjust based on task type
        multipliers = {
            TaskType.ADD_FEATURE: 1.5,
            TaskType.FIX_BUG: 1.2,
            TaskType.REFACTOR: 2.0,
            TaskType.ADD_TESTS: 1.3,
            TaskType.UPDATE_DOCS: 0.8,
            TaskType.CREATE_FILE: 0.7,
            TaskType.ANALYZE: 0.9,
        }
        
        multiplier = multipliers.get(task.task_type, 1.0)
        return int(base_duration * multiplier)
    
    def _find_project_root(self, start_path: Path) -> Optional[Path]:
        """Find project root directory."""
        current = start_path.resolve()
        
        # Look for common project indicators
        indicators = ['.git', 'package.json', 'requirements.txt', 'Cargo.toml', 'go.mod']
        
        while current.parent != current:
            if any((current / indicator).exists() for indicator in indicators):
                return current
            current = current.parent
        
        return None
    
    def _detect_primary_language(self, project_path: Path) -> Optional[str]:
        """Detect the primary programming language."""
        if not project_path.exists():
            return None
        
        # Count files by extension
        extension_counts = {}
        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix:
                ext = file_path.suffix.lower()
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # Map extensions to languages
        extension_to_language = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.rs': 'rust',
            '.go': 'go',
            '.rb': 'ruby',
            '.php': 'php',
        }
        
        if extension_counts:
            most_common_ext = max(extension_counts.items(), key=lambda x: x[1])[0]
            return extension_to_language.get(most_common_ext)
        
        return None
    
    def _detect_framework(self, project_path: Path) -> Optional[str]:
        """Detect the framework being used."""
        # Check for framework indicators
        if (project_path / 'package.json').exists():
            try:
                with open(project_path / 'package.json') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    if 'react' in deps:
                        return 'react'
                    elif 'vue' in deps:
                        return 'vue'
                    elif 'express' in deps:
                        return 'express'
            except:
                pass
        
        if (project_path / 'requirements.txt').exists():
            try:
                with open(project_path / 'requirements.txt') as f:
                    content = f.read()
                    if 'flask' in content.lower():
                        return 'flask'
                    elif 'django' in content.lower():
                        return 'django'
                    elif 'fastapi' in content.lower():
                        return 'fastapi'
            except:
                pass
        
        return None
    
    def validate_task(self, task: Task) -> List[str]:
        """Validate a task and return warnings."""
        warnings = []
        
        if not task.title.strip():
            warnings.append("Task has no title")
        
        if not task.description.strip():
            warnings.append("Task has no description")
        
        if not task.steps:
            warnings.append("Task has no steps defined")
        
        # Check for circular dependencies
        step_ids = {step.step_id for step in task.steps}
        for step in task.steps:
            for dep_id in step.dependencies:
                if dep_id not in step_ids:
                    warnings.append(f"Step '{step.title}' has invalid dependency: {dep_id}")
        
        return warnings
    
    def suggest_improvements(self, task: Task) -> List[str]:
        """Suggest improvements for a task."""
        suggestions = []
        
        if task.estimated_duration and task.estimated_duration > 600:  # 10 minutes
            suggestions.append("Consider breaking this task into smaller subtasks")
        
        if len(task.steps) > 10:
            suggestions.append("Task has many steps - consider grouping related steps")
        
        if not any(step.action == ActionType.VALIDATE for step in task.steps):
            suggestions.append("Consider adding validation steps to verify results")
        
        return suggestions