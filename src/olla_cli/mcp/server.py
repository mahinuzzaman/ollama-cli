"""MCP Server implementation for olla-cli."""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable

from .protocol import MCPProtocol, MCPMessage

logger = logging.getLogger('olla-cli.mcp.server')


class MCPServer:
    """MCP Server for handling tool communication."""
    
    def __init__(self, protocol: Optional[MCPProtocol] = None):
        self.protocol = protocol or MCPProtocol()
        self.is_running = False
        self.handlers: Dict[str, Callable] = {}
        
    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler."""
        self.handlers[message_type] = handler
        logger.debug(f"Registered handler for message type: {message_type}")
    
    async def start(self) -> None:
        """Start the MCP server."""
        if self.is_running:
            logger.warning("MCP Server is already running")
            return
        
        self.is_running = True
        logger.info("MCP Server started")
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("MCP Server stopped")
    
    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle incoming MCP message."""
        if not self.is_running:
            logger.warning("Server not running, ignoring message")
            return None
        
        handler = self.handlers.get(message.type)
        if handler:
            try:
                return await handler(message)
            except Exception as e:
                logger.error(f"Error handling message {message.type}: {e}")
                return MCPMessage(
                    type="error",
                    data={"error": str(e)},
                    message_id=message.message_id
                )
        else:
            logger.warning(f"No handler for message type: {message.type}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get server status."""
        return {
            'running': self.is_running,
            'handlers_count': len(self.handlers),
            'registered_types': list(self.handlers.keys())
        }