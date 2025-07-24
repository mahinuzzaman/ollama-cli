"""Execution Planning System for multi-step task orchestration."""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import logging

from .intent import Intent, IntentType
from ..mcp.tools import ToolInterface, ToolCapability, ToolResult

logger = logging.getLogger('olla-cli.routing.planner')


class StepStatus(Enum):
    """Status of an execution step."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionStep:
    """A single step in an execution plan."""
    id: str
    tool: ToolInterface
    capability: ToolCapability
    parameters: Dict[str, Any]
    status: StepStatus = StepStatus.PENDING
    result: Optional[ToolResult] = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    async def execute(self, context: Optional[Dict[str, Any]] = None) -> ToolResult:
        """Execute this step."""
        self.status = StepStatus.RUNNING
        
        try:
            # Substitute variables in parameters
            resolved_params = self._resolve_parameters(self.parameters, context or {})
            
            # Validate parameters
            if not await self.tool.validate_params(self.capability, resolved_params):
                raise ValueError(f"Invalid parameters for {self.capability.name}")
            
            # Execute the tool capability
            self.result = await self.tool.execute(self.capability.name, resolved_params)
            
            if self.result.success:
                self.status = StepStatus.COMPLETED
            else:
                self.status = StepStatus.FAILED
                self.error = self.result.error
                
            return self.result
            
        except Exception as e:
            self.status = StepStatus.FAILED
            self.error = str(e)
            self.result = ToolResult(success=False, error=str(e), data=None)
            logger.error(f"Step {self.id} failed: {e}")
            return self.result
    
    def can_retry(self) -> bool:
        """Check if this step can be retried."""
        return self.status == StepStatus.FAILED and self.retry_count < self.max_retries
    
    def should_skip(self) -> bool:
        """Check if this step should be skipped."""
        return self.status == StepStatus.SKIPPED
    
    def _resolve_parameters(self, params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve parameter variables using context."""
        resolved = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Extract variable name
                var_name = value[2:-1]
                resolved_value = context.get(var_name, value)
                logger.debug(f"Resolving {var_name}: found={var_name in context}, value_preview={str(resolved_value)[:100]}")
                resolved[key] = resolved_value
            else:
                resolved[key] = value
        return resolved


@dataclass 
class ExecutionPlan:
    """A plan for executing multiple steps to fulfill an intent."""
    id: str
    intent: Intent
    steps: List[ExecutionStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    parallel_execution: bool = False
    
    def add_step(self, step: ExecutionStep) -> None:
        """Add a step to the plan."""
        self.steps.append(step)
    
    def get_next_steps(self) -> List[ExecutionStep]:
        """Get steps that are ready to execute."""
        ready_steps = []
        completed_step_ids = {step.id for step in self.steps if step.status == StepStatus.COMPLETED}
        
        for step in self.steps:
            if step.status == StepStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_met = all(dep_id in completed_step_ids for dep_id in step.dependencies)
                if dependencies_met:
                    ready_steps.append(step)
        
        return ready_steps
    
    def is_complete(self) -> bool:
        """Check if the plan is complete."""
        return all(step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED] for step in self.steps)
    
    def has_failures(self) -> bool:
        """Check if any steps have failed."""
        return any(step.status == StepStatus.FAILED for step in self.steps)
    
    def get_results(self) -> List[ToolResult]:
        """Get results from all completed steps."""
        return [step.result for step in self.steps if step.result is not None]


