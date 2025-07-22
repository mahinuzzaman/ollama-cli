"""General helper utilities."""

import re
import traceback
from typing import Any, Optional


def format_error_message(error: Exception) -> str:
    """Format an error message for display."""
    error_type = type(error).__name__
    error_msg = str(error)
    
    if not error_msg:
        return error_type
    
    return f"{error_type}: {error_msg}"


def validate_temperature(temperature: float) -> bool:
    """Validate temperature parameter."""
    return 0.0 <= temperature <= 2.0


def validate_context_length(context_length: int) -> bool:
    """Validate context length parameter."""
    return context_length > 0


def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary."""
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_bytes(bytes_count: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f}{unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f}PB"


def get_stack_trace(error: Exception) -> str:
    """Get formatted stack trace from exception."""
    return ''.join(traceback.format_exception(type(error), error, error.__traceback__))


class TokenCounter:
    """Utility for estimating token counts."""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for text.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        # This varies by tokenizer but provides a reasonable approximation
        return len(text) // 4
    
    @staticmethod
    def estimate_tokens_precise(text: str) -> int:
        """More precise token estimation.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Split by whitespace and punctuation
        words = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        # Estimate tokens per word (accounting for subword tokenization)
        token_count = 0
        for word in words:
            if len(word) <= 3:
                token_count += 1
            elif len(word) <= 6:
                token_count += 2
            else:
                token_count += max(2, len(word) // 4)
        
        return token_count