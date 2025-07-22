"""Factory for creating OutputFormatter instances with configuration."""

from typing import Optional
from ..config import Config
from .output_formatter import OutputFormatter, FormatOptions, ThemeType, OutputFormat


class FormatterFactory:
    """Factory class for creating OutputFormatter instances."""
    
    @staticmethod
    def create_formatter(config: Optional[Config] = None, 
                        theme_override: Optional[str] = None,
                        **kwargs) -> OutputFormatter:
        """Create an OutputFormatter with configuration.
        
        Args:
            config: Configuration object
            theme_override: Override theme setting
            **kwargs: Additional options to override
            
        Returns:
            Configured OutputFormatter instance
        """
        if config is None:
            config = Config()
        
        # Get output configuration
        output_config = config.get('output', {})
        
        # Determine theme
        theme_name = theme_override or output_config.get('theme', 'dark')
        theme_map = {
            'dark': ThemeType.DARK,
            'light': ThemeType.LIGHT,
            'auto': ThemeType.AUTO,
            'custom': ThemeType.CUSTOM
        }
        theme_type = theme_map.get(theme_name.lower(), ThemeType.DARK)
        
        # Create format options
        options = FormatOptions(
            theme=theme_type,
            syntax_highlight=output_config.get('syntax_highlight', True),
            show_line_numbers=output_config.get('show_line_numbers', True),
            wrap_text=output_config.get('wrap_text', True),
            show_progress=output_config.get('show_progress', True),
            enable_pager=output_config.get('enable_pager', True),
            max_width=output_config.get('max_width'),
            custom_colors=output_config.get('custom_colors', {})
        )
        
        # Override with any provided kwargs
        for key, value in kwargs.items():
            if hasattr(options, key):
                setattr(options, key, value)
        
        return OutputFormatter(options)
    
    @staticmethod
    def create_export_formatter(export_format: str, config: Optional[Config] = None) -> OutputFormatter:
        """Create formatter optimized for export.
        
        Args:
            export_format: Export format ('markdown', 'html', 'plain')
            config: Configuration object
            
        Returns:
            OutputFormatter configured for export
        """
        format_map = {
            'markdown': OutputFormat.MARKDOWN,
            'html': OutputFormat.HTML,
            'plain': OutputFormat.PLAIN,
            'json': OutputFormat.JSON
        }
        
        export_type = format_map.get(export_format.lower(), OutputFormat.MARKDOWN)
        
        # Create formatter with export-optimized settings
        return FormatterFactory.create_formatter(
            config=config,
            export_format=export_type,
            enable_pager=False,  # No pager for export
            show_progress=False,  # No progress for export
        )