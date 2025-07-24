"""Model Context Protocol (MCP) Layer for olla-cli.

This module provides the MCP interface for tool and external service integration,
similar to Claude CLI's architecture.
"""

from .protocol import MCPProtocol
from .server import MCPServer
from .client import MCPClient
from .tools import ToolInterface, ToolCapability, ToolResult
from .registry import ToolRegistry

__all__ = [
    'MCPProtocol',
    'MCPServer', 
    'MCPClient',
    'ToolInterface',
    'ToolCapability',
    'ToolResult',
    'ToolRegistry'
]