"""Context Analysis System for project and file relationship analysis."""

import os
import json
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import logging

logger = logging.getLogger('olla-cli.intelligence.context')


class ContextAnalyzer:
    """Analyzes project context and file relationships for better decision making."""
    
    def __init__(self):
        self.project_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_timeout = 300  # 5 minutes
        
    async def analyze_project_context(self, current_dir: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the current project context."""
        if current_dir is None:
            current_dir = os.getcwd()
        
        current_dir = os.path.abspath(current_dir)
        
        # Check cache first
        if current_dir in self.project_cache:
            cache_entry = self.project_cache[current_dir]
            import time
            if time.time() - cache_entry.get('timestamp', 0) < self.cache_timeout:
                return cache_entry['context']
        
        # Analyze project structure
        context = {
            'project_root': self._find_project_root(current_dir),
            'current_directory': current_dir,
            'project_type': await self._detect_project_type(current_dir),
            'primary_language': await self._detect_primary_language(current_dir),
            'frameworks': await self._detect_frameworks(current_dir),
            'build_tools': await self._detect_build_tools(current_dir),
            'config_files': await self._find_config_files(current_dir),
            'recent_files': await self._get_recent_files(current_dir),
            'file_structure': await self._analyze_file_structure(current_dir)
        }
        
        # Cache the result
        import time
        self.project_cache[current_dir] = {
            'context': context,
            'timestamp': time.time()
        }
        
        return context
    
    def _find_project_root(self, current_dir: str) -> Optional[str]:
        """Find the project root directory."""
        path = Path(current_dir)
        
        # Look for common project root indicators
        root_indicators = [
            '.git', '.gitignore', 'README.md', 'README.rst',
            'pyproject.toml', 'setup.py', 'package.json', 'Cargo.toml',
            'pom.xml', 'build.gradle', 'composer.json', 'Gemfile'
        ]
        
        for parent in [path] + list(path.parents):
            for indicator in root_indicators:
                if (parent / indicator).exists():
                    return str(parent)
        
        return current_dir
    
    async def _detect_project_type(self, current_dir: str) -> str:
        """Detect the type of project."""
        path = Path(current_dir)
        project_root = self._find_project_root(current_dir)
        if project_root:
            path = Path(project_root)
        
        # Check for specific project types
        if (path / 'pyproject.toml').exists() or (path / 'setup.py').exists():
            return 'python_package'
        elif (path / 'package.json').exists():
            package_json = path / 'package.json'
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    if 'react' in data.get('dependencies', {}) or 'react' in data.get('devDependencies', {}):
                        return 'react_app'
                    elif 'vue' in data.get('dependencies', {}) or 'vue' in data.get('devDependencies', {}):
                        return 'vue_app'
                    elif 'angular' in data.get('dependencies', {}) or '@angular' in str(data.get('dependencies', {})):
                        return 'angular_app'
                    else:
                        return 'node_app'
            except:
                return 'node_app'
        elif (path / 'Cargo.toml').exists():
            return 'rust_project'
        elif (path / 'pom.xml').exists():
            return 'maven_project'
        elif (path / 'build.gradle').exists():
            return 'gradle_project'
        elif (path / 'composer.json').exists():
            return 'php_project'
        elif (path / 'Gemfile').exists():
            return 'ruby_project'
        elif (path / 'go.mod').exists():
            return 'go_module'
        else:
            return 'general'
    
    async def _detect_primary_language(self, current_dir: str) -> Optional[str]:
        """Detect the primary programming language."""
        path = Path(current_dir)
        project_root = self._find_project_root(current_dir)
        if project_root:
            path = Path(project_root)
        
        # Count files by extension
        extension_counts = {}
        
        for file_path in path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                ext = file_path.suffix.lower()
                extension_counts[ext] = extension_counts.get(ext, 0) + 1
        
        # Map extensions to languages
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.jsx': 'javascript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.php': 'php',
            '.rb': 'ruby',
            '.kt': 'kotlin',
            '.swift': 'swift'
        }
        
        # Find most common language
        lang_counts = {}
        for ext, count in extension_counts.items():
            if ext in ext_to_lang:
                lang = ext_to_lang[ext]
                lang_counts[lang] = lang_counts.get(lang, 0) + count
        
        if lang_counts:
            return max(lang_counts.items(), key=lambda x: x[1])[0]
        
        return None
    
    async def _detect_frameworks(self, current_dir: str) -> List[str]:
        """Detect frameworks used in the project."""
        frameworks = []
        project_root = self._find_project_root(current_dir)
        if not project_root:
            return frameworks
        
        path = Path(project_root)
        
        # Check package.json for JS frameworks
        package_json = path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    if 'react' in deps:
                        frameworks.append('react')
                    if 'vue' in deps:
                        frameworks.append('vue')
                    if any('@angular' in dep for dep in deps):
                        frameworks.append('angular')
                    if 'express' in deps:
                        frameworks.append('express')
                    if 'next' in deps or 'nextjs' in deps:
                        frameworks.append('nextjs')
                    if 'nuxt' in deps:
                        frameworks.append('nuxt')
            except:
                pass
        
        # Check Python files for frameworks
        for py_file in path.rglob('*.py'):
            if self._should_ignore_file(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'from django' in content or 'import django' in content:
                        if 'django' not in frameworks:
                            frameworks.append('django')
                    if 'from flask' in content or 'import flask' in content:
                        if 'flask' not in frameworks:
                            frameworks.append('flask')
                    if 'from fastapi' in content or 'import fastapi' in content:
                        if 'fastapi' not in frameworks:
                            frameworks.append('fastapi')
            except:
                continue
            
            # Don't check too many files
            if len(frameworks) > 5:
                break
        
        # Check for Spring (Java)
        for java_file in path.rglob('*.java'):
            if self._should_ignore_file(java_file):
                continue
            try:
                with open(java_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '@SpringBootApplication' in content or 'org.springframework' in content:
                        if 'spring' not in frameworks:
                            frameworks.append('spring')
                        break
            except:
                continue
        
        return frameworks
    
    async def _detect_build_tools(self, current_dir: str) -> List[str]:
        """Detect build tools used in the project."""
        build_tools = []
        project_root = self._find_project_root(current_dir)
        if not project_root:
            return build_tools
        
        path = Path(project_root)
        
        # Check for various build tool files
        build_files = {
            'package.json': 'npm',
            'yarn.lock': 'yarn',
            'pnpm-lock.yaml': 'pnpm',
            'pyproject.toml': 'poetry',
            'setup.py': 'setuptools',
            'requirements.txt': 'pip',
            'Pipfile': 'pipenv',
            'Cargo.toml': 'cargo',
            'pom.xml': 'maven',
            'build.gradle': 'gradle',
            'Makefile': 'make',
            'composer.json': 'composer',
            'Gemfile': 'bundler'
        }
        
        for file_name, tool in build_files.items():
            if (path / file_name).exists():
                build_tools.append(tool)
        
        return build_tools
    
    async def _find_config_files(self, current_dir: str) -> List[str]:
        """Find configuration files in the project."""
        config_files = []
        project_root = self._find_project_root(current_dir)
        if not project_root:
            return config_files
        
        path = Path(project_root)
        
        # Common config file patterns
        config_patterns = [
            '*.json', '*.yaml', '*.yml', '*.toml', '*.ini',
            '.env*', 'config.*', 'settings.*', '.*rc', '.*config'
        ]
        
        for pattern in config_patterns:
            for config_file in path.glob(pattern):
                if config_file.is_file() and not self._should_ignore_file(config_file):
                    config_files.append(str(config_file.relative_to(path)))
        
        return config_files[:10]  # Limit to 10 most relevant config files
    
    async def _get_recent_files(self, current_dir: str, limit: int = 10) -> List[str]:
        """Get recently modified files."""
        path = Path(current_dir)
        project_root = self._find_project_root(current_dir)
        if project_root:
            path = Path(project_root)
        
        files = []
        for file_path in path.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                try:
                    files.append((file_path, file_path.stat().st_mtime))
                except:
                    continue
        
        # Sort by modification time (most recent first)
        files.sort(key=lambda x: x[1], reverse=True)
        
        # Return relative paths
        recent_files = []
        for file_path, _ in files[:limit]:
            try:
                relative_path = str(file_path.relative_to(path))
                recent_files.append(relative_path)
            except:
                recent_files.append(str(file_path))
        
        return recent_files
    
    async def _analyze_file_structure(self, current_dir: str) -> Dict[str, Any]:
        """Analyze the file structure of the project."""
        path = Path(current_dir)
        project_root = self._find_project_root(current_dir)
        if project_root:
            path = Path(project_root)
        
        structure = {
            'total_files': 0,
            'directories': [],
            'file_types': {},
            'large_files': [],
            'empty_directories': []
        }
        
        for item in path.rglob('*'):
            if self._should_ignore_file(item):
                continue
                
            if item.is_file():
                structure['total_files'] += 1
                
                # Count file types
                ext = item.suffix.lower() or 'no_extension'
                structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
                
                # Track large files (> 1MB)
                try:
                    if item.stat().st_size > 1024 * 1024:
                        structure['large_files'].append(str(item.relative_to(path)))
                except:
                    pass
                    
            elif item.is_dir():
                try:
                    relative_dir = str(item.relative_to(path))
                    structure['directories'].append(relative_dir)
                    
                    # Check if directory is empty
                    if not any(item.iterdir()):
                        structure['empty_directories'].append(relative_dir)
                except:
                    pass
        
        # Limit lists to reasonable sizes
        structure['directories'] = structure['directories'][:20]
        structure['large_files'] = structure['large_files'][:10]
        structure['empty_directories'] = structure['empty_directories'][:10]
        
        return structure
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if a file should be ignored in analysis."""
        ignore_patterns = {
            # Version control
            '.git', '.svn', '.hg',
            # Dependencies
            'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env',
            'vendor', 'target', 'dist', 'build', '.tox',
            # IDE files
            '.vscode', '.idea', '.eclipse', '*.tmp', '*.temp',
            # OS files
            '.DS_Store', 'Thumbs.db',
            # Compiled files
            '*.pyc', '*.pyo', '*.class', '*.o', '*.so'
        }
        
        path_str = str(file_path).lower()
        name = file_path.name.lower()
        
        for pattern in ignore_patterns:
            if pattern.startswith('*.'):
                # Extension pattern
                if name.endswith(pattern[1:]):
                    return True
            else:
                # Directory or file pattern
                if pattern in path_str or name == pattern:
                    return True
        
        return False
    
    async def analyze_file_relationships(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze relationships between files."""
        relationships = {
            'imports': {},
            'dependencies': {},
            'similar_files': [],
            'related_configs': []
        }
        
        for file_path in file_paths:
            if not os.path.exists(file_path):
                continue
                
            path = Path(file_path)
            
            # Analyze imports for Python files
            if path.suffix == '.py':
                imports = await self._extract_python_imports(file_path)
                relationships['imports'][file_path] = imports
            
            # Analyze imports for JavaScript/TypeScript files
            elif path.suffix in ['.js', '.ts', '.jsx', '.tsx']:
                imports = await self._extract_js_imports(file_path)
                relationships['imports'][file_path] = imports
        
        return relationships
    
    async def _extract_python_imports(self, file_path: str) -> List[str]:
        """Extract import statements from Python files."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('from '):
                        imports.append(line)
        except:
            pass
        return imports
    
    async def _extract_js_imports(self, file_path: str) -> List[str]:
        """Extract import statements from JavaScript/TypeScript files."""
        imports = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('import ') or line.startswith('const ') and 'require(' in line:
                        imports.append(line)
        except:
            pass
        return imports
    
    def clear_cache(self) -> None:
        """Clear the project context cache."""
        self.project_cache.clear()
        logger.info("Project context cache cleared")