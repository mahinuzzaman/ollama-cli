"""MCP Client implementation for olla-cli."""

import asyncio
import logging
from typing import Dict, Any, Optional, List

from .protocol import MCPProtocol, MCPMessage

logger = logging.getLogger('olla-cli.mcp.client')


class MCPClient:
    """MCP Client for communicating with tools and services."""
    
    def __init__(self, protocol: Optional[MCPProtocol] = None):
        self.protocol = protocol or MCPProtocol()
        self.is_connected = False
        
    async def connect(self) -> None:
        """Connect to MCP services."""
        if self.is_connected:
            logger.warning("MCP Client is already connected")
            return
        
        self.is_connected = True
        logger.info("MCP Client connected")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP services."""
        if not self.is_connected:
            return
        
        self.is_connected = False
        logger.info("MCP Client disconnected")
    
    async def send_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Send a message and wait for response."""
        if not self.is_connected:
            logger.warning("Client not connected, cannot send message")
            return None
        
        try:
            return await self.protocol.handle_message(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return MCPMessage(
                type="error",
                data={"error": str(e)},
                message_id=message.message_id
            )
    
    async def call_tool(self, tool_name: str, capability: str, parameters: Dict[str, Any]) -> Optional[MCPMessage]:
        """Call a tool capability."""
        message = MCPMessage(
            type="tool_call",
            data={
                "tool": tool_name,
                "capability": capability,
                "parameters": parameters
            }
        )
        
        return await self.send_message(message)
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status."""
        return {
            'connected': self.is_connected,
            'protocol_version': getattr(self.protocol, 'version', '1.0')
        }