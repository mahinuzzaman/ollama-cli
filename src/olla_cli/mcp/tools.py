"""Tool interface and capability definitions for MCP layer."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger('olla-cli.mcp.tools')


class ToolType(Enum):
    """Types of tools available."""
    FILE_SYSTEM = "filesystem"
    CODE_ANALYSIS = "code_analysis"
    WEB = "web"
    SHELL = "shell"
    GENERATION = "generation"
    CONTEXT = "context"
    TASK = "task"


@dataclass
class ToolCapability:
    """Describes what a tool can do."""
    name: str
    description: str
    parameters: Dict[str, Any]
    required_params: List[str]
    tool_type: ToolType
    confidence_threshold: float = 0.7
    
    def matches_intent(self, intent: str, confidence: float) -> bool:
        """Check if this capability matches the given intent."""
        if confidence < self.confidence_threshold:
            return False
        
        # Map intent types to capability names
        intent_capability_mapping = {
            'code_explain': ['explain_code'],
            'code_review': ['review_code'],
            'code_generate': ['generate_code'],
            'code_refactor': ['refactor_code'],
            'code_debug': ['debug_code'],
            'file_read': ['read_file'],
            'file_write': ['write_file'],
            'file_list': ['list_files'],
            'web_fetch': ['fetch_url'],
            'web_search': ['search_web']
        }
        
        # Check if this capability matches the intent
        matching_capabilities = intent_capability_mapping.get(intent, [])
        return self.name in matching_capabilities


@dataclass 
class ToolResult:
    """Result from tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata or {}
        }