class ExecutionPlanner:
    """Creates and manages execution plans for intents."""
    
    def __init__(self):
        self.active_plans: Dict[str, ExecutionPlan] = {}
        
    async def create_plan(self, intent: Intent, available_tools: List[tuple]) -> ExecutionPlan:
        """Create an execution plan for the given intent."""
        import uuid
        plan_id = str(uuid.uuid4())
        
        plan = ExecutionPlan(id=plan_id, intent=intent)
        
        # Simple single-step plan for most intents
        if len(available_tools) == 1:
            tool, capability = available_tools[0]
            step = ExecutionStep(
                id=f"{plan_id}_001",
                tool=tool,
                capability=capability,
                parameters=self._prepare_parameters(intent, capability)
            )
            plan.add_step(step)
        
        # Multi-step plan for complex intents
        elif intent.type == IntentType.TASK_COMPLEX:
            plan = await self._create_complex_plan(intent, available_tools, plan_id)
        
        # File-based operations might need multiple steps
        elif intent.type in [IntentType.CODE_EXPLAIN, IntentType.CODE_REVIEW] and 'file_path' in intent.parameters:
            plan = await self._create_file_based_plan(intent, available_tools, plan_id)
        
        # Code generation with filename -> create file with generated code
        elif intent.type == IntentType.CODE_GENERATE and self._contains_filename(intent.raw_input):
            # For this special case, we need both code generation and file writing capabilities
            # Look for both in the available tools, and if not found, we'll create what we can
            plan = await self._create_code_to_file_plan(intent, available_tools, plan_id)
        
        # Default: create steps only for relevant tools 
        else:
            # Filter tools based on intent type to avoid irrelevant tool execution
            relevant_tools = self._filter_relevant_tools(intent, available_tools)
            
            for i, (tool, capability) in enumerate(relevant_tools):
                step = ExecutionStep(
                    id=f"{plan_id}_{i+1:03d}",
                    tool=tool,
                    capability=capability,
                    parameters=self._prepare_parameters(intent, capability)
                )
                plan.add_step(step)
            
            # Only use parallel execution if we have multiple relevant tools
            plan.parallel_execution = len(relevant_tools) > 1
        
        self.active_plans[plan_id] = plan
        return plan
    
    async def execute_plan(self, plan: ExecutionPlan) -> List[ToolResult]:
        """Execute a plan and return results."""
        results = []
        
        if plan.parallel_execution:
            # Execute all steps in parallel
            tasks = []
            for step in plan.steps:
                tasks.append(step.execute())
            
            step_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for step, result in zip(plan.steps, step_results):
                if isinstance(result, Exception):
                    step.status = StepStatus.FAILED
                    step.error = str(result)
                    step.result = ToolResult(success=False, error=str(result), data=None)
                results.append(step.result)
        
        else:
            # Execute steps sequentially, respecting dependencies
            while not plan.is_complete():
                next_steps = plan.get_next_steps()
                
                if not next_steps:
                    # No more steps can be executed
                    if plan.has_failures():
                        # Try to retry failed steps
                        retry_steps = [step for step in plan.steps if step.can_retry()]
                        if retry_steps:
                            for step in retry_steps:
                                step.retry_count += 1
                                step.status = StepStatus.PENDING
                        else:
                            break  # No more retries possible
                    else:
                        break  # All remaining steps are blocked
                
                # Execute next steps
                for step in next_steps:
                    logger.debug(f"Executing step {step.id} with {step.capability.name}")
                    result = await step.execute(plan.context)
                    results.append(result)
                    
                    logger.debug(f"Step {step.id} result: success={result.success}, has_data={bool(result.data)}, data_repr={repr(result.data)[:200]}")
                    
                    # Update context with results for subsequent steps
                    if result.success and result.data:
                        context_key = f"step_{step.id}_result"
                        plan.context[context_key] = result.data
                        logger.debug(f"Added to context: {context_key} = {str(result.data)[:100]}...")
                    else:
                        logger.debug(f"NOT adding to context: success={result.success}, data_type={type(result.data)}, error={result.error}")
        
        # Clean up completed plan
        if plan.id in self.active_plans:
            del self.active_plans[plan.id]
        
        return results
    
    async def _create_complex_plan(self, intent: Intent, available_tools: List[tuple], plan_id: str) -> ExecutionPlan:
        """Create a multi-step plan for complex tasks."""
        plan = ExecutionPlan(id=plan_id, intent=intent)
        
        # Example: Complex task might involve file operations + code analysis
        file_tools = [(tool, cap) for tool, cap in available_tools if cap.tool_type.value == 'filesystem']
        code_tools = [(tool, cap) for tool, cap in available_tools if cap.tool_type.value == 'code_analysis']
        
        step_counter = 1
        
        # Step 1: Read files if needed
        if file_tools and 'file_path' in intent.parameters:
            tool, capability = file_tools[0]  # Take first file tool
            read_step = ExecutionStep(
                id=f"{plan_id}_{step_counter:03d}",
                tool=tool,
                capability=capability,
                parameters={'file_path': intent.parameters['file_path']}
            )
            plan.add_step(read_step)
            step_counter += 1
        
        # Step 2: Analyze code (depends on file read)
        if code_tools:
            tool, capability = code_tools[0]  # Take first code tool
            analysis_step = ExecutionStep(
                id=f"{plan_id}_{step_counter:03d}",
                tool=tool,
                capability=capability,
                parameters=self._prepare_parameters(intent, capability),
                dependencies=[f"{plan_id}_001"] if step_counter > 1 else []
            )
            plan.add_step(analysis_step)
        
        return plan
    
    async def _create_file_based_plan(self, intent: Intent, available_tools: List[tuple], plan_id: str) -> ExecutionPlan:
        """Create a plan that starts with file reading."""
        plan = ExecutionPlan(id=plan_id, intent=intent)
        
        # Find file system and code analysis tools
        file_tools = [(tool, cap) for tool, cap in available_tools 
                     if cap.tool_type.value == 'filesystem' and cap.name == 'read_file']
        analysis_tools = [(tool, cap) for tool, cap in available_tools 
                         if cap.tool_type.value == 'code_analysis']
        
        if file_tools and 'file_path' in intent.parameters:
            # Step 1: Read the file
            file_tool, file_capability = file_tools[0]
            read_step = ExecutionStep(
                id=f"{plan_id}_001",
                tool=file_tool,
                capability=file_capability,
                parameters={'file_path': intent.parameters['file_path']}
            )
            plan.add_step(read_step)
            
            # Step 2: Analyze the file content
            if analysis_tools:
                analysis_tool, analysis_capability = analysis_tools[0]
                analysis_step = ExecutionStep(
                    id=f"{plan_id}_002",
                    tool=analysis_tool, 
                    capability=analysis_capability,
                    parameters=self._prepare_parameters(intent, analysis_capability),
                    dependencies=[f"{plan_id}_001"]
                )
                plan.add_step(analysis_step)
        
        return plan
    
    def _prepare_parameters(self, intent: Intent, capability: ToolCapability) -> Dict[str, Any]:
        """Prepare parameters for a tool capability based on intent."""
        params = {}
        
        # Copy relevant parameters from intent
        for param_name in capability.required_params:
            if param_name in intent.parameters:
                params[param_name] = intent.parameters[param_name]
        
        # Add defaults based on capability type
        if capability.name == 'explain_code':
            params.setdefault('detail_level', 'normal')
            if 'code' not in params and 'raw_input' in intent.__dict__:
                # Extract code from raw input if not already present
                params['code'] = intent.raw_input
        
        elif capability.name == 'review_code':
            params.setdefault('focus', intent.parameters.get('focus', 'all'))
            if 'code' not in params and 'raw_input' in intent.__dict__:
                params['code'] = intent.raw_input
        
        elif capability.name == 'generate_code':
            params.setdefault('language', intent.parameters.get('language', 'python'))
            if 'description' not in params:
                params['description'] = intent.raw_input
        
        return params
    
    def _filter_relevant_tools(self, intent: Intent, available_tools: List[tuple]) -> List[tuple]:
        """Filter tools based on intent type to avoid irrelevant executions."""
        from .intent import IntentType
        
        # Define which tool types are relevant for each intent type
        intent_tool_mapping = {
            IntentType.CODE_EXPLAIN: ['code_analysis'],
            IntentType.CODE_REVIEW: ['code_analysis'],
            IntentType.CODE_GENERATE: ['code_analysis'],
            IntentType.CODE_REFACTOR: ['code_analysis'],
            IntentType.CODE_DEBUG: ['code_analysis'],
            IntentType.FILE_READ: ['filesystem'],
            IntentType.FILE_WRITE: ['filesystem'],
            IntentType.FILE_LIST: ['filesystem'],
            IntentType.WEB_SEARCH: ['web'],
            IntentType.WEB_FETCH: ['web'],
            IntentType.TASK_COMPLEX: ['filesystem', 'code_analysis', 'web'],  # May need multiple tools
        }
        
        relevant_tool_types = intent_tool_mapping.get(intent.type, ['code_analysis'])  # Default to code analysis
        
        # Filter tools based on relevant types
        filtered_tools = []
        for tool, capability in available_tools:
            tool_type = capability.tool_type.value if hasattr(capability.tool_type, 'value') else str(capability.tool_type)
            if tool_type in relevant_tool_types:
                filtered_tools.append((tool, capability))
        
        # If no relevant tools found, return the first available tool to avoid empty plans
        if not filtered_tools and available_tools:
            filtered_tools = [available_tools[0]]
        
        return filtered_tools
    
    def _contains_filename(self, text: str) -> bool:
        """Check if text contains a filename pattern."""
        import re
        # Look for common filename patterns
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
    
    def _extract_filename(self, text: str) -> Optional[str]:
        """Extract filename from text."""
        import re
        patterns = [
            r'([\w\-_.]+\.(py|js|ts|java|cpp|c|h|go|rs|php|rb|txt|md|json|yaml|yml|toml|html|css))',
            r'(?:called|named)\s+([\w\-_.]+\.(py|js|ts|java|cpp|c|h|go|rs|php|rb|txt|md|json|yaml|yml|toml|html|css))',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    async def _create_code_to_file_plan(self, intent: Intent, available_tools: List[tuple], plan_id: str) -> ExecutionPlan:
        """Create a plan that generates code and saves it to a file."""
        plan = ExecutionPlan(id=plan_id, intent=intent)
        
        # Find code analysis and filesystem tools
        code_tools = [(tool, cap) for tool, cap in available_tools 
                     if cap.tool_type.value == 'code_analysis' and cap.name == 'generate_code']
        file_tools = [(tool, cap) for tool, cap in available_tools 
                     if cap.tool_type.value == 'filesystem' and cap.name == 'write_file']
        
        filename = self._extract_filename(intent.raw_input)
        
        # Step 1: Generate code
        if code_tools:
            tool, capability = code_tools[0]
            generate_step = ExecutionStep(
                id=f"{plan_id}_001",
                tool=tool,
                capability=capability,
                parameters=self._prepare_parameters(intent, capability)
            )
            plan.add_step(generate_step)
        
        # Step 2: Save to file (depends on code generation)
        if file_tools and filename:
            tool, capability = file_tools[0]
            save_step = ExecutionStep(
                id=f"{plan_id}_002",
                tool=tool,
                capability=capability,
                parameters={
                    'file_path': filename,
                    'content': '${step_' + f"{plan_id}_001" + '_result}'  # Reference to previous step result
                },
                dependencies=[f"{plan_id}_001"]
            )
            plan.add_step(save_step)
        
        return plan
    
    def get_plan_status(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an execution plan."""
        if plan_id not in self.active_plans:
            return None
        
        plan = self.active_plans[plan_id]
        
        return {
            'id': plan.id,
            'intent_type': plan.intent.type.value,
            'total_steps': len(plan.steps),
            'completed_steps': len([s for s in plan.steps if s.status == StepStatus.COMPLETED]),
            'failed_steps': len([s for s in plan.steps if s.status == StepStatus.FAILED]),
            'is_complete': plan.is_complete(),
            'has_failures': plan.has_failures()
        }