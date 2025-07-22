"""Comprehensive output formatting system for olla-cli using Rich library."""

import os
import re
import sys
import json
import html
import tempfile
import webbrowser
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple, Iterator
from dataclasses import dataclass
from datetime import datetime
import logging

# Rich imports
from rich.console import Console, ConsoleOptions, RenderResult
from rich.style import Style
from rich.theme import Theme
from rich.panel import Panel
from rich.table import Table, Column
from rich.columns import Columns
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.progress import (
    Progress, SpinnerColumn, TextColumn, BarColumn, 
    TaskProgressColumn, TimeRemainingColumn, MofNCompleteColumn
)
from rich.live import Live
from rich.pager import Pager
from rich.align import Align
from rich.rule import Rule
from rich.tree import Tree
from rich.pretty import Pretty
from rich.traceback import install as install_traceback
from rich.highlighter import ReprHighlighter
from rich.prompt import Prompt, Confirm

# Additional imports
import pyperclip
import markdown as md_lib
from pygments import highlight
from pygments.lexers import get_lexer_by_name, guess_lexer_for_filename, ClassNotFound
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound as PygmentsClassNotFound

from ..config import Config

logger = logging.getLogger('olla-cli')

# Install rich traceback handler
install_traceback(show_locals=True)


class ThemeType(Enum):
    """Available theme types."""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"
    CUSTOM = "custom"


class OutputFormat(Enum):
    """Available output formats."""
    CONSOLE = "console"
    MARKDOWN = "markdown"
    HTML = "html"
    JSON = "json"
    PLAIN = "plain"


@dataclass
class FormatOptions:
    """Options for output formatting."""
    theme: ThemeType = ThemeType.DARK
    syntax_highlight: bool = True
    show_line_numbers: bool = True
    wrap_text: bool = True
    show_progress: bool = True
    enable_pager: bool = True
    max_width: Optional[int] = None
    export_format: OutputFormat = OutputFormat.CONSOLE
    custom_colors: Optional[Dict[str, str]] = None


class OllaThemes:
    """Custom themes for olla-cli."""
    
    DARK_THEME = Theme({
        "olla.primary": "bright_cyan",
        "olla.secondary": "bright_magenta",
        "olla.success": "bright_green",
        "olla.warning": "bright_yellow",
        "olla.error": "bright_red",
        "olla.info": "bright_blue",
        "olla.muted": "dim white",
        "olla.code": "bright_white on grey11",
        "olla.header": "bold bright_cyan",
        "olla.footer": "dim bright_cyan",
        "olla.brand": "bold bright_magenta",
        "olla.highlight": "bright_yellow on blue",
        "olla.diff.added": "bright_green",
        "olla.diff.removed": "bright_red",
        "olla.diff.modified": "bright_yellow",
        "olla.table.header": "bold bright_cyan",
        "olla.table.border": "bright_blue"
    })
    
    LIGHT_THEME = Theme({
        "olla.primary": "blue",
        "olla.secondary": "purple",
        "olla.success": "green",
        "olla.warning": "dark_orange",
        "olla.error": "red",
        "olla.info": "blue",
        "olla.muted": "dim black",
        "olla.code": "black on white",
        "olla.header": "bold blue",
        "olla.footer": "dim blue",
        "olla.brand": "bold purple",
        "olla.highlight": "black on yellow",
        "olla.diff.added": "green",
        "olla.diff.removed": "red",
        "olla.diff.modified": "dark_orange",
        "olla.table.header": "bold blue",
        "olla.table.border": "blue"
    })
    
    @classmethod
    def get_theme(cls, theme_type: ThemeType, custom_colors: Optional[Dict[str, str]] = None) -> Theme:
        """Get theme based on type."""
        if theme_type == ThemeType.LIGHT:
            base_theme = cls.LIGHT_THEME
        elif theme_type == ThemeType.AUTO:
            # Detect terminal background (simplified)
            if os.getenv('COLORFGBG', '').endswith('15'):  # Light background
                base_theme = cls.LIGHT_THEME
            else:
                base_theme = cls.DARK_THEME
        else:
            base_theme = cls.DARK_THEME
        
        if custom_colors:
            # Merge custom colors
            theme_dict = {**base_theme.styles, **custom_colors}
            return Theme(theme_dict)
        
        return base_theme