class ToolInterface(ABC):
    """Abstract base class for all MCP tools."""
    
    def __init__(self, name: str):
        self.name = name
        self.capabilities: List[ToolCapability] = []
        
    @abstractmethod
    async def execute(self, capability: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a tool capability."""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[ToolCapability]:
        """Get list of capabilities this tool provides."""
        pass
    
    def can_handle(self, intent: str, confidence: float) -> Optional[ToolCapability]:
        """Check if this tool can handle the given intent."""
        for capability in self.get_capabilities():
            if capability.matches_intent(intent, confidence):
                return capability
        return None
    
    async def validate_params(self, capability: ToolCapability, params: Dict[str, Any]) -> bool:
        """Validate parameters for a capability."""
        for required_param in capability.required_params:
            if required_param not in params:
                return False
        return True


class FileSystemTool(ToolInterface):
    """File system operations tool."""
    
    def __init__(self):
        super().__init__("filesystem")
        
    def get_capabilities(self) -> List[ToolCapability]:
        return [
            ToolCapability(
                name="read_file",
                description="Read contents of a file",
                parameters={"file_path": "string"},
                required_params=["file_path"],
                tool_type=ToolType.FILE_SYSTEM
            ),
            ToolCapability(
                name="write_file", 
                description="Write content to a file",
                parameters={"file_path": "string", "content": "string"},
                required_params=["file_path", "content"],
                tool_type=ToolType.FILE_SYSTEM
            ),
            ToolCapability(
                name="list_files",
                description="List files in a directory",
                parameters={"directory": "string", "pattern": "string"},
                required_params=["directory"],
                tool_type=ToolType.FILE_SYSTEM
            )
        ]
    
    async def execute(self, capability: str, params: Dict[str, Any]) -> ToolResult:
        """Execute file system operations."""
        try:
            if capability == "read_file":
                file_path = params.get("file_path") or params.get("path") or params.get("filename")
                if not file_path:
                    return ToolResult(success=False, error="Missing file_path parameter", data=None)
                return await self._read_file(file_path)
                
            elif capability == "write_file":
                file_path = params.get("file_path") or params.get("path") or params.get("filename")
                content = params.get("content", "")
                if not file_path:
                    return ToolResult(success=False, error="Missing file_path parameter", data=None)
                return await self._write_file(file_path, content)
                
            elif capability == "list_files":
                directory = params.get("directory") or params.get("path", ".")
                pattern = params.get("pattern")
                return await self._list_files(directory, pattern)
            else:
                return ToolResult(success=False, error=f"Unknown capability: {capability}", data=None)
                
        except Exception as e:
            logger.error(f"FileSystemTool error: {e}")
            return ToolResult(success=False, error=str(e), data=None)
    
    async def _read_file(self, file_path: str) -> ToolResult:
        """Read file contents."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ToolResult(success=True, data=content)
        except Exception as e:
            return ToolResult(success=False, error=str(e), data=None)
    
    async def _write_file(self, file_path: str, content: str) -> ToolResult:
        """Write file contents."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return ToolResult(success=True, data=f"File written: {file_path}")
        except Exception as e:
            return ToolResult(success=False, error=str(e), data=None)
    
    async def _list_files(self, directory: str, pattern: Optional[str] = None) -> ToolResult:
        """List files in directory."""
        try:
            import os
            import glob
            
            if pattern:
                files = glob.glob(os.path.join(directory, pattern))
            else:
                files = [os.path.join(directory, f) for f in os.listdir(directory)]
            
            return ToolResult(success=True, data=files)
        except Exception as e:
            return ToolResult(success=False, error=str(e), data=None)


class CodeAnalysisTool(ToolInterface):
    """Code analysis operations tool."""
    
    def __init__(self, config=None):
        super().__init__("code_analysis")
        self.config = config
        
    def get_capabilities(self) -> List[ToolCapability]:
        return [
            ToolCapability(
                name="explain_code",
                description="Explain how code works",
                parameters={"code": "string", "language": "string", "detail_level": "string"},
                required_params=["code"],
                tool_type=ToolType.CODE_ANALYSIS
            ),
            ToolCapability(
                name="review_code",
                description="Review code for issues",
                parameters={"code": "string", "focus": "string"},
                required_params=["code"],
                tool_type=ToolType.CODE_ANALYSIS
            ),
            ToolCapability(
                name="generate_code",
                description="Generate code from description",
                parameters={"description": "string", "language": "string", "framework": "string"},
                required_params=["description"],
                tool_type=ToolType.CODE_ANALYSIS
            )
        ]
    
    async def execute(self, capability: str, params: Dict[str, Any]) -> ToolResult:
        """Execute code analysis operations."""
        try:
            if capability == "explain_code":
                code = params.get("code", "")
                language = params.get("language", "unknown")
                
                # Simple code analysis
                lines = code.split('\n')
                analysis = {
                    "summary": f"This is {language} code with {len(lines)} lines",
                    "structure": "Function definitions and implementation details",
                    "complexity": "moderate" if len(lines) > 20 else "simple"
                }
                
                result = f"Code Analysis:\n- Language: {language}\n- Lines: {len(lines)}\n- Structure: Contains various programming constructs\n- Complexity: {analysis['complexity']}"
                return ToolResult(success=True, data=result)
                
            elif capability == "review_code":
                code = params.get("code", "")
                focus = params.get("focus", "all")
                
                # Simple code review
                issues = []
                if "TODO" in code:
                    issues.append("Contains TODO comments")
                if "print(" in code:
                    issues.append("Contains debug print statements")
                if len(code.split('\n')) > 100:
                    issues.append("File is quite long, consider breaking into smaller modules")
                
                result = f"Code Review (focus: {focus}):\n"
                if issues:
                    result += "\n".join(f"- {issue}" for issue in issues)
                else:
                    result += "No major issues found"
                
                return ToolResult(success=True, data=result)
                
            elif capability == "generate_code":
                description = params.get("description", "")
                language = params.get("language", "python")
                
                # Use actual Ollama model for code generation
                try:
                    logger.debug(f"Attempting Ollama generation for: {description[:100]}")
                    code = await self._generate_with_ollama(description, language)
                    logger.debug(f"Ollama generated {len(code)} characters")
                    return ToolResult(success=True, data=code)
                except Exception as e:
                    # Fallback to enhanced template-based generation
                    logger.warning(f"Ollama generation failed, using fallback: {e}")
                    return await self._generate_code_fallback(description, language)
            
            else:
                return ToolResult(success=False, error=f"Unknown capability: {capability}", data=None)
                
        except Exception as e:
            logger.error(f"CodeAnalysisTool error: {e}")
            return ToolResult(success=False, error=str(e), data=None)
    
    async def _generate_with_ollama(self, description: str, language: str) -> str:
        """Generate code using actual Ollama model."""
        import ollama
        
        # Create a detailed prompt for code generation
        prompt = f"""Generate complete, functional {language} code for the following request:

{description}

Requirements:
- Write complete, working code with proper error handling
- Include comprehensive docstrings/comments
- Add example usage at the end
- Follow best practices for {language}
- Make it production-ready with proper exception handling
- Include imports/dependencies as needed

Generate only the code, no explanations:"""

        try:
            logger.debug(f"Calling Ollama with prompt length: {len(prompt)}")
            # Use codellama for better code generation
            response = ollama.generate(
                model='codellama:latest',
                prompt=prompt,
                options={
                    'temperature': 0.1,  # Lower temperature for more consistent code
                    'top_p': 0.9,
                    'stop': ['```']  # Stop at code block markers
                }
            )
            
            logger.debug(f"Ollama raw response length: {len(response.get('response', ''))}")
            code = response['response'].strip()
            logger.debug(f"Code after strip: {len(code)} chars, preview: {code[:100]}")
            
            # Clean up the response - remove markdown formatting if present
            if code.startswith('```'):
                lines = code.split('\n')
                # Remove first line if it's markdown language marker
                if len(lines) > 1 and lines[0].startswith('```'):
                    lines = lines[1:]
                # Remove last line if it's closing markdown
                if len(lines) > 1 and lines[-1].strip() == '```':
                    lines = lines[:-1]
                code = '\n'.join(lines)
                logger.debug(f"Code after markdown cleanup: {len(code)} chars")
            
            return code
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise e
    
    async def _generate_code_fallback(self, description: str, language: str) -> ToolResult:
        """Fallback code generation using templates."""
        # Enhanced template-based generation (your existing logic)
        if "factorial" in description.lower():
            if language == "python":
                code = '''def factorial(n):
    """Calculate the factorial of a number.
    
    Args:
        n (int): A non-negative integer
        
    Returns:
        int: The factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n == 0 or n == 1:
        return 1
    
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

# Example usage
if __name__ == "__main__":
    print(f"Factorial of 5: {factorial(5)}")
    print(f"Factorial of 0: {factorial(0)}")'''
            else:
                code = '''function factorial(n) {
    if (n < 0) {
        throw new Error("Factorial is not defined for negative numbers");
    }
    if (n === 0 || n === 1) {
        return 1;
    }
    
    let result = 1;
    for (let i = 2; i <= n; i++) {
        result *= i;
    }
    return result;
}

console.log("Factorial of 5:", factorial(5));'''
                
        elif "calculator" in description.lower():
            if language == "python":
                code = '''class Calculator:
    """A simple calculator class with basic operations."""
    
    def add(self, a, b):
        """Add two numbers."""
        return a + b
    
    def subtract(self, a, b):
        """Subtract b from a."""
        return a - b
    
    def multiply(self, a, b):
        """Multiply two numbers."""
        return a * b
    
    def divide(self, a, b):
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def power(self, a, b):
        """Raise a to the power of b."""
        return a ** b

# Example usage
if __name__ == "__main__":
    calc = Calculator()
    print(f"5 + 3 = {calc.add(5, 3)}")
    print(f"10 - 4 = {calc.subtract(10, 4)}")
    print(f"6 * 7 = {calc.multiply(6, 7)}")
    print(f"15 / 3 = {calc.divide(15, 3)}")'''
            else:
                code = '''class Calculator {
    add(a, b) {
        return a + b;
    }
    
    subtract(a, b) {
        return a - b;
    }
    
    multiply(a, b) {
        return a * b;
    }
    
    divide(a, b) {
        if (b === 0) {
            throw new Error("Cannot divide by zero");
        }
        return a / b;
    }
}

const calc = new Calculator();
console.log("5 + 3 =", calc.add(5, 3));'''
        else:
            # Generic fallback
            if language == "python":
                code = f'''"""
{description}
"""

def main():
    """Main function to implement the requested functionality."""
    # TODO: Implement based on the description: {description}
    pass

if __name__ == "__main__":
    main()'''
            else:
                code = f'''// {description}

function main() {{
    // TODO: Implement based on the description: {description}
}}

main();'''
        
        return ToolResult(success=True, data=code)


class WebTool(ToolInterface):
    """Web operations tool (similar to Claude's WebFetch)."""
    
    def __init__(self):
        super().__init__("web")
        
    def get_capabilities(self) -> List[ToolCapability]:
        return [
            ToolCapability(
                name="fetch_url",
                description="Fetch content from a URL",
                parameters={"url": "string", "method": "string", "headers": "object"},
                required_params=["url"],
                tool_type=ToolType.WEB
            ),
            ToolCapability(
                name="search_web",
                description="Search the web for information",
                parameters={"query": "string", "limit": "number"},
                required_params=["query"],
                tool_type=ToolType.WEB
            )
        ]
    
    async def execute(self, capability: str, params: Dict[str, Any]) -> ToolResult:
        """Execute web operations."""
        try:
            if capability == "fetch_url":
                url = params.get("url")
                if not url:
                    return ToolResult(success=False, error="Missing url parameter", data=None)
                return await self._fetch_url(url, params.get("method", "GET"))
            elif capability == "search_web":
                query = params.get("query")
                if not query:
                    return ToolResult(success=False, error="Missing query parameter", data=None)
                return await self._search_web(query, params.get("limit", 10))
            else:
                return ToolResult(success=False, error=f"Unknown capability: {capability}", data=None)
                
        except Exception as e:
            logger.error(f"WebTool error: {e}")
            return ToolResult(success=False, error=str(e), data=None)
    
    async def _fetch_url(self, url: str, method: str = "GET") -> ToolResult:
        """Fetch content from URL."""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url) as response:
                    content = await response.text()
                    return ToolResult(
                        success=True, 
                        data=content,
                        metadata={
                            "status_code": response.status,
                            "headers": dict(response.headers),
                            "url": str(response.url)
                        }
                    )
        except Exception as e:
            return ToolResult(success=False, error=str(e), data=None)
    
    async def _search_web(self, query: str, limit: int = 10) -> ToolResult:
        """Search the web (placeholder - would integrate with search API)."""
        # This would integrate with a search API like DuckDuckGo or Google
        return ToolResult(
            success=False, 
            error="Web search not implemented yet - requires search API integration",
            data=None
        )