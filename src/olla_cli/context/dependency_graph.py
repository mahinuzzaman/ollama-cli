"""Dependency graph building for code context management."""

import ast
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
import logging

from .context_manager import FileInfo, LanguageDetector


logger = logging.getLogger('olla-cli')


@dataclass
class DependencyNode:
    """Represents a node in the dependency graph."""
    file_path: Path
    imports: Set[str] = field(default_factory=set)
    exports: Set[str] = field(default_factory=set)
    internal_dependencies: Set[Path] = field(default_factory=set)
    external_dependencies: Set[str] = field(default_factory=set)


class ImportExtractor:
    """Extract import statements from code files."""
    
    @staticmethod
    def extract_python_imports(content: str, file_path: Path) -> Tuple[List[str], List[str]]:
        """Extract Python imports and exports."""
        imports = []
        exports = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if node.level > 0:  # Relative import
                            imports.append(f"{'.' * node.level}{node.module or ''}")
                        else:
                            imports.append(node.module)
                        
                        # Add specific imports
                        for alias in node.names:
                            if alias.name != '*':
                                imports.append(f"{node.module}.{alias.name}")
                
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    # Functions and classes are potential exports
                    exports.append(node.name)
                
                elif isinstance(node, ast.Assign):
                    # Global variable assignments are potential exports
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            exports.append(target.id)
        
        except SyntaxError as e:
            logger.warning(f"Failed to parse Python file {file_path}: {e}")
        
        return imports, exports
    
    @staticmethod
    def extract_js_imports(content: str, file_path: Path) -> Tuple[List[str], List[str]]:
        """Extract JavaScript/TypeScript imports and exports."""
        imports = []
        exports = []
        
        # ES6 imports
        import_patterns = [
            r'import\s+.*\s+from\s+["\']([^"\']+)["\']',  # import ... from 'module'
            r'import\s*\(\s*["\']([^"\']+)["\']\s*\)',      # import('module')
            r'import\s+["\']([^"\']+)["\']',                # import 'module'
        ]
        
        for pattern in import_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)
        
        # CommonJS require
        require_pattern = r'require\s*\(\s*["\']([^"\']+)["\']\s*\)'
        matches = re.findall(require_pattern, content, re.MULTILINE)
        imports.extend(matches)
        
        # Exports
        export_patterns = [
            r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)',
            r'export\s*\{\s*([^}]+)\s*\}',
            r'module\.exports\s*=\s*(\w+)',
        ]
        
        for pattern in export_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if isinstance(match, str) and ',' in match:
                    # Handle export { a, b, c }
                    exports.extend([name.strip() for name in match.split(',')])
                else:
                    exports.append(match)
        
        return imports, exports
    
    @staticmethod
    def extract_imports(content: str, file_path: Path, language: str) -> Tuple[List[str], List[str]]:
        """Extract imports and exports based on language."""
        if language == 'python':
            return ImportExtractor.extract_python_imports(content, file_path)
        elif language in ['javascript', 'typescript']:
            return ImportExtractor.extract_js_imports(content, file_path)
        else:
            return [], []