class SyntaxHighlighter:
    """Enhanced syntax highlighter with language detection."""
    
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.cc': 'cpp',
        '.cxx': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rs': 'rust',
        '.go': 'go',
        '.php': 'php',
        '.rb': 'ruby',
        '.sh': 'bash',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.json': 'json',
        '.xml': 'xml',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown',
        '.dockerfile': 'dockerfile',
        '.vim': 'vim'
    }
    
    LANGUAGE_PATTERNS = [
        (r'#!/usr/bin/env python|#!/usr/bin/python|^import |^from .+ import', 'python'),
        (r'#!/bin/bash|#!/usr/bin/bash|^#.*bash', 'bash'),
        (r'function\s+\w+\s*\(|var\s+\w+\s*=|const\s+\w+\s*=', 'javascript'),
        (r'interface\s+\w+|type\s+\w+\s*=|export\s+(interface|type)', 'typescript'),
        (r'public\s+(class|static)|private\s+\w+|package\s+\w+', 'java'),
        (r'#include\s*<|int\s+main\s*\(|printf\s*\(', 'c'),
        (r'std::|#include\s*<iostream>|namespace\s+\w+', 'cpp'),
        (r'fn\s+\w+\s*\(|let\s+\w+\s*=|pub\s+fn', 'rust'),
        (r'func\s+\w+\s*\(|package\s+main|import\s*\(', 'go'),
        (r'<\?php|function\s+\w+\s*\(|\$\w+\s*=', 'php'),
        (r'def\s+\w+|class\s+\w+|require\s+[\'"]', 'ruby'),
        (r'SELECT\s+|UPDATE\s+|INSERT\s+|DELETE\s+', 'sql'),
        (r'<html|<div|<span|<!DOCTYPE', 'html'),
        (r'\{\s*["\']?\w+["\']?\s*:|^\s*\[|\{.*\}', 'json'),
    ]
    
    @classmethod
    def detect_language(cls, code: str, filename: Optional[str] = None) -> str:
        """Detect programming language from code content or filename."""
        # Try filename extension first
        if filename:
            ext = Path(filename).suffix.lower()
            if ext in cls.LANGUAGE_EXTENSIONS:
                return cls.LANGUAGE_EXTENSIONS[ext]
        
        # Pattern matching
        for pattern, language in cls.LANGUAGE_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE | re.MULTILINE):
                return language
        
        return 'text'
    
    @classmethod
    def highlight_code(cls, code: str, language: Optional[str] = None, 
                      filename: Optional[str] = None, theme: str = "monokai") -> Syntax:
        """Create Rich Syntax object with highlighting."""
        if not language:
            language = cls.detect_language(code, filename)
        
        return Syntax(
            code, 
            language, 
            theme=theme,
            line_numbers=True,
            word_wrap=True,
            background_color="default"
        )


class DiffVisualizer:
    """Create visual diffs for code changes."""
    
    @staticmethod
    def create_diff(old_code: str, new_code: str, filename: str = "code") -> Panel:
        """Create a side-by-side diff visualization."""
        old_lines = old_code.strip().split('\n')
        new_lines = new_code.strip().split('\n')
        
        # Simple diff algorithm (in production, use difflib)
        max_lines = max(len(old_lines), len(new_lines))
        
        diff_table = Table(show_header=True, header_style="olla.table.header")
        diff_table.add_column("Before", style="olla.diff.removed", width=50)
        diff_table.add_column("After", style="olla.diff.added", width=50)
        
        for i in range(max_lines):
            old_line = old_lines[i] if i < len(old_lines) else ""
            new_line = new_lines[i] if i < len(new_lines) else ""
            
            old_text = Text(old_line)
            new_text = Text(new_line)
            
            # Highlight differences
            if old_line != new_line:
                if old_line and new_line:
                    old_text.stylize("olla.diff.modified")
                    new_text.stylize("olla.diff.modified")
                elif old_line:
                    old_text.stylize("olla.diff.removed")
                elif new_line:
                    new_text.stylize("olla.diff.added")
            
            diff_table.add_row(old_text, new_text)
        
        return Panel(
            diff_table,
            title=f"[olla.header]Code Changes: {filename}[/]",
            title_align="left",
            border_style="olla.table.border"
        )


