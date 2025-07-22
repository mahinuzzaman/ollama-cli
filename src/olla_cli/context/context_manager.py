"""Intelligent code context management for Olla CLI."""

import os
import re
import ast
import json
import time
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional, Union, Tuple, Any
from enum import Enum
import logging

from ..utils import TokenCounter


logger = logging.getLogger('olla-cli')


class ContextStrategy(Enum):
    """Context building strategies."""
    SINGLE_FILE = "single_file"
    RELATED_FILES = "related_files"
    PROJECT_OVERVIEW = "project_overview"


@dataclass
class FileInfo:
    """Information about a file in the project."""
    path: Path
    relative_path: Path
    size: int
    modified: float
    language: str
    content_hash: str = ""
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


@dataclass
class ProjectInfo:
    """Project structure information."""
    root: Path
    language: str
    framework: Optional[str]
    files: Dict[str, FileInfo] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class ContextResult:
    """Result of context building."""
    strategy: ContextStrategy
    files: List[FileInfo]
    content: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class LanguageDetector:
    """Detect programming language and framework."""
    
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rs': 'rust',
        '.go': 'go',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',
    }
    
    FRAMEWORK_INDICATORS = {
        'python': {
            'django': ['manage.py', 'settings.py', 'wsgi.py'],
            'flask': ['app.py', 'application.py'],
            'fastapi': ['main.py'],
            'pytest': ['pytest.ini', 'conftest.py'],
        },
        'javascript': {
            'react': ['package.json'],  # Check for react in dependencies
            'vue': ['vue.config.js', 'nuxt.config.js'],
            'angular': ['angular.json', '.angular-cli.json'],
            'express': ['package.json'],  # Check for express in dependencies
            'next': ['next.config.js'],
        },
        'typescript': {
            'angular': ['angular.json', 'tsconfig.json'],
            'next': ['next.config.js', 'tsconfig.json'],
        }
    }
    
    @classmethod
    def detect_language(cls, file_path: Path) -> str:
        """Detect language from file extension."""
        return cls.LANGUAGE_EXTENSIONS.get(file_path.suffix.lower(), 'text')
    
    @classmethod
    def detect_project_language(cls, project_root: Path) -> str:
        """Detect primary project language."""
        language_counts = {}
        
        for file_path in project_root.rglob('*'):
            if file_path.is_file() and not cls._should_ignore_file(file_path):
                lang = cls.detect_language(file_path)
                language_counts[lang] = language_counts.get(lang, 0) + 1
        
        # Remove 'text' from consideration
        language_counts.pop('text', None)
        
        if not language_counts:
            return 'text'
        
        return max(language_counts, key=language_counts.get)
    
    @classmethod
    def detect_framework(cls, project_root: Path, language: str) -> Optional[str]:
        """Detect framework for the given language."""
        if language not in cls.FRAMEWORK_INDICATORS:
            return None
        
        for framework, indicators in cls.FRAMEWORK_INDICATORS[language].items():
            for indicator in indicators:
                if (project_root / indicator).exists():
                    # Special handling for package.json dependencies
                    if indicator == 'package.json':
                        try:
                            with open(project_root / 'package.json', 'r') as f:
                                package_data = json.load(f)
                                deps = {**package_data.get('dependencies', {}), 
                                       **package_data.get('devDependencies', {})}
                                if framework in deps or f"{framework}js" in deps:
                                    return framework
                        except (json.JSONDecodeError, FileNotFoundError):
                            continue
                    else:
                        return framework
        
        return None
    
    @staticmethod
    def _should_ignore_file(file_path: Path) -> bool:
        """Check if file should be ignored."""
        ignore_dirs = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'build', 'dist'}
        return any(part in ignore_dirs for part in file_path.parts)


class FileFilter:
    """Smart file filtering using .gitignore and .olla-ignore patterns."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.gitignore_patterns = self._load_ignore_patterns('.gitignore')
        self.olla_ignore_patterns = self._load_ignore_patterns('.olla-ignore')
        self.default_ignores = {
            # Version control
            '.git', '.svn', '.hg',
            # Dependencies
            'node_modules', '__pycache__', '.venv', 'venv', 'env',
            # Build outputs
            'build', 'dist', 'target', 'out', '.build',
            # IDE/Editor files
            '.vscode', '.idea', '*.swp', '*.swo', '*~',
            # OS files
            '.DS_Store', 'Thumbs.db',
            # Cache
            '.cache', '.pytest_cache', '.mypy_cache',
            # Logs
            '*.log', 'logs',
        }
    
    def _load_ignore_patterns(self, filename: str) -> List[str]:
        """Load ignore patterns from file."""
        ignore_file = self.project_root / filename
        if not ignore_file.exists():
            return []
        
        try:
            with open(ignore_file, 'r') as f:
                patterns = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
                return patterns
        except Exception as e:
            logger.warning(f"Failed to load {filename}: {e}")
            return []
    
    def should_ignore(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        relative_path = file_path.relative_to(self.project_root)
        path_str = str(relative_path)
        
        # Check default ignores
        for pattern in self.default_ignores:
            if self._matches_pattern(path_str, pattern):
                return True
        
        # Check .olla-ignore (higher priority)
        for pattern in self.olla_ignore_patterns:
            if self._matches_pattern(path_str, pattern):
                return True
        
        # Check .gitignore
        for pattern in self.gitignore_patterns:
            if self._matches_pattern(path_str, pattern):
                return True
        
        return False
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Check if path matches ignore pattern."""
        # Handle directory patterns
        if pattern.endswith('/'):
            pattern = pattern[:-1]
            return path.startswith(pattern + '/') or path == pattern
        
        # Handle wildcard patterns
        if '*' in pattern:
            import fnmatch
            return fnmatch.fnmatch(path, pattern)
        
        # Direct match or directory match
        return path == pattern or path.startswith(pattern + '/')


