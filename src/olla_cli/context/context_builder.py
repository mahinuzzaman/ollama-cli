"""Core context building and management functionality."""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Optional, Union, Tuple
from dataclasses import dataclass
import logging

from .context_manager import (
    ContextStrategy, ContextResult, FileInfo, ProjectInfo,
    LanguageDetector, FileFilter, FileTree, CodeExtractor, FileCache
)
from .dependency_graph import DependencyGraph
from ..utils import TokenCounter


logger = logging.getLogger('olla-cli')


class LanguageContextBuilder:
    """Language-specific context builders."""
    
    @staticmethod
    def build_python_context(file_info: FileInfo, content: str, strategy: ContextStrategy) -> str:
        """Build Python-specific context."""
        context_parts = []
        
        if strategy == ContextStrategy.SINGLE_FILE:
            context_parts.append(f"# File: {file_info.relative_path}")
            context_parts.append(f"# Language: Python")
            if file_info.imports:
                context_parts.append(f"# Imports: {', '.join(file_info.imports[:10])}")
            context_parts.append("")
            context_parts.append("```python")
            context_parts.append(content)
            context_parts.append("```")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def build_javascript_context(file_info: FileInfo, content: str, strategy: ContextStrategy) -> str:
        """Build JavaScript/TypeScript-specific context."""
        context_parts = []
        
        language = "typescript" if file_info.path.suffix in ['.ts', '.tsx'] else "javascript"
        
        if strategy == ContextStrategy.SINGLE_FILE:
            context_parts.append(f"// File: {file_info.relative_path}")
            context_parts.append(f"// Language: {language.title()}")
            if file_info.imports:
                context_parts.append(f"// Imports: {', '.join(file_info.imports[:10])}")
            context_parts.append("")
            context_parts.append(f"```{language}")
            context_parts.append(content)
            context_parts.append("```")
        
        return "\n".join(context_parts)
    
    @staticmethod
    def build_generic_context(file_info: FileInfo, content: str, strategy: ContextStrategy) -> str:
        """Build generic language context."""
        context_parts = []
        
        if strategy == ContextStrategy.SINGLE_FILE:
            context_parts.append(f"File: {file_info.relative_path}")
            context_parts.append(f"Language: {file_info.language}")
            context_parts.append("")
            context_parts.append(f"```{file_info.language}")
            context_parts.append(content)
            context_parts.append("```")
        
        return "\n".join(context_parts)


class ContextOptimizer:
    """Optimize context size and content."""
    
    @staticmethod
    def calculate_context_size(content: str) -> int:
        """Calculate context size in tokens."""
        return TokenCounter.estimate_tokens(content)
    
    @staticmethod
    def optimize_for_token_limit(content: str, max_tokens: int, priority_sections: List[str] = None) -> str:
        """Optimize content to fit within token limit."""
        current_tokens = ContextOptimizer.calculate_context_size(content)
        
        if current_tokens <= max_tokens:
            return content
        
        logger.info(f"Optimizing context: {current_tokens} -> {max_tokens} tokens")
        
        # Split content into sections
        sections = content.split('\n\n')
        
        # If we have priority sections, keep them first
        if priority_sections:
            priority_content = []
            remaining_sections = []
            
            for section in sections:
                is_priority = any(priority in section for priority in priority_sections)
                if is_priority:
                    priority_content.append(section)
                else:
                    remaining_sections.append(section)
            
            sections = priority_content + remaining_sections
        
        # Build optimized content
        optimized_sections = []
        current_size = 0
        
        for section in sections:
            section_size = ContextOptimizer.calculate_context_size(section)
            if current_size + section_size <= max_tokens:
                optimized_sections.append(section)
                current_size += section_size
            else:
                # Try to include partial section
                remaining_tokens = max_tokens - current_size
                if remaining_tokens > 100:  # Only if significant space left
                    truncated_section = ContextOptimizer._truncate_section(section, remaining_tokens)
                    if truncated_section:
                        optimized_sections.append(truncated_section)
                break
        
        if len(optimized_sections) < len(sections):
            optimized_sections.append("\n[... content truncated to fit token limit ...]")
        
        return '\n\n'.join(optimized_sections)
    
    @staticmethod
    def _truncate_section(section: str, max_tokens: int) -> Optional[str]:
        """Truncate a section to fit within token limit."""
        lines = section.split('\n')
        truncated_lines = []
        current_tokens = 0
        
        for line in lines:
            line_tokens = ContextOptimizer.calculate_context_size(line)
            if current_tokens + line_tokens <= max_tokens:
                truncated_lines.append(line)
                current_tokens += line_tokens
            else:
                break
        
        if truncated_lines and len(truncated_lines) < len(lines):
            truncated_lines.append("// ... truncated ...")
            return '\n'.join(truncated_lines)
        
        return None


