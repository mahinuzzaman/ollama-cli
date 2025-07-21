"""Logging configuration for Olla CLI."""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    verbose: bool = False
) -> logging.Logger:
    """Set up logging configuration for Olla CLI.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        verbose: Enable verbose logging
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('olla-cli')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if verbose:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Set console handler level based on verbose flag
    if verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        
        # File handler always uses detailed format
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_path}")
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    return logger


def get_default_log_file() -> str:
    """Get default log file path.
    
    Returns:
        Default log file path
    """
    # Use user's home directory for log file
    log_dir = Path.home() / '.olla-cli' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    return str(log_dir / 'olla-cli.log')


def configure_logging_from_config(config_dict: dict, verbose: bool = False) -> logging.Logger:
    """Configure logging from configuration dictionary.
    
    Args:
        config_dict: Configuration dictionary
        verbose: Enable verbose logging
        
    Returns:
        Configured logger instance
    """
    log_level = config_dict.get('log_level', 'INFO')
    log_file = config_dict.get('log_file')
    
    # Use default log file if logging is enabled but no file specified
    if config_dict.get('enable_logging', False) and not log_file:
        log_file = get_default_log_file()
    
    return setup_logging(level=log_level, log_file=log_file, verbose=verbose)


class LoggerMixin:
    """Mixin class to add logging capabilities to other classes."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger('olla-cli')