"""Configuration management for Olla CLI."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration class for Olla CLI."""
    
    def __init__(self):
        self.config_dir = Path.home() / ".olla-cli"
        self.config_file = self.config_dir / "config.yaml"
        self.config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default config."""
        if not self.config_file.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise RuntimeError(f"Failed to load config file: {e}")
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        default_config = {
            "model": "codellama",
            "temperature": 0.7,
            "context_length": 4096,
            "api_url": "http://localhost:11434",
            "output": {
                "theme": "dark",
                "syntax_highlight": True,
                "show_line_numbers": True,
                "wrap_text": True,
                "show_progress": True,
                "enable_pager": True,
                "max_width": None,
                "custom_colors": {}
            }
        }
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to create config file: {e}")
        
        return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config_data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and save to file."""
        self.config_data[key] = value
        self._save_config()
    
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save config file: {e}")
    
    def show(self) -> Dict[str, Any]:
        """Return current configuration."""
        return self.config_data.copy()
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config_data = self._create_default_config()