class FileTree:
    """Visualize project structure as a tree."""
    
    def __init__(self, project_root: Path, file_filter: FileFilter):
        self.project_root = project_root
        self.file_filter = file_filter
    
    def generate_tree(self, max_depth: int = 3, max_files: int = 50) -> str:
        """Generate a tree representation of the project."""
        tree_lines = [f"📁 {self.project_root.name}/"]
        files_shown = 0
        
        def add_directory(path: Path, prefix: str, depth: int):
            nonlocal files_shown
            if depth > max_depth or files_shown >= max_files:
                return
            
            try:
                items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            except PermissionError:
                return
            
            for i, item in enumerate(items):
                if files_shown >= max_files:
                    tree_lines.append(f"{prefix}└── ... (truncated)")
                    break
                
                if self.file_filter.should_ignore(item):
                    continue
                
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                next_prefix = prefix + ("    " if is_last else "│   ")
                
                if item.is_file():
                    icon = self._get_file_icon(item)
                    tree_lines.append(f"{prefix}{current_prefix}{icon} {item.name}")
                    files_shown += 1
                elif item.is_dir() and depth < max_depth:
                    tree_lines.append(f"{prefix}{current_prefix}📁 {item.name}/")
                    add_directory(item, next_prefix, depth + 1)
        
        add_directory(self.project_root, "", 0)
        
        if files_shown >= max_files:
            tree_lines.append("... (more files not shown)")
        
        return "\n".join(tree_lines)
    
    def _get_file_icon(self, file_path: Path) -> str:
        """Get appropriate icon for file type."""
        ext = file_path.suffix.lower()
        icons = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '📘',
            '.jsx': '⚛️',
            '.tsx': '⚛️',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.md': '📖',
            '.yml': '⚙️',
            '.yaml': '⚙️',
            '.toml': '⚙️',
            '.xml': '📄',
            '.sql': '🗃️',
            '.sh': '🔧',
            '.dockerfile': '🐳',
            '.gitignore': '🙈',
        }
        return icons.get(ext, '📄')


