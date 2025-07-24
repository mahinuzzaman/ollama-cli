"""Model Context Protocol implementation for olla-cli."""

import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger('olla-cli.mcp')


class MessageType(Enum):
    """MCP message types."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


@dataclass
class MCPMessage:
    """Base MCP message structure."""
    id: str
    type: MessageType
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        data = asdict(self)
        data['type'] = self.type.value
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod 
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPMessage':
        """Create message from dictionary."""
        data['type'] = MessageType(data['type'])
        return cls(**data)


class MCPProtocol:
    """Model Context Protocol handler."""
    
    def __init__(self):
        self.handlers: Dict[str, callable] = {}
        self.middleware: List[callable] = []
        
    def register_handler(self, method: str, handler: callable) -> None:
        """Register a method handler."""
        self.handlers[method] = handler
        logger.debug(f"Registered handler for method: {method}")
        
    def add_middleware(self, middleware: callable) -> None:
        """Add middleware function."""
        self.middleware.append(middleware)
        
    async def handle_message(self, message: MCPMessage) -> Optional[MCPMessage]:
        """Handle incoming MCP message."""
        try:
            # Apply middleware
            for middleware in self.middleware:
                message = await self._run_middleware(middleware, message)
                if message is None:
                    return None
                    
            # Handle the message
            if message.method in self.handlers:
                handler = self.handlers[message.method]
                result = await self._run_handler(handler, message)
                
                return MCPMessage(
                    id=message.id,
                    type=MessageType.RESPONSE,
                    result=result
                )
            else:
                return MCPMessage(
                    id=message.id,
                    type=MessageType.ERROR,
                    error={
                        "code": -32601,
                        "message": f"Method not found: {message.method}"
                    }
                )
                
        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            return MCPMessage(
                id=message.id,
                type=MessageType.ERROR,
                error={
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            )
    
    async def _run_middleware(self, middleware: callable, message: MCPMessage) -> Optional[MCPMessage]:
        """Run middleware function."""
        if asyncio.iscoroutinefunction(middleware):
            return await middleware(message)
        else:
            return middleware(message)
            
    async def _run_handler(self, handler: callable, message: MCPMessage) -> Any:
        """Run message handler."""
        if asyncio.iscoroutinefunction(handler):
            return await handler(message.params or {})
        else:
            return handler(message.params or {})
    
    def create_request(self, method: str, params: Optional[Dict[str, Any]] = None, message_id: Optional[str] = None) -> MCPMessage:
        """Create a request message."""
        if message_id is None:
            import uuid
            message_id = str(uuid.uuid4())
            
        return MCPMessage(
            id=message_id,
            type=MessageType.REQUEST,
            method=method,
            params=params
        )
    
    def create_notification(self, method: str, params: Optional[Dict[str, Any]] = None) -> MCPMessage:
        """Create a notification message."""
        import uuid
        return MCPMessage(
            id=str(uuid.uuid4()),
            type=MessageType.NOTIFICATION,
            method=method,
            params=params
        )