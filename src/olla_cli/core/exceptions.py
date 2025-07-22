"""Custom exceptions for Olla CLI and Ollama integration."""


class OllaCliError(Exception):
    """Base exception for Olla CLI."""
    pass


class OllamaConnectionError(OllaCliError):
    """Raised when unable to connect to Ollama server."""
    pass


class OllamaServerError(OllaCliError):
    """Raised when Ollama server returns an error."""
    pass


class ModelNotFoundError(OllaCliError):
    """Raised when requested model is not available."""
    pass


class ModelPullError(OllaCliError):
    """Raised when model pull operation fails."""
    pass


class InvalidModelError(OllaCliError):
    """Raised when model configuration is invalid."""
    pass


class ContextLimitExceededError(OllaCliError):
    """Raised when input exceeds model's context limit."""
    pass


class StreamingError(OllaCliError):
    """Raised when streaming response fails."""
    pass


class ConfigurationError(OllaCliError):
    """Raised when configuration is invalid."""
    pass


class TimeoutError(OllaCliError):
    """Raised when operation times out."""
    pass