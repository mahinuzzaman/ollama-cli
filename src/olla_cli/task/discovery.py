"""File discovery engine for task execution."""

import re
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging

from .models import TaskType, TaskContext
from ..context import ContextBuilder

logger = logging.getLogger('olla-cli')


class FileDiscoveryEngine:
    """Discovers files relevant to task execution based on context."""
    
    def __init__(self, context_manager: Optional[ContextBuilder] = None):
        self.context_manager = context_manager
        
        # File patterns for different task types
        self.task_file_patterns = {
            TaskType.ADD_FEATURE: [r'.*\.py$', r'.*\.js$', r'.*\.ts$', r'.*\.java$'],
            TaskType.FIX_BUG: [r'.*\.py$', r'.*\.js$', r'.*\.ts$', r'.*\.java$', r'.*\.log$'],
            TaskType.ADD_TESTS: [r'test_.*\.py$', r'.*_test\.py$', r'.*\.test\.js$', r'.*\.spec\.js$'],
            TaskType.UPDATE_DOCS: [r'README.*', r'.*\.md$', r'.*\.rst$', r'docs/.*'],
        }
    
    def discover_files(self, task_description: str, task_type: TaskType, 
                      context: TaskContext) -> Dict[str, List[Path]]:
        """Discover files relevant to the task."""
        
        discovery_result = {
            "target_files": [],
            "related_files": [],
            "test_files": [],
            "config_files": [],
            "suggested_new": []
        }
        
        # Extract file mentions from description
        mentioned_files = self._extract_file_mentions(task_description, context.working_directory)
        discovery_result["target_files"].extend(mentioned_files)
        
        # Find files by keywords
        keywords = self._extract_keywords(task_description)
        keyword_files = self._find_files_by_keywords(keywords, context.working_directory)
        discovery_result["related_files"].extend(keyword_files)
        
        # Find files by patterns based on task type
        pattern_files = self._find_files_by_patterns(task_type, context.working_directory)
        discovery_result["related_files"].extend(pattern_files)
        
        # Find test files
        test_files = self._find_test_files(context.working_directory)
        discovery_result["test_files"].extend(test_files)
        
        # Find configuration files
        config_files = self._find_config_files(context.working_directory)
        discovery_result["config_files"].extend(config_files)
        
        # Suggest new files if needed
        new_files = self._suggest_new_files(task_description, task_type, context)
        discovery_result["suggested_new"].extend(new_files)
        
        # Remove duplicates and ensure files exist
        for key in discovery_result:
            if key != "suggested_new":  # New files don't exist yet
                discovery_result[key] = [f for f in set(discovery_result[key]) if f.exists()]
            else:
                discovery_result[key] = list(set(discovery_result[key]))
        
        return discovery_result
    
    def _extract_file_mentions(self, description: str, working_dir: Path) -> List[Path]:
        """Extract explicit file mentions from task description."""
        files = []
        
        # Common file patterns
        patterns = [
            r'(?:file|script|module)\s+["\']?([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)["\']?',
            r'["\']([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9]+)["\']',
            r'(?:^|\s)([a-zA-Z0-9_-]+\.[a-zA-Z0-9]+)(?:\s|$)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                file_path = working_dir / match
                if file_path.exists():
                    files.append(file_path)
                    
                # Also check relative to project root
                if self.context_manager:
                    alt_path = self.context_manager.working_directory / match
                    if alt_path.exists() and alt_path not in files:
                        files.append(alt_path)
        
        return files
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extract relevant keywords from task description."""
        # Remove common words and extract meaningful terms
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', description.lower())
        
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:10]  # Limit to most relevant
    
    def _find_files_by_keywords(self, keywords: List[str], search_dir: Path) -> List[Path]:
        """Find files whose names or content contain keywords."""
        if not keywords:
            return []
        
        files = []
        
        # Search for files with matching names
        for pattern in [f"*{keyword}*" for keyword in keywords]:
            files.extend(search_dir.rglob(pattern))
        
        # Limit results to avoid overwhelming
        return files[:20]
    
    def _find_files_by_patterns(self, task_type: TaskType, search_dir: Path) -> List[Path]:
        """Find files matching patterns for the task type."""
        patterns = self.task_file_patterns.get(task_type, [])
        files = []
        
        for pattern in patterns:
            try:
                for file_path in search_dir.rglob("*"):
                    if file_path.is_file() and re.match(pattern, str(file_path)):
                        files.append(file_path)
            except Exception as e:
                logger.debug(f"Pattern search error: {e}")
        
        return files[:15]  # Limit results
    
    def _find_test_files(self, search_dir: Path) -> List[Path]:
        """Find test files in the project."""
        test_patterns = [
            "test_*.py", "*_test.py", "tests.py",
            "*.test.js", "*.spec.js", "test/*.js",
            "*Test.java", "test*.java"
        ]
        
        files = []
        for pattern in test_patterns:
            files.extend(search_dir.rglob(pattern))
        
        return files[:10]
    
    def _find_config_files(self, search_dir: Path) -> List[Path]:
        """Find configuration files."""
        config_files = [
            "package.json", "requirements.txt", "setup.py", "Cargo.toml",
            "config.py", "settings.py", ".env", "config.json",
            "Makefile", "CMakeLists.txt", ".gitignore"
        ]
        
        files = []
        for filename in config_files:
            file_path = search_dir / filename
            if file_path.exists():
                files.append(file_path)
        
        return files
    
    def _suggest_new_files(self, description: str, task_type: TaskType, 
                          context: TaskContext) -> List[Path]:
        """Suggest new files that might need to be created."""
        suggestions = []
        
        if task_type == TaskType.ADD_TESTS:
            # Suggest test file names based on existing files
            for existing_file in context.working_directory.rglob("*.py"):
                if not existing_file.name.startswith("test_"):
                    test_name = f"test_{existing_file.stem}.py"
                    suggestions.append(context.working_directory / test_name)
        
        elif task_type == TaskType.ADD_FEATURE:
            # Suggest feature-related files
            if "api" in description.lower():
                suggestions.append(context.working_directory / "api.py")
            if "model" in description.lower():
                suggestions.append(context.working_directory / "models.py")
            if "view" in description.lower():
                suggestions.append(context.working_directory / "views.py")
        
        elif task_type == TaskType.UPDATE_DOCS:
            # Suggest documentation files
            if not (context.working_directory / "README.md").exists():
                suggestions.append(context.working_directory / "README.md")
            if not (context.working_directory / "docs").exists():
                suggestions.append(context.working_directory / "docs" / "index.md")
        
        return suggestions[:5]  # Limit suggestions
    
    def get_file_relationships(self, files: List[Path]) -> Dict[Path, List[Path]]:
        """Analyze relationships between files."""
        relationships = {}
        
        for file_path in files:
            if not file_path.exists():
                continue
                
            related = []
            try:
                # Simple relationship detection based on imports/includes
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                
                # Python imports
                import_matches = re.findall(r'from\s+(\w+)\s+import|import\s+(\w+)', content)
                for match in import_matches:
                    module_name = match[0] or match[1]
                    potential_file = file_path.parent / f"{module_name}.py"
                    if potential_file.exists() and potential_file in files:
                        related.append(potential_file)
                
                # JavaScript/TypeScript imports
                js_imports = re.findall(r'import.*from\s+["\'](.+?)["\']', content)
                for imp in js_imports:
                    if not imp.startswith('.'):
                        continue
                    potential_file = (file_path.parent / imp).with_suffix('.js')
                    if potential_file.exists() and potential_file in files:
                        related.append(potential_file)
                
            except Exception as e:
                logger.debug(f"Error analyzing file relationships for {file_path}: {e}")
            
            relationships[file_path] = related
        
        return relationships