class ProgressManager:
    """Manage progress bars and spinners."""
    
    def __init__(self, console: Console):
        self.console = console
        self._progress: Optional[Progress] = None
        self._live: Optional[Live] = None
    
    def create_progress(self, description: str = "Processing") -> Progress:
        """Create a progress bar."""
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=self.console,
            expand=True
        )
        return self._progress
    
    def create_spinner(self, description: str = "Working") -> Live:
        """Create a spinner for indefinite operations."""
        spinner_text = Text.assemble(
            ("⠋ ", "olla.primary"),
            (description, "olla.info")
        )
        self._live = Live(spinner_text, console=self.console, refresh_per_second=10)
        return self._live
    
    def stop_all(self):
        """Stop all progress indicators."""
        if self._progress:
            self._progress.stop()
        if self._live:
            self._live.stop()


class ExportManager:
    """Handle output export functionality."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def export_as_markdown(self, content: str, title: str = "Olla CLI Output") -> str:
        """Export content as Markdown."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markdown_content = f"""# {title}

*Generated by [Olla CLI](https://github.com/mahinuzzaman/ollama-cli) on {timestamp}*

---

{content}

---

*Powered by Olla CLI - Your AI Coding Assistant*
"""
        return markdown_content
    
    def export_as_html(self, content: str, title: str = "Olla CLI Output") -> str:
        """Export content as HTML with styling."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert markdown to HTML
        html_content = md_lib.markdown(content, extensions=['codehilite', 'tables', 'toc'])
        
        css_styles = """
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
                   line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 2rem; 
                   background: #0d1117; color: #c9d1d9; }
            .header { background: linear-gradient(90deg, #00d4ff, #a855f7); 
                      padding: 1rem; border-radius: 8px; margin-bottom: 2rem; }
            .header h1 { margin: 0; color: white; }
            .footer { text-align: center; margin-top: 2rem; color: #8b949e; 
                      border-top: 1px solid #30363d; padding-top: 1rem; }
            pre { background: #161b22; padding: 1rem; border-radius: 6px; 
                  border: 1px solid #30363d; overflow-x: auto; }
            code { background: #161b22; padding: 0.2rem 0.4rem; border-radius: 3px; 
                   font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; }
            table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
            th, td { border: 1px solid #30363d; padding: 0.75rem; text-align: left; }
            th { background: #21262d; font-weight: 600; }
            .timestamp { color: #8b949e; font-size: 0.9rem; }
        </style>
        """
        
        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {css_styles}
</head>
<body>
    <div class="header">
        <h1>🚀 {title}</h1>
        <div class="timestamp">Generated by Olla CLI on {timestamp}</div>
    </div>
    
    <div class="content">
        {html_content}
    </div>
    
    <div class="footer">
        <p>⚡ Powered by <strong>Olla CLI</strong> - Your AI Coding Assistant</p>
    </div>
</body>
</html>"""
        return full_html
    
    def copy_to_clipboard(self, content: str) -> bool:
        """Copy content to clipboard."""
        try:
            pyperclip.copy(content)
            return True
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
            return False
    
    def save_to_file(self, content: str, filepath: Path, format_type: OutputFormat) -> bool:
        """Save content to file with appropriate format."""
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == OutputFormat.HTML:
                content = self.export_as_html(content)
            elif format_type == OutputFormat.MARKDOWN:
                content = self.export_as_markdown(content)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save to file {filepath}: {e}")
            return False


class CollapsibleSection:
    """Create collapsible sections for detailed content."""
    
    def __init__(self, title: str, content: str, expanded: bool = False):
        self.title = title
        self.content = content
        self.expanded = expanded
    
    def render(self, console: Console) -> Panel:
        """Render collapsible section."""
        if self.expanded:
            display_content = self.content
            icon = "▼"
        else:
            # Show first few lines as preview
            lines = self.content.split('\n')
            preview = '\n'.join(lines[:3])
            if len(lines) > 3:
                preview += f"\n... ({len(lines) - 3} more lines)"
            display_content = preview
            icon = "▶"
        
        return Panel(
            display_content,
            title=f"[olla.header]{icon} {self.title}[/]",
            title_align="left",
            border_style="olla.table.border",
            expand=False
        )


class OutputFormatter:
    """Comprehensive output formatter for olla-cli."""
    
    def __init__(self, options: Optional[FormatOptions] = None):
        """Initialize the output formatter."""
        self.options = options or FormatOptions()
        
        # Setup console with theme
        theme = OllaThemes.get_theme(self.options.theme, self.options.custom_colors)
        
        self.console = Console(
            theme=theme,
            width=self.options.max_width,
            force_terminal=True,
            legacy_windows=False
        )
        
        self.progress_manager = ProgressManager(self.console)
        self.export_manager = ExportManager(self.console)
        self.highlighter = ReprHighlighter()
        
        # Load configuration
        try:
            self.config = Config()
        except Exception:
            self.config = {}
    
    def print_header(self, title: str, subtitle: str = "") -> None:
        """Print a branded header."""
        header_text = Text()
        header_text.append("🚀 ", style="olla.brand")
        header_text.append("Olla CLI", style="olla.brand")
        
        if subtitle:
            header_content = f"{title}\n{subtitle}"
        else:
            header_content = title
        
        panel = Panel(
            header_content,
            title=header_text,
            title_align="left",
            border_style="olla.primary",
            padding=(1, 2)
        )
        
        self.console.print(panel)
        self.console.print()
    
    def print_footer(self, include_branding: bool = True) -> None:
        """Print a footer with optional branding."""
        if include_branding:
            footer_text = Text.assemble(
                ("⚡ Powered by ", "olla.muted"),
                ("Olla CLI", "olla.brand"),
                (" - Your AI Coding Assistant", "olla.muted")
            )
            
            self.console.print()
            self.console.print(Rule(style="olla.muted"))
            self.console.print(Align.center(footer_text))
    
    def print_code(self, code: str, language: Optional[str] = None, 
                   filename: Optional[str] = None, title: str = "") -> None:
        """Print syntax-highlighted code."""
        if not self.options.syntax_highlight:
            self.console.print(Panel(code, title=title or "Code"))
            return
        
        syntax = SyntaxHighlighter.highlight_code(code, language, filename)
        
        if title:
            panel = Panel(syntax, title=f"[olla.header]{title}[/]", title_align="left")
            self.console.print(panel)
        else:
            self.console.print(syntax)
    
    def print_diff(self, old_code: str, new_code: str, filename: str = "code") -> None:
        """Print a visual diff."""
        diff_panel = DiffVisualizer.create_diff(old_code, new_code, filename)
        self.console.print(diff_panel)
    
    def print_markdown(self, content: str) -> None:
        """Print rendered Markdown content."""
        # Process code blocks for syntax highlighting
        processed_content = self._process_markdown_code_blocks(content)
        
        markdown = Markdown(processed_content, code_theme="monokai")
        self.console.print(markdown)
    
    def _process_markdown_code_blocks(self, content: str) -> str:
        """Process markdown code blocks for better highlighting."""
        # This is a simplified processor - in production, use a proper markdown parser
        return content
    
    def print_table(self, data: List[Dict[str, Any]], title: str = "") -> None:
        """Print a formatted table."""
        if not data:
            return
        
        headers = list(data[0].keys())
        
        table = Table(
            title=title,
            title_style="olla.header",
            header_style="olla.table.header",
            border_style="olla.table.border",
            show_lines=True
        )
        
        for header in headers:
            table.add_column(header, overflow="fold")
        
        for row in data:
            table.add_row(*[str(row.get(header, "")) for header in headers])
        
        self.console.print(table)
    
    def print_tree(self, data: Dict[str, Any], title: str = "Structure") -> None:
        """Print a tree structure."""
        tree = Tree(f"[olla.header]{title}[/]")
        self._build_tree(tree, data)
        self.console.print(tree)
    
    def _build_tree(self, tree: Tree, data: Dict[str, Any]) -> None:
        """Recursively build tree structure."""
        for key, value in data.items():
            if isinstance(value, dict):
                branch = tree.add(f"[olla.primary]{key}[/]")
                self._build_tree(branch, value)
            elif isinstance(value, list):
                branch = tree.add(f"[olla.secondary]{key}[/] ({len(value)} items)")
                for i, item in enumerate(value[:5]):  # Show first 5 items
                    branch.add(f"[olla.muted]{i}: {str(item)[:50]}[/]")
                if len(value) > 5:
                    branch.add(f"[olla.muted]... and {len(value) - 5} more[/]")
            else:
                tree.add(f"[olla.info]{key}[/]: {str(value)}")
    
    def print_success(self, message: str, details: str = "") -> None:
        """Print success message."""
        text = Text()
        text.append("✅ ", style="olla.success")
        text.append(message, style="olla.success")
        
        if details:
            text.append(f"\n{details}", style="olla.muted")
        
        self.console.print(text)
    
    def print_warning(self, message: str, details: str = "") -> None:
        """Print warning message."""
        text = Text()
        text.append("⚠️  ", style="olla.warning")
        text.append(message, style="olla.warning")
        
        if details:
            text.append(f"\n{details}", style="olla.muted")
        
        self.console.print(text)
    
    def print_error(self, message: str, details: str = "", suggestions: List[str] = None) -> None:
        """Print error message with suggestions."""
        text = Text()
        text.append("❌ ", style="olla.error")
        text.append(message, style="olla.error")
        
        if details:
            text.append(f"\n{details}", style="olla.muted")
        
        if suggestions:
            text.append("\n\nSuggestions:", style="olla.info")
            for suggestion in suggestions:
                text.append(f"\n• {suggestion}", style="olla.muted")
        
        self.console.print(Panel(text, border_style="olla.error", padding=(1, 2)))
    
    def print_info(self, message: str, details: str = "") -> None:
        """Print info message."""
        text = Text()
        text.append("ℹ️  ", style="olla.info")
        text.append(message, style="olla.info")
        
        if details:
            text.append(f"\n{details}", style="olla.muted")
        
        self.console.print(text)
    
    def create_progress(self, description: str = "Processing") -> Progress:
        """Create a progress bar."""
        return self.progress_manager.create_progress(description)
    
    def create_spinner(self, description: str = "Working") -> Live:
        """Create a spinner."""
        return self.progress_manager.create_spinner(description)
    
    def print_with_pager(self, content: str) -> None:
        """Print content with pager for long text."""
        if self.options.enable_pager and len(content.split('\n')) > 50:
            with self.console.pager():
                self.console.print(content)
        else:
            self.console.print(content)
    
    def export_output(self, content: str, filepath: Optional[Path] = None, 
                     format_type: OutputFormat = OutputFormat.MARKDOWN,
                     title: str = "Olla CLI Output") -> Optional[Path]:
        """Export output to file or clipboard."""
        if format_type == OutputFormat.CONSOLE and not filepath:
            # Copy to clipboard
            success = self.export_manager.copy_to_clipboard(content)
            if success:
                self.print_success("Output copied to clipboard")
            else:
                self.print_error("Failed to copy to clipboard")
            return None
        
        if not filepath:
            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext = "html" if format_type == OutputFormat.HTML else "md"
            filepath = Path.cwd() / f"olla_output_{timestamp}.{ext}"
        
        success = self.export_manager.save_to_file(content, filepath, format_type)
        
        if success:
            self.print_success(f"Output exported to: {filepath}")
            return filepath
        else:
            self.print_error(f"Failed to export to: {filepath}")
            return None
    
    def format_streaming_response(self, response_generator: Iterator[str], 
                                 title: str = "") -> str:
        """Format streaming response with progress indication."""
        content_parts = []
        
        if title:
            self.print_header(title)
        
        try:
            for chunk in response_generator:
                if chunk.strip():
                    self.console.print(chunk, end="")
                    content_parts.append(chunk)
            
            self.console.print()  # Final newline
            
        except KeyboardInterrupt:
            self.print_warning("\nResponse interrupted by user")
        except Exception as e:
            self.print_error(f"Error during streaming: {str(e)}")
        
        return ''.join(content_parts)
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Ask for user confirmation."""
        return Confirm.ask(message, default=default, console=self.console)
    
    def prompt_input(self, message: str, default: str = "") -> str:
        """Prompt for user input."""
        return Prompt.ask(message, default=default, console=self.console)
    
    def set_theme(self, theme_type: ThemeType, custom_colors: Optional[Dict[str, str]] = None) -> None:
        """Change the current theme."""
        self.options.theme = theme_type
        self.options.custom_colors = custom_colors
        
        # Recreate console with new theme
        theme = OllaThemes.get_theme(theme_type, custom_colors)
        self.console = Console(
            theme=theme,
            width=self.options.max_width,
            force_terminal=True,
            legacy_windows=False
        )
        
        # Update managers
        self.progress_manager = ProgressManager(self.console)
        self.export_manager = ExportManager(self.console)
    
    def get_terminal_size(self) -> Tuple[int, int]:
        """Get terminal size (width, height)."""
        return self.console.size