class CodeExtractor:
    """Extract relevant code sections from files."""
    
    @staticmethod
    def extract_functions(content: str, language: str) -> List[Dict[str, str]]:
        """Extract function definitions from code."""
        if language == 'python':
            return CodeExtractor._extract_python_functions(content)
        elif language in ['javascript', 'typescript']:
            return CodeExtractor._extract_js_functions(content)
        else:
            return []
    
    @staticmethod
    def extract_classes(content: str, language: str) -> List[Dict[str, str]]:
        """Extract class definitions from code."""
        if language == 'python':
            return CodeExtractor._extract_python_classes(content)
        elif language in ['javascript', 'typescript']:
            return CodeExtractor._extract_js_classes(content)
        else:
            return []
    
    @staticmethod
    def _extract_python_functions(content: str) -> List[Dict[str, str]]:
        """Extract Python functions."""
        functions = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Get function source
                    lines = content.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    
                    func_code = '\n'.join(lines[start_line:end_line])
                    
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'code': func_code,
                        'docstring': ast.get_docstring(node) or "",
                        'args': [arg.arg for arg in node.args.args]
                    })
        except SyntaxError:
            logger.warning("Failed to parse Python code for function extraction")
        
        return functions
    
    @staticmethod
    def _extract_python_classes(content: str) -> List[Dict[str, str]]:
        """Extract Python classes."""
        classes = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    lines = content.split('\n')
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 1
                    
                    class_code = '\n'.join(lines[start_line:end_line])
                    
                    # Extract methods
                    methods = []
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods.append(item.name)
                    
                    classes.append({
                        'name': node.name,
                        'line': node.lineno,
                        'code': class_code,
                        'docstring': ast.get_docstring(node) or "",
                        'methods': methods,
                        'bases': [base.id if isinstance(base, ast.Name) else str(base) for base in node.bases]
                    })
        except SyntaxError:
            logger.warning("Failed to parse Python code for class extraction")
        
        return classes
    
    @staticmethod
    def _extract_js_functions(content: str) -> List[Dict[str, str]]:
        """Extract JavaScript/TypeScript functions (basic regex-based)."""
        functions = []
        
        # Function declarations
        func_pattern = r'function\s+(\w+)\s*\([^)]*\)\s*\{'
        matches = re.finditer(func_pattern, content, re.MULTILINE)
        
        for match in matches:
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            functions.append({
                'name': name,
                'line': line_num,
                'code': '',  # Would need proper JS parser for full code
                'type': 'function'
            })
        
        # Arrow functions
        arrow_pattern = r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
        matches = re.finditer(arrow_pattern, content, re.MULTILINE)
        
        for match in matches:
            name = match.group(1)
            line_num = content[:match.start()].count('\n') + 1
            functions.append({
                'name': name,
                'line': line_num,
                'code': '',
                'type': 'arrow_function'
            })
        
        return functions
    
    @staticmethod
    def _extract_js_classes(content: str) -> List[Dict[str, str]]:
        """Extract JavaScript/TypeScript classes (basic regex-based)."""
        classes = []
        
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?\s*\{'
        matches = re.finditer(class_pattern, content, re.MULTILINE)
        
        for match in matches:
            name = match.group(1)
            extends = match.group(2) if match.group(2) else None
            line_num = content[:match.start()].count('\n') + 1
            
            classes.append({
                'name': name,
                'line': line_num,
                'extends': extends,
                'code': '',  # Would need proper JS parser for full code
            })
        
        return classes


class FileCache:
    """File content caching with TTL."""
    
    def __init__(self, cache_dir: Path, default_ttl: int = 3600):
        """Initialize file cache.
        
        Args:
            cache_dir: Cache directory path
            default_ttl: Default time-to-live in seconds
        """
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._metadata_file = cache_dir / 'metadata.json'
        self._load_metadata()
    
    def _load_metadata(self):
        """Load cache metadata."""
        try:
            if self._metadata_file.exists():
                with open(self._metadata_file, 'r') as f:
                    self._metadata = json.load(f)
            else:
                self._metadata = {}
        except (json.JSONDecodeError, FileNotFoundError):
            self._metadata = {}
    
    def _save_metadata(self):
        """Save cache metadata."""
        try:
            with open(self._metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache metadata: {e}")
    
    def _get_cache_key(self, file_path: Path) -> str:
        """Generate cache key for file."""
        return hashlib.md5(str(file_path).encode()).hexdigest()
    
    def get(self, file_path: Path) -> Optional[FileInfo]:
        """Get cached file info."""
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        # Check metadata for TTL
        if cache_key in self._metadata:
            cache_time = self._metadata[cache_key].get('cached_at', 0)
            ttl = self._metadata[cache_key].get('ttl', self.default_ttl)
            if time.time() - cache_time > ttl:
                # Cache expired
                self._cleanup_cache_entry(cache_key)
                return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                # Convert string paths back to Path objects
                data['path'] = Path(data['path'])
                data['relative_path'] = Path(data['relative_path'])
                return FileInfo(**data)
        except (json.JSONDecodeError, FileNotFoundError, TypeError):
            self._cleanup_cache_entry(cache_key)
            return None
    
    def set(self, file_path: Path, file_info: FileInfo, ttl: Optional[int] = None):
        """Cache file info."""
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            # Convert FileInfo to dict for JSON serialization
            data = {
                'path': str(file_info.path),
                'relative_path': str(file_info.relative_path),
                'size': file_info.size,
                'modified': file_info.modified,
                'language': file_info.language,
                'content_hash': file_info.content_hash,
                'imports': file_info.imports,
                'exports': file_info.exports,
                'functions': file_info.functions,
                'classes': file_info.classes,
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Update metadata
            self._metadata[cache_key] = {
                'file_path': str(file_path),
                'cached_at': time.time(),
                'ttl': ttl or self.default_ttl
            }
            self._save_metadata()
            
        except Exception as e:
            logger.warning(f"Failed to cache file info: {e}")
    
    def _cleanup_cache_entry(self, cache_key: str):
        """Clean up expired cache entry."""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            cache_file.unlink()
        self._metadata.pop(cache_key, None)
        self._save_metadata()
    
    def cleanup_expired(self):
        """Clean up all expired cache entries."""
        current_time = time.time()
        expired_keys = []
        
        for cache_key, metadata in self._metadata.items():
            cache_time = metadata.get('cached_at', 0)
            ttl = metadata.get('ttl', self.default_ttl)
            if current_time - cache_time > ttl:
                expired_keys.append(cache_key)
        
        for key in expired_keys:
            self._cleanup_cache_entry(key)
        
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")