"""Intelligent Tool Router for olla-cli."""

from typing import List, Dict, Any, Optional, Tuple
import asyncio
import logging

from .intent import IntentClassifier, Intent, IntentType
from .planner import ExecutionPlanner, ExecutionPlan
from ..mcp.registry import ToolRegistry
from ..mcp.tools import ToolInterface, ToolResult

logger = logging.getLogger('olla-cli.routing.router')


class ToolRouter:
    """Intelligent router that analyzes user requests and routes them to appropriate tools."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        self.intent_classifier = IntentClassifier()
        self.execution_planner = ExecutionPlanner()
        self.routing_stats = {
            'total_requests': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'intent_accuracy': {}
        }
    
    async def route_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> List[ToolResult]:
        """Route a user request to appropriate tools and return results."""
        self.routing_stats['total_requests'] += 1
        
        try:
            # Step 1: Classify the intent
            intent = self.intent_classifier.classify(user_input, context)
            logger.info(f"Classified intent: {intent.type.value} (confidence: {intent.confidence:.2f})")
            
            # Step 2: Find tools that can handle this intent
            available_tools = self.tool_registry.find_tools_for_intent(
                intent.type.value, 
                intent.confidence
            )
            
            # Special case: CODE_GENERATE with filename needs both code and file tools
            if intent.type.value == 'code_generate' and self._contains_filename(user_input):
                # Add filesystem write capability if not already present
                file_tools = self.tool_registry.find_tools_for_intent('file_write', intent.confidence)
                for tool, capability in file_tools:
                    if (tool, capability) not in available_tools:
                        available_tools.append((tool, capability))
            
            if not available_tools:
                logger.warning(f"No tools found for intent: {intent.type.value}")
                return [ToolResult(
                    success=False,
                    error=f"No tools available to handle: {user_input}",
                    data=None
                )]
            
            # Step 3: Create execution plan
            plan = await self.execution_planner.create_plan(intent, available_tools)
            logger.info(f"Created plan with {len(plan.steps)} steps")
            
            # Step 4: Execute the plan
            results = await self.execution_planner.execute_plan(plan)
            
            # Update statistics
            if any(r.success for r in results):
                self.routing_stats['successful_routes'] += 1
            else:
                self.routing_stats['failed_routes'] += 1
            
            # Track intent accuracy
            intent_key = intent.type.value
            if intent_key not in self.routing_stats['intent_accuracy']:
                self.routing_stats['intent_accuracy'][intent_key] = {'attempts': 0, 'successes': 0}
            
            self.routing_stats['intent_accuracy'][intent_key]['attempts'] += 1
            if any(r.success for r in results):
                self.routing_stats['intent_accuracy'][intent_key]['successes'] += 1
            
            return results
            
        except Exception as e:
            logger.error(f"Error routing request: {e}")
            self.routing_stats['failed_routes'] += 1
            return [ToolResult(
                success=False,
                error=f"Routing error: {str(e)}",
                data=None
            )]
    
    async def suggest_corrections(self, user_input: str, failed_results: List[ToolResult]) -> List[str]:
        """Suggest corrections when routing fails."""
        suggestions = []
        
        # Classify intent again to get more info
        intent = self.intent_classifier.classify(user_input)
        
        # Common suggestions based on intent type
        if intent.type == IntentType.UNKNOWN:
            suggestions.extend([
                "Try being more specific about what you want to do",
                "Use keywords like 'explain', 'generate', 'review', or 'create'",
                "Include file paths or code snippets if relevant"
            ])
        
        elif intent.type == IntentType.CODE_EXPLAIN and intent.confidence < 0.5:
            suggestions.extend([
                "Try: 'explain this code: <your code>'",
                "Or: 'explain file.py'",
                "Make sure to include the code or file path"
            ])
        
        elif intent.type == IntentType.FILE_READ:
            suggestions.extend([
                "Make sure the file path exists",
                "Try using absolute paths if relative paths don't work",
                "Check file permissions"
            ])
        
        # Check if we have tools but they failed
        available_tools = self.tool_registry.find_tools_for_intent(intent.type.value, 0.1)  # Lower threshold
        if available_tools:
            suggestions.append("The required tools are available but failed to execute")
            
            # Analyze failures
            for result in failed_results:
                if result.error:
                    if "not found" in result.error.lower():
                        suggestions.append("Check that the specified files or resources exist")
                    elif "permission" in result.error.lower():
                        suggestions.append("Check file permissions")
                    elif "connection" in result.error.lower():
                        suggestions.append("Check network connectivity or service availability")
        
        return suggestions
    
    def get_available_capabilities(self) -> Dict[str, List[Dict]]:
        """Get all available capabilities across tools."""
        return self.tool_registry.get_capabilities_summary()
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics."""
        stats = self.routing_stats.copy()
        
        # Calculate success rate
        total = stats['total_requests']
        if total > 0:
            stats['success_rate'] = stats['successful_routes'] / total
        else:
            stats['success_rate'] = 0.0
        
        # Calculate intent accuracy rates
        for intent_type, data in stats['intent_accuracy'].items():
            if data['attempts'] > 0:
                data['accuracy'] = data['successes'] / data['attempts']
            else:
                data['accuracy'] = 0.0
        
        return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the routing system."""
        health = {
            'router_status': 'healthy',
            'tool_registry': self.tool_registry.get_stats(),
            'tool_health': self.tool_registry.validate_tool_health(),
            'classifier_status': 'healthy',
            'planner_status': 'healthy'
        }
        
        # Check if we have essential tools
        essential_types = ['filesystem', 'code_analysis']
        for tool_type in essential_types:
            from ..mcp.tools import ToolType
            tools = self.tool_registry.get_tools_by_type(ToolType(tool_type))
            if not tools:
                health['router_status'] = 'degraded'
                health[f'missing_{tool_type}_tools'] = True
        
        # Test basic classification
        try:
            test_intent = self.intent_classifier.classify("explain this code")
            if test_intent.type == IntentType.UNKNOWN:
                health['classifier_status'] = 'degraded'
        except Exception as e:
            health['classifier_status'] = 'failed'
            health['classifier_error'] = str(e)
        
        return health
    
    async def debug_routing(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Debug routing for a specific input."""
        debug_info = {
            'user_input': user_input,
            'context': context
        }
        
        # Step 1: Intent classification
        intent = self.intent_classifier.classify(user_input, context)
        debug_info['intent'] = {
            'type': intent.type.value,
            'confidence': intent.confidence,
            'parameters': intent.parameters
        }
        
        # Step 2: Tool matching
        available_tools = self.tool_registry.find_tools_for_intent(
            intent.type.value,
            intent.confidence
        )
        
        # Special case: CODE_GENERATE with filename needs both code and file tools
        if intent.type.value == 'code_generate' and self._contains_filename(user_input):
            # Add filesystem write capability if not already present
            file_tools = self.tool_registry.find_tools_for_intent('file_write', intent.confidence)
            for tool, capability in file_tools:
                if (tool, capability) not in available_tools:
                    available_tools.append((tool, capability))
        debug_info['available_tools'] = [
            {
                'tool_name': tool.name,
                'capability_name': capability.name,
                'capability_type': capability.tool_type.value,
                'confidence_threshold': capability.confidence_threshold
            }
            for tool, capability in available_tools
        ]
        
        # Step 3: Plan creation (without execution)
        if available_tools:
            try:
                plan = await self.execution_planner.create_plan(intent, available_tools)
                debug_info['execution_plan'] = {
                    'total_steps': len(plan.steps),
                    'parallel_execution': plan.parallel_execution,
                    'steps': [
                        {
                            'id': step.id,
                            'tool_name': step.tool.name,
                            'capability_name': step.capability.name,
                            'parameters': step.parameters,
                            'dependencies': step.dependencies
                        }
                        for step in plan.steps
                    ]
                }
            except Exception as e:
                debug_info['plan_error'] = str(e)
        
        return debug_info
    
    def _contains_filename(self, text: str) -> bool:
        """Check if text contains a filename pattern."""
        import re
        filename_patterns = [
            r'[\w\-_.]+\.(py|js|ts|java|cpp|c|h|go|rs|php|rb|txt|md|json|yaml|yml|toml|html|css)',
            r'called\s+[\w\-_.]+\.(py|js|ts|java|cpp|c|h|go|rs|php|rb|txt|md|json|yaml|yml|toml|html|css)',
            r'named\s+[\w\-_.]+\.(py|js|ts|java|cpp|c|h|go|rs|php|rb|txt|md|json|yaml|yml|toml|html|css)',
            r'file\s+(called|named)\s+[\w\-_.]+\.',
        ]
        
        for pattern in filename_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False