"""Tool Registry for managing and discovering MCP tools."""

from typing import Dict, List, Optional, Set
from .tools import ToolInterface, ToolCapability, ToolType
import logging

logger = logging.getLogger('olla-cli.mcp.registry')


class ToolRegistry:
    """Registry for managing MCP tools and their capabilities."""
    
    def __init__(self):
        self.tools: Dict[str, ToolInterface] = {}
        self.capabilities: Dict[str, List[ToolCapability]] = {}
        self.type_index: Dict[ToolType, List[str]] = {}
        
    def register_tool(self, tool: ToolInterface) -> None:
        """Register a tool with the registry."""
        self.tools[tool.name] = tool
        
        # Index capabilities
        capabilities = tool.get_capabilities()
        self.capabilities[tool.name] = capabilities
        
        # Index by type
        for capability in capabilities:
            if capability.tool_type not in self.type_index:
                self.type_index[capability.tool_type] = []
            if tool.name not in self.type_index[capability.tool_type]:
                self.type_index[capability.tool_type].append(tool.name)
                
        logger.info(f"Registered tool: {tool.name} with {len(capabilities)} capabilities")
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool from the registry."""
        if tool_name not in self.tools:
            return False
            
        # Remove from tools
        del self.tools[tool_name]
        
        # Remove from capabilities
        if tool_name in self.capabilities:
            del self.capabilities[tool_name]
        
        # Remove from type index
        for tool_type, tools in self.type_index.items():
            if tool_name in tools:
                tools.remove(tool_name)
                
        logger.info(f"Unregistered tool: {tool_name}")
        return True
    
    def get_tool(self, tool_name: str) -> Optional[ToolInterface]:
        """Get a tool by name."""
        return self.tools.get(tool_name)
    
    def get_tools_by_type(self, tool_type: ToolType) -> List[ToolInterface]:
        """Get all tools of a specific type."""
        tool_names = self.type_index.get(tool_type, [])
        return [self.tools[name] for name in tool_names if name in self.tools]
    
    def get_all_tools(self) -> List[ToolInterface]:
        """Get all registered tools."""
        return list(self.tools.values())
    
    def find_tools_for_intent(self, intent: str, confidence: float) -> List[tuple]:
        """Find tools that can handle the given intent.
        
        Returns:
            List of (tool, capability) tuples
        """
        matches = []
        
        for tool in self.tools.values():
            capability = tool.can_handle(intent, confidence)
            if capability:
                matches.append((tool, capability))
                
        # Sort by confidence (higher first)
        matches.sort(key=lambda x: x[1].confidence_threshold, reverse=True)
        return matches
    
    def get_capabilities_summary(self) -> Dict[str, List[Dict]]:
        """Get a summary of all capabilities by tool."""
        summary = {}
        for tool_name, capabilities in self.capabilities.items():
            summary[tool_name] = [
                {
                    'name': cap.name,
                    'description': cap.description,
                    'type': cap.tool_type.value,
                    'parameters': cap.parameters
                }
                for cap in capabilities
            ]
        return summary
    
    def validate_tool_health(self) -> Dict[str, bool]:
        """Validate that all registered tools are healthy."""
        health_status = {}
        
        for tool_name, tool in self.tools.items():
            try:
                # Basic health check - ensure tool has capabilities
                capabilities = tool.get_capabilities()
                health_status[tool_name] = len(capabilities) > 0
            except Exception as e:
                logger.error(f"Health check failed for tool {tool_name}: {e}")
                health_status[tool_name] = False
                
        return health_status
    
    def discover_tools(self) -> List[str]:
        """Discover and auto-register available tools."""
        discovered = []
        
        try:
            # Auto-register built-in tools
            from .tools import FileSystemTool, CodeAnalysisTool, WebTool
            
            builtin_tools = [
                FileSystemTool(),
                CodeAnalysisTool(), 
                WebTool()
            ]
            
            for tool in builtin_tools:
                if tool.name not in self.tools:
                    self.register_tool(tool)
                    discovered.append(tool.name)
                    
        except Exception as e:
            logger.error(f"Error discovering tools: {e}")
            
        return discovered
    
    def get_stats(self) -> Dict[str, int]:
        """Get registry statistics."""
        total_capabilities = sum(len(caps) for caps in self.capabilities.values())
        
        return {
            'total_tools': len(self.tools),
            'total_capabilities': total_capabilities,
            'types_covered': len(self.type_index),
            'healthy_tools': sum(1 for healthy in self.validate_tool_health().values() if healthy)
        }