class ContextManager:
    """Main context management class."""
    
    def __init__(self, project_root: Optional[Path] = None, cache_dir: Optional[Path] = None):
        """Initialize ContextManager.
        
        Args:
            project_root: Project root directory
            cache_dir: Cache directory (defaults to ~/.olla-cli/cache)
        """
        self.project_root = project_root or self._detect_project_root()
        self.cache_dir = cache_dir or Path.home() / '.olla-cli' / 'cache'
        
        # Initialize components
        self.file_filter = FileFilter(self.project_root)
        self.file_tree = FileTree(self.project_root, self.file_filter)
        self.file_cache = FileCache(self.cache_dir)
        self.dependency_graph = DependencyGraph(self.project_root)
        
        # Project info
        self.project_info = self._analyze_project()
        
        logger.info(f"ContextManager initialized for project: {self.project_root}")
        logger.info(f"Project language: {self.project_info.language}, Framework: {self.project_info.framework}")
    
    def _detect_project_root(self) -> Path:
        """Detect project root directory."""
        current = Path.cwd()
        
        # Look for common project indicators
        indicators = [
            '.git', '.gitignore', 'package.json', 'requirements.txt',
            'pyproject.toml', 'setup.py', 'Cargo.toml', 'go.mod',
            'pom.xml', 'build.gradle', 'Makefile'
        ]
        
        while current != current.parent:
            for indicator in indicators:
                if (current / indicator).exists():
                    return current
            current = current.parent
        
        # Fallback to current directory
        return Path.cwd()
    
    def _analyze_project(self) -> ProjectInfo:
        """Analyze project structure."""
        language = LanguageDetector.detect_project_language(self.project_root)
        framework = LanguageDetector.detect_framework(self.project_root, language)
        
        project_info = ProjectInfo(
            root=self.project_root,
            language=language,
            framework=framework
        )
        
        # Scan files
        files = self._scan_project_files()
        project_info.files = {str(f.relative_path): f for f in files}
        
        # Build dependency graph
        if files:
            self.dependency_graph.build_graph(files)
        
        return project_info
    
    def _scan_project_files(self, max_files: int = 1000) -> List[FileInfo]:
        """Scan project files."""
        files = []
        scanned_count = 0
        
        for file_path in self.project_root.rglob('*'):
            if scanned_count >= max_files:
                logger.warning(f"Reached maximum file scan limit ({max_files})")
                break
            
            if not file_path.is_file() or self.file_filter.should_ignore(file_path):
                continue
            
            try:
                stat = file_path.stat()
                language = LanguageDetector.detect_language(file_path)
                relative_path = file_path.relative_to(self.project_root)
                
                # Check cache first
                cached_info = self.file_cache.get(file_path)
                if cached_info and cached_info.modified == stat.st_mtime:
                    files.append(cached_info)
                    scanned_count += 1
                    continue
                
                # Read and analyze file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # Skip binary files
                    continue
                
                # Calculate content hash
                content_hash = hashlib.md5(content.encode()).hexdigest()
                
                # Extract code elements
                functions = [f['name'] for f in CodeExtractor.extract_functions(content, language)]
                classes = [c['name'] for c in CodeExtractor.extract_classes(content, language)]
                
                # Extract imports/exports
                from .dependency_graph import ImportExtractor
                imports, exports = ImportExtractor.extract_imports(content, file_path, language)
                
                file_info = FileInfo(
                    path=file_path,
                    relative_path=relative_path,
                    size=stat.st_size,
                    modified=stat.st_mtime,
                    language=language,
                    content_hash=content_hash,
                    imports=imports,
                    exports=exports,
                    functions=functions,
                    classes=classes
                )
                
                # Cache the file info
                self.file_cache.set(file_path, file_info)
                files.append(file_info)
                scanned_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to analyze file {file_path}: {e}")
                continue
        
        logger.info(f"Scanned {len(files)} files")
        return files
    
    def build_context(
        self,
        target_file: Union[str, Path],
        strategy: ContextStrategy = ContextStrategy.SINGLE_FILE,
        max_tokens: Optional[int] = None,
        include_dependencies: bool = True,
        dependency_depth: int = 1
    ) -> ContextResult:
        """Build context for a target file.
        
        Args:
            target_file: Target file path
            strategy: Context building strategy
            max_tokens: Maximum tokens in context
            include_dependencies: Whether to include dependencies
            dependency_depth: Depth of dependency inclusion
            
        Returns:
            ContextResult with built context
        """
        target_path = Path(target_file)
        if not target_path.is_absolute():
            target_path = self.project_root / target_path
        
        logger.info(f"Building context for {target_path} using strategy {strategy.value}")
        
        if strategy == ContextStrategy.SINGLE_FILE:
            return self._build_single_file_context(target_path, max_tokens)
        elif strategy == ContextStrategy.RELATED_FILES:
            return self._build_related_files_context(target_path, max_tokens, dependency_depth)
        elif strategy == ContextStrategy.PROJECT_OVERVIEW:
            return self._build_project_overview_context(target_path, max_tokens)
        else:
            raise ValueError(f"Unknown context strategy: {strategy}")
    
    def _build_single_file_context(self, target_path: Path, max_tokens: Optional[int]) -> ContextResult:
        """Build context for a single file."""
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {target_path}")
        
        # Get file info
        relative_path = target_path.relative_to(self.project_root)
        file_key = str(relative_path)
        
        if file_key in self.project_info.files:
            file_info = self.project_info.files[file_key]
        else:
            # Analyze file on-demand
            stat = target_path.stat()
            language = LanguageDetector.detect_language(target_path)
            
            file_info = FileInfo(
                path=target_path,
                relative_path=relative_path,
                size=stat.st_size,
                modified=stat.st_mtime,
                language=language
            )
        
        # Read file content
        with open(target_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Build language-specific context
        if file_info.language == 'python':
            context_content = LanguageContextBuilder.build_python_context(
                file_info, content, ContextStrategy.SINGLE_FILE
            )
        elif file_info.language in ['javascript', 'typescript']:
            context_content = LanguageContextBuilder.build_javascript_context(
                file_info, content, ContextStrategy.SINGLE_FILE
            )
        else:
            context_content = LanguageContextBuilder.build_generic_context(
                file_info, content, ContextStrategy.SINGLE_FILE
            )
        
        # Optimize for token limit
        if max_tokens:
            context_content = ContextOptimizer.optimize_for_token_limit(context_content, max_tokens)
        
        token_count = ContextOptimizer.calculate_context_size(context_content)
        
        return ContextResult(
            strategy=ContextStrategy.SINGLE_FILE,
            files=[file_info],
            content=context_content,
            token_count=token_count,
            metadata={
                'target_file': str(relative_path),
                'language': file_info.language
            }
        )
    
    def _build_related_files_context(self, target_path: Path, max_tokens: Optional[int], depth: int) -> ContextResult:
        """Build context including related files."""
        # Start with single file context
        main_context = self._build_single_file_context(target_path, None)
        
        # Get related files through dependencies
        related_paths = self.dependency_graph.get_dependencies(target_path, depth)
        
        context_parts = [main_context.content]
        all_files = [main_context.files[0]]
        
        # Add related files
        for related_path in related_paths:
            try:
                related_context = self._build_single_file_context(related_path, None)
                context_parts.append(f"\n\n{'='*50}")
                context_parts.append(f"RELATED FILE: {related_context.files[0].relative_path}")
                context_parts.append('='*50)
                context_parts.append(related_context.content)
                all_files.extend(related_context.files)
            except Exception as e:
                logger.warning(f"Failed to build context for related file {related_path}: {e}")
        
        full_content = '\n'.join(context_parts)
        
        # Optimize for token limit
        if max_tokens:
            full_content = ContextOptimizer.optimize_for_token_limit(
                full_content, max_tokens, 
                priority_sections=[str(main_context.files[0].relative_path)]
            )
        
        token_count = ContextOptimizer.calculate_context_size(full_content)
        
        return ContextResult(
            strategy=ContextStrategy.RELATED_FILES,
            files=all_files,
            content=full_content,
            token_count=token_count,
            metadata={
                'target_file': str(target_path.relative_to(self.project_root)),
                'related_files': [str(f.relative_path) for f in all_files[1:]],
                'dependency_depth': depth
            }
        )
    
    def _build_project_overview_context(self, target_path: Path, max_tokens: Optional[int]) -> ContextResult:
        """Build project overview context."""
        context_parts = []
        
        # Project structure
        context_parts.append(f"# Project Overview: {self.project_root.name}")
        context_parts.append(f"Language: {self.project_info.language}")
        if self.project_info.framework:
            context_parts.append(f"Framework: {self.project_info.framework}")
        context_parts.append("")
        
        # File tree
        context_parts.append("## Project Structure")
        context_parts.append("```")
        context_parts.append(self.file_tree.generate_tree(max_depth=2, max_files=30))
        context_parts.append("```")
        context_parts.append("")
        
        # Key files summary
        context_parts.append("## Key Files")
        key_files = self._get_key_files()
        for file_info in key_files[:10]:  # Limit to top 10
            context_parts.append(f"- **{file_info.relative_path}** ({file_info.language})")
            if file_info.functions:
                context_parts.append(f"  Functions: {', '.join(file_info.functions[:5])}")
            if file_info.classes:
                context_parts.append(f"  Classes: {', '.join(file_info.classes[:3])}")
        
        context_parts.append("")
        
        # Target file context
        target_context = self._build_single_file_context(target_path, None)
        context_parts.append("## Target File")
        context_parts.append(target_context.content)
        
        full_content = '\n'.join(context_parts)
        
        # Optimize for token limit
        if max_tokens:
            full_content = ContextOptimizer.optimize_for_token_limit(
                full_content, max_tokens,
                priority_sections=["Target File", str(target_context.files[0].relative_path)]
            )
        
        token_count = ContextOptimizer.calculate_context_size(full_content)
        
        return ContextResult(
            strategy=ContextStrategy.PROJECT_OVERVIEW,
            files=[target_context.files[0]] + key_files,
            content=full_content,
            token_count=token_count,
            metadata={
                'target_file': str(target_path.relative_to(self.project_root)),
                'project_language': self.project_info.language,
                'project_framework': self.project_info.framework,
                'total_files': len(self.project_info.files)
            }
        )
    
    def _get_key_files(self) -> List[FileInfo]:
        """Get key files in the project."""
        files = list(self.project_info.files.values())
        
        # Score files by importance
        scored_files = []
        for file_info in files:
            score = 0
            
            # Size factor (larger files are often more important)
            score += min(file_info.size / 1000, 10)
            
            # Function/class count
            score += len(file_info.functions) * 2
            score += len(file_info.classes) * 3
            
            # Import/export count (more connected files)
            score += len(file_info.imports)
            score += len(file_info.exports) * 2
            
            # File type preferences
            if file_info.path.name in ['main.py', 'app.py', 'index.js', 'main.js']:
                score += 20
            if file_info.path.suffix in ['.py', '.js', '.ts']:
                score += 5
            
            scored_files.append((score, file_info))
        
        # Sort by score and return top files
        scored_files.sort(key=lambda x: x[0], reverse=True)
        return [file_info for _, file_info in scored_files]
    
    def get_project_summary(self) -> Dict[str, any]:
        """Get project summary information."""
        return {
            'root': str(self.project_root),
            'language': self.project_info.language,
            'framework': self.project_info.framework,
            'total_files': len(self.project_info.files),
            'file_types': self._get_file_type_counts(),
            'dependency_stats': self._get_dependency_stats(),
        }
    
    def _get_file_type_counts(self) -> Dict[str, int]:
        """Get count of files by language."""
        counts = {}
        for file_info in self.project_info.files.values():
            counts[file_info.language] = counts.get(file_info.language, 0) + 1
        return counts
    
    def _get_dependency_stats(self) -> Dict[str, int]:
        """Get dependency statistics."""
        total_internal_deps = sum(
            len(node.internal_dependencies) 
            for node in self.dependency_graph.nodes.values()
        )
        total_external_deps = len(set().union(
            *[node.external_dependencies for node in self.dependency_graph.nodes.values()]
        ))
        
        return {
            'total_internal_dependencies': total_internal_deps,
            'total_external_dependencies': total_external_deps,
            'files_with_dependencies': len([
                node for node in self.dependency_graph.nodes.values()
                if node.internal_dependencies
            ])
        }