class DependencyGraph:
    """Build and manage dependency graphs for projects."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.nodes: Dict[Path, DependencyNode] = {}
        self.language = LanguageDetector.detect_project_language(project_root)
    
    def build_graph(self, files: List[FileInfo]) -> None:
        """Build dependency graph from list of files."""
        logger.info(f"Building dependency graph for {len(files)} files")
        
        # First pass: extract all imports and exports
        for file_info in files:
            try:
                with open(file_info.path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                imports, exports = ImportExtractor.extract_imports(
                    content, file_info.path, file_info.language
                )
                
                node = DependencyNode(
                    file_path=file_info.path,
                    imports=set(imports),
                    exports=set(exports)
                )
                
                self.nodes[file_info.path] = node
                
            except Exception as e:
                logger.warning(f"Failed to process {file_info.path}: {e}")
        
        # Second pass: resolve internal dependencies
        self._resolve_internal_dependencies()
        
        logger.info(f"Dependency graph built with {len(self.nodes)} nodes")
    
    def _resolve_internal_dependencies(self) -> None:
        """Resolve internal project dependencies."""
        # Create a mapping of module names to file paths
        module_map = self._build_module_map()
        
        for file_path, node in self.nodes.items():
            for import_name in node.imports:
                resolved_path = self._resolve_import(import_name, file_path, module_map)
                
                if resolved_path and resolved_path in self.nodes:
                    node.internal_dependencies.add(resolved_path)
                elif not resolved_path:
                    # External dependency
                    node.external_dependencies.add(import_name)
    
    def _build_module_map(self) -> Dict[str, Path]:
        """Build mapping from module names to file paths."""
        module_map = {}
        
        for file_path in self.nodes.keys():
            relative_path = file_path.relative_to(self.project_root)
            
            # Remove file extension and convert to module name
            module_parts = list(relative_path.parts)
            if module_parts:
                module_parts[-1] = module_parts[-1].rsplit('.', 1)[0]  # Remove extension
                
                # Handle __init__.py files
                if module_parts[-1] == '__init__':
                    module_parts.pop()
                
                module_name = '.'.join(module_parts)
                module_map[module_name] = file_path
                
                # Also map the full path
                module_map[str(relative_path)] = file_path
        
        return module_map
    
    def _resolve_import(self, import_name: str, current_file: Path, module_map: Dict[str, Path]) -> Optional[Path]:
        """Resolve an import to a file path."""
        if self.language == 'python':
            return self._resolve_python_import(import_name, current_file, module_map)
        elif self.language in ['javascript', 'typescript']:
            return self._resolve_js_import(import_name, current_file, module_map)
        return None
    
    def _resolve_python_import(self, import_name: str, current_file: Path, module_map: Dict[str, Path]) -> Optional[Path]:
        """Resolve Python import."""
        # Handle relative imports
        if import_name.startswith('.'):
            current_dir = current_file.parent
            level = len(import_name) - len(import_name.lstrip('.'))
            
            # Go up the directory tree
            for _ in range(level - 1):
                current_dir = current_dir.parent
            
            if level == len(import_name):  # Just dots, import current package
                module_name = str(current_dir.relative_to(self.project_root)).replace('/', '.')
            else:
                remainder = import_name[level:]
                module_name = str(current_dir.relative_to(self.project_root)).replace('/', '.') + '.' + remainder
            
            return module_map.get(module_name)
        
        # Handle absolute imports
        return module_map.get(import_name)
    
    def _resolve_js_import(self, import_name: str, current_file: Path, module_map: Dict[str, Path]) -> Optional[Path]:
        """Resolve JavaScript/TypeScript import."""
        # Handle relative imports
        if import_name.startswith('./') or import_name.startswith('../'):
            current_dir = current_file.parent
            import_path = current_dir / import_name
            try:
                resolved_path = import_path.resolve()
                if resolved_path.exists():
                    return resolved_path
                
                # Try with extensions
                for ext in ['.js', '.ts', '.jsx', '.tsx']:
                    ext_path = resolved_path.with_suffix(ext)
                    if ext_path.exists():
                        return ext_path
            except Exception:
                pass
        
        # Handle module imports (could be local modules)
        return module_map.get(import_name)
    
    def get_dependencies(self, file_path: Path, depth: int = 1) -> Set[Path]:
        """Get dependencies of a file up to specified depth."""
        if file_path not in self.nodes:
            return set()
        
        visited = set()
        to_visit = [(file_path, 0)]
        dependencies = set()
        
        while to_visit:
            current_path, current_depth = to_visit.pop(0)
            
            if current_path in visited or current_depth > depth:
                continue
            
            visited.add(current_path)
            
            if current_path != file_path:  # Don't include the file itself
                dependencies.add(current_path)
            
            if current_depth < depth and current_path in self.nodes:
                node = self.nodes[current_path]
                for dep_path in node.internal_dependencies:
                    if dep_path not in visited:
                        to_visit.append((dep_path, current_depth + 1))
        
        return dependencies
    
    def get_dependents(self, file_path: Path) -> Set[Path]:
        """Get files that depend on the given file."""
        dependents = set()
        
        for node_path, node in self.nodes.items():
            if file_path in node.internal_dependencies:
                dependents.add(node_path)
        
        return dependents
    
    def find_circular_dependencies(self) -> List[List[Path]]:
        """Find circular dependencies in the graph."""
        def dfs(path: Path, visited: Set[Path], rec_stack: Set[Path], current_path: List[Path]) -> List[List[Path]]:
            visited.add(path)
            rec_stack.add(path)
            current_path.append(path)
            cycles = []
            
            if path in self.nodes:
                for dep_path in self.nodes[path].internal_dependencies:
                    if dep_path not in visited:
                        cycles.extend(dfs(dep_path, visited, rec_stack, current_path[:]))
                    elif dep_path in rec_stack:
                        # Found a cycle
                        cycle_start = current_path.index(dep_path)
                        cycle = current_path[cycle_start:] + [dep_path]
                        cycles.append(cycle)
            
            rec_stack.remove(path)
            return cycles
        
        visited = set()
        all_cycles = []
        
        for file_path in self.nodes:
            if file_path not in visited:
                cycles = dfs(file_path, visited, set(), [])
                all_cycles.extend(cycles)
        
        return all_cycles
    
    def export_graph(self) -> Dict[str, any]:
        """Export dependency graph to dictionary."""
        graph_data = {
            'project_root': str(self.project_root),
            'language': self.language,
            'nodes': {}
        }
        
        for file_path, node in self.nodes.items():
            relative_path = str(file_path.relative_to(self.project_root))
            graph_data['nodes'][relative_path] = {
                'imports': list(node.imports),
                'exports': list(node.exports),
                'internal_dependencies': [
                    str(dep.relative_to(self.project_root)) 
                    for dep in node.internal_dependencies
                ],
                'external_dependencies': list(node.external_dependencies)
            }
        
        return graph_data