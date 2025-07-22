"""Core command implementations for olla-cli."""

import re
import time
import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Iterator
from dataclasses import dataclass
from enum import Enum
import logging

from ..client import OllamaClient
from ..client import ModelManager
from ..context import ContextBuilder as ContextManager, ContextStrategy
from ..utils import MessageBuilder, ResponseFormatter, TokenCounter
from ..core import (
    OllamaConnectionError, ModelNotFoundError, ContextLimitExceededError
)
from ..ui import FormatterFactory


logger = logging.getLogger('olla-cli')


class DetailLevel(Enum):
    """Detail levels for explanations."""
    BRIEF = "brief"
    NORMAL = "normal"
    COMPREHENSIVE = "comprehensive"


class ReviewFocus(Enum):
    """Focus areas for code review."""
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    BUGS = "bugs"
    ALL = "all"


class RefactorType(Enum):
    """Types of refactoring."""
    SIMPLIFY = "simplify"
    OPTIMIZE = "optimize"
    MODERNIZE = "modernize"
    GENERAL = "general"


class SeverityLevel(Enum):
    """Severity levels for review findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class ReviewFinding:
    """Represents a code review finding."""
    line: int
    severity: SeverityLevel
    category: str
    message: str
    suggestion: str
    code_snippet: str


@dataclass
class RefactorSuggestion:
    """Represents a refactoring suggestion."""
    title: str
    description: str
    before_code: str
    after_code: str
    benefits: List[str]
    line_range: Optional[Tuple[int, int]] = None


class ProgressIndicator:
    """Simple progress indicator for streaming operations."""
    
    def __init__(self, message: str, show_spinner: bool = True):
        self.message = message
        self.show_spinner = show_spinner
        self.running = False
        self.thread = None
        
    def start(self):
        """Start the progress indicator."""
        if self.show_spinner:
            self.running = True
            self.thread = threading.Thread(target=self._spin)
            self.thread.daemon = True
            self.thread.start()
    
    def stop(self):
        """Stop the progress indicator."""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _spin(self):
        """Spinner animation."""
        import sys
        spinner = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        idx = 0
        while self.running:
            sys.stderr.write(f'\r{spinner[idx]} {self.message}')
            sys.stderr.flush()
            idx = (idx + 1) % len(spinner)
            time.sleep(0.1)
        sys.stderr.write('\r' + ' ' * (len(self.message) + 2) + '\r')
        sys.stderr.flush()


class CodeExtractor:
    """Extract specific code sections."""
    
    @staticmethod
    def extract_line_range(content: str, start_line: int, end_line: int) -> str:
        """Extract specific line range from content."""
        lines = content.split('\n')
        if start_line < 1 or start_line > len(lines):
            raise ValueError(f"Start line {start_line} out of range (1-{len(lines)})")
        if end_line < start_line or end_line > len(lines):
            raise ValueError(f"End line {end_line} out of range ({start_line}-{len(lines)})")
        
        extracted_lines = lines[start_line-1:end_line]
        return '\n'.join(extracted_lines)
    
    @staticmethod
    def add_line_numbers(content: str, start_line: int = 1) -> str:
        """Add line numbers to content."""
        lines = content.split('\n')
        numbered_lines = []
        for i, line in enumerate(lines):
            line_num = start_line + i
            numbered_lines.append(f"{line_num:4d} │ {line}")
        return '\n'.join(numbered_lines)


class TemplateManager:
    """Manage code generation templates."""
    
    TEMPLATES = {
        'function': {
            'python': '''def {function_name}({parameters}):
    """
    {description}
    
    Args:
        {args_docs}
    
    Returns:
        {return_type}: {return_description}
    """
    {body}''',
            
            'javascript': '''function {function_name}({parameters}) {
    /**
     * {description}
     * @param {{{param_types}}} {param_names} - {param_descriptions}
     * @returns {{{return_type}}} {return_description}
     */
    {body}
}''',
        },
        
        'class': {
            'python': '''class {class_name}:
    """
    {description}
    
    Attributes:
        {attributes}
    """
    
    def __init__(self{init_params}):
        """Initialize {class_name}."""
        {init_body}
    
    {methods}''',
            
            'javascript': '''class {class_name} {
    /**
     * {description}
     */
    constructor({constructor_params}) {
        {constructor_body}
    }
    
    {methods}
}''',
        },
        
        'api_endpoint': {
            'python': '''@app.route('/{endpoint}', methods=['{method}'])
def {function_name}():
    """
    {description}
    
    Returns:
        JSON response with {response_description}
    """
    try:
        {body}
        return jsonify({{"status": "success", "data": result}})
    except Exception as e:
        return jsonify({{"status": "error", "message": str(e)}}), 400''',
            
            'javascript': '''app.{method_lower}('/{endpoint}', async (req, res) => {
    try {
        // {description}
        {body}
        res.json({{ status: 'success', data: result }});
    } catch (error) {
        res.status(400).json({{ status: 'error', message: error.message }});
    }
});''',
        }
    }
    
    @classmethod
    def get_template(cls, template_type: str, language: str) -> Optional[str]:
        """Get template by type and language."""
        return cls.TEMPLATES.get(template_type, {}).get(language)
    
    @classmethod
    def list_templates(cls) -> Dict[str, List[str]]:
        """List available templates."""
        result = {}
        for template_type, languages in cls.TEMPLATES.items():
            result[template_type] = list(languages.keys())
        return result


class CommandImplementations:
    """Core command implementations."""
    
    def __init__(self, client: OllamaClient, model_manager: ModelManager, 
                 context_manager: ContextManager, formatter=None):
        self.client = client
        self.model_manager = model_manager
        self.context_manager = context_manager
        self.formatter = formatter or FormatterFactory.create_formatter()
    
    def explain_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        line_range: Optional[Tuple[int, int]] = None,
        detail_level: DetailLevel = DetailLevel.NORMAL,
        model: str = "codellama",
        temperature: float = 0.7,
        stream: bool = False,
        language: Optional[str] = None
    ) -> Iterator[str]:
        """Explain code functionality."""
        
        # Extract line range if specified
        if line_range:
            try:
                code = CodeExtractor.extract_line_range(code, line_range[0], line_range[1])
                code = CodeExtractor.add_line_numbers(code, line_range[0])
            except ValueError as e:
                yield f"❌ Line range error: {e}\n"
                return
        
        # Detect language if not provided
        if not language and file_path:
            language = self.model_manager.validate_model(model).family
            if language == 'unknown':
                language = 'python'  # Default fallback
        
        # Build context-aware prompt
        system_prompt = self._build_explain_system_prompt(detail_level, language)
        
        # Add context if file path provided
        context_info = ""
        if file_path:
            try:
                target_path = Path(file_path)
                if target_path.exists():
                    context_result = self.context_manager.build_context(
                        target_path,
                        ContextStrategy.SINGLE_FILE,
                        max_tokens=1000
                    )
                    context_info = f"\n\nFile Context:\n{context_result.content}"
            except Exception as e:
                logger.warning(f"Could not build context: {e}")
        
        user_content = f"""Please explain this code:

```{language or 'text'}
{code}
```{context_info}

Focus on:
- What the code does (functionality)
- How it works (implementation details)
- Why it's written this way (design decisions)
- Any potential issues or improvements
"""
        
        messages = (
            MessageBuilder()
            .add_system_message(system_prompt)
            .add_user_message(user_content)
            .build_chat_messages()
        )
        
        yield from self._stream_response(messages, model, temperature, stream)
    
    def review_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        focus: ReviewFocus = ReviewFocus.ALL,
        model: str = "codellama",
        temperature: float = 0.3,
        stream: bool = False,
        language: Optional[str] = None
    ) -> Iterator[str]:
        """Review code for issues and improvements."""
        
        # Detect language
        if not language and file_path:
            language = Path(file_path).suffix[1:] if Path(file_path).suffix else 'text'
        
        system_prompt = self._build_review_system_prompt(focus, language)
        
        # Add context if available
        context_info = ""
        if file_path:
            try:
                target_path = Path(file_path)
                if target_path.exists():
                    context_result = self.context_manager.build_context(
                        target_path,
                        ContextStrategy.RELATED_FILES,
                        max_tokens=1500
                    )
                    context_info = f"\n\nProject Context:\n{context_result.content}"
            except Exception as e:
                logger.warning(f"Could not build context: {e}")
        
        user_content = f"""Please review this code for potential issues:

```{language or 'text'}
{code}
```{context_info}

Please structure your review with:
1. **Overview**: Brief assessment
2. **Critical Issues**: High-severity problems
3. **Improvements**: Medium-severity suggestions  
4. **Style & Best Practices**: Low-severity recommendations
5. **Security Considerations**: Security-related findings
6. **Performance Notes**: Performance-related observations

For each finding, include:
- Line number (if applicable)
- Severity level (Critical/High/Medium/Low)
- Clear explanation
- Suggested fix
"""
        
        messages = (
            MessageBuilder()
            .add_system_message(system_prompt)
            .add_user_message(user_content)
            .build_chat_messages()
        )
        
        yield from self._stream_response(messages, model, temperature, stream)
    
    def refactor_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        refactor_type: RefactorType = RefactorType.GENERAL,
        model: str = "codellama",
        temperature: float = 0.5,
        stream: bool = False,
        language: Optional[str] = None
    ) -> Iterator[str]:
        """Suggest code refactoring improvements."""
        
        if not language and file_path:
            language = Path(file_path).suffix[1:] if Path(file_path).suffix else 'text'
        
        system_prompt = self._build_refactor_system_prompt(refactor_type, language)
        
        user_content = f"""Please suggest refactoring improvements for this code:

**Original Code:**
```{language or 'text'}
{code}
```

Please provide:

1. **Assessment**: Current code analysis
2. **Refactoring Suggestions**: Specific improvements
3. **Before/After Comparison**: Show the changes
4. **Benefits**: Why each change helps
5. **Implementation Notes**: How to apply changes safely

Format each suggestion as:
### Suggestion N: [Title]
**Before:**
```{language or 'text'}
[original code]
```

**After:**
```{language or 'text'}
[improved code]
```

**Benefits:**
- [benefit 1]
- [benefit 2]
"""
        
        messages = (
            MessageBuilder()
            .add_system_message(system_prompt)
            .add_user_message(user_content)
            .build_chat_messages()
        )
        
        yield from self._stream_response(messages, model, temperature, stream)
    
    def debug_code(
        self,
        code: str,
        error_message: Optional[str] = None,
        stack_trace: Optional[str] = None,
        file_path: Optional[str] = None,
        model: str = "codellama",
        temperature: float = 0.3,
        stream: bool = False,
        language: Optional[str] = None
    ) -> Iterator[str]:
        """Debug code and provide step-by-step suggestions."""
        
        if not language and file_path:
            language = Path(file_path).suffix[1:] if Path(file_path).suffix else 'text'
        
        system_prompt = self._build_debug_system_prompt(language)
        
        debug_info = []
        if error_message:
            debug_info.append(f"**Error Message:**\n```\n{error_message}\n```")
        if stack_trace:
            debug_info.append(f"**Stack Trace:**\n```\n{stack_trace}\n```")
        
        debug_context = '\n\n'.join(debug_info) if debug_info else ""
        
        user_content = f"""Please help debug this code issue:

**Code:**
```{language or 'text'}
{code}
```

{debug_context}

Please provide:

1. **Error Analysis**: What's causing the problem
2. **Root Cause**: Why this error occurs
3. **Step-by-Step Debug Process**: How to investigate
4. **Suggested Fixes**: Concrete solutions
5. **Prevention**: How to avoid similar issues
6. **Testing Strategy**: How to verify the fix

Be specific about line numbers and provide working code examples.
"""
        
        messages = (
            MessageBuilder()
            .add_system_message(system_prompt)
            .add_user_message(user_content)
            .build_chat_messages()
        )
        
        yield from self._stream_response(messages, model, temperature, stream)
    
    def generate_code(
        self,
        description: str,
        language: str = "python",
        framework: Optional[str] = None,
        template: Optional[str] = None,
        model: str = "codellama",
        temperature: float = 0.7,
        stream: bool = False
    ) -> Iterator[str]:
        """Generate code from natural language description."""
        
        system_prompt = self._build_generate_system_prompt(language, framework)
        
        # Add template context if specified
        template_context = ""
        if template:
            template_code = TemplateManager.get_template(template, language)
            if template_code:
                template_context = f"\n\nTemplate to follow:\n```{language}\n{template_code}\n```"
        
        user_content = f"""Please generate {language} code based on this description:

**Requirements:**
{description}

**Language:** {language}
{f"**Framework:** {framework}" if framework else ""}
{template_context}

Please provide:

1. **Implementation**: Complete, working code
2. **Documentation**: Docstrings and comments
3. **Usage Example**: How to use the code  
4. **Error Handling**: Appropriate exception handling
5. **Best Practices**: Following language conventions

The code should be:
- Production-ready
- Well-documented
- Following best practices
- Include proper error handling
- Have clear variable names
"""
        
        messages = (
            MessageBuilder()
            .add_system_message(system_prompt)
            .add_user_message(user_content)
            .build_chat_messages()
        )
        
        yield from self._stream_response(messages, model, temperature, stream)
    
    def generate_tests(
        self,
        code: str,
        file_path: Optional[str] = None,
        framework: str = "pytest",
        coverage: bool = False,
        model: str = "codellama",
        temperature: float = 0.5,
        stream: bool = False,
        language: Optional[str] = None
    ) -> Iterator[str]:
        """Generate unit tests for code."""
        
        if not language and file_path:
            language = Path(file_path).suffix[1:] if Path(file_path).suffix else 'python'
        
        system_prompt = self._build_test_system_prompt(framework, language, coverage)
        
        user_content = f"""Please generate comprehensive unit tests for this code:

**Code to Test:**
```{language or 'python'}
{code}
```

**Testing Framework:** {framework}
**Include Edge Cases:** {coverage}

Please provide:

1. **Test Structure**: Organized test classes/functions
2. **Happy Path Tests**: Normal usage scenarios
3. **Edge Case Tests**: Boundary conditions and special cases
4. **Error Handling Tests**: Exception scenarios
5. **Mock/Fixture Setup**: If external dependencies exist
6. **Test Documentation**: Clear test descriptions

Requirements:
- Use {framework} framework
- Test all public methods/functions
- Include assertions with clear messages
- Cover error conditions
- Follow testing best practices
{'- Focus on high code coverage and edge cases' if coverage else ''}
"""
        
        messages = (
            MessageBuilder()
            .add_system_message(system_prompt)
            .add_user_message(user_content)
            .build_chat_messages()
        )
        
        yield from self._stream_response(messages, model, temperature, stream)
    
    def document_code(
        self,
        code: str,
        file_path: Optional[str] = None,
        doc_format: str = "docstring",
        doc_type: str = "api",  # api, readme, inline
        model: str = "codellama", 
        temperature: float = 0.5,
        stream: bool = False,
        language: Optional[str] = None
    ) -> Iterator[str]:
        """Generate documentation for code."""
        
        if not language and file_path:
            language = Path(file_path).suffix[1:] if Path(file_path).suffix else 'python'
        
        system_prompt = self._build_document_system_prompt(doc_format, doc_type, language)
        
        user_content = f"""Please generate {doc_format} documentation for this code:

**Code:**
```{language or 'text'}
{code}
```

**Documentation Type:** {doc_type}
**Format:** {doc_format}

Please provide:

1. **API Documentation**: Function/class descriptions
2. **Parameter Documentation**: All inputs and outputs
3. **Usage Examples**: Practical code examples
4. **Implementation Notes**: Important details
5. **Dependencies**: Required imports/packages

Requirements:
- Follow {doc_format} format standards
- Include type hints where applicable
- Provide realistic examples
- Explain complex logic
- Note any assumptions or limitations
"""
        
        messages = (
            MessageBuilder()
            .add_system_message(system_prompt)
            .add_user_message(user_content)
            .build_chat_messages()
        )
        
        yield from self._stream_response(messages, model, temperature, stream)
    
    def _stream_response(
        self, 
        messages: List[Dict[str, str]], 
        model: str, 
        temperature: float, 
        stream: bool
    ) -> Iterator[str]:
        """Stream response from the model."""
        try:
            if stream:
                # Streaming response
                response_iter = self.client.chat(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=True
                )
                
                for chunk in response_iter:
                    # Handle different response formats
                    if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                        content = chunk.message.content
                    elif isinstance(chunk, dict):
                        content = ResponseFormatter.extract_content(chunk)
                    else:
                        content = str(chunk)
                    
                    if content and content.strip():
                        yield content
            else:
                # Non-streaming response
                response = self.client.chat(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=False
                )
                
                content = ResponseFormatter.extract_content(response)
                yield content
                
        except Exception as e:
            yield f"❌ Error generating response: {e}\n"
    
    # System prompt builders
    def _build_explain_system_prompt(self, detail_level: DetailLevel, language: Optional[str]) -> str:
        """Build system prompt for explain command."""
        level_instructions = {
            DetailLevel.BRIEF: "Provide a concise explanation focusing on the main purpose and key functionality.",
            DetailLevel.NORMAL: "Provide a clear explanation covering functionality, implementation, and key concepts.",
            DetailLevel.COMPREHENSIVE: "Provide a detailed explanation including functionality, implementation details, design patterns, potential issues, and improvement suggestions."
        }
        
        return f"""You are an expert code analysis assistant for olla-cli. Your role is to explain code clearly and helpfully.

Detail Level: {detail_level.value}
{f"Primary Language: {language}" if language else ""}

Instructions:
{level_instructions[detail_level]}

Format your response with clear headings and examples. Be educational and focus on helping the user understand the code better."""
    
    def _build_review_system_prompt(self, focus: ReviewFocus, language: Optional[str]) -> str:
        """Build system prompt for review command."""
        focus_instructions = {
            ReviewFocus.SECURITY: "Focus primarily on security vulnerabilities, input validation, and potential exploits.",
            ReviewFocus.PERFORMANCE: "Focus on performance bottlenecks, efficiency improvements, and optimization opportunities.",
            ReviewFocus.STYLE: "Focus on code style, formatting, naming conventions, and readability improvements.",
            ReviewFocus.BUGS: "Focus on potential bugs, logical errors, and correctness issues.",
            ReviewFocus.ALL: "Provide a comprehensive review covering security, performance, style, and potential bugs."
        }
        
        return f"""You are an expert code reviewer for olla-cli. Provide thorough, constructive code reviews.

Review Focus: {focus.value}
{f"Primary Language: {language}" if language else ""}

Instructions:
{focus_instructions[focus]}

Always include:
- Specific line references when possible
- Clear severity levels (Critical/High/Medium/Low)
- Actionable suggestions for improvement
- Positive feedback for good practices

Be constructive, specific, and helpful."""
    
    def _build_refactor_system_prompt(self, refactor_type: RefactorType, language: Optional[str]) -> str:
        """Build system prompt for refactor command."""
        type_instructions = {
            RefactorType.SIMPLIFY: "Focus on making code simpler, more readable, and easier to maintain.",
            RefactorType.OPTIMIZE: "Focus on performance improvements and efficiency optimizations.",
            RefactorType.MODERNIZE: "Focus on updating code to use modern language features and best practices.",
            RefactorType.GENERAL: "Provide general refactoring suggestions for better code quality."
        }
        
        return f"""You are an expert refactoring assistant for olla-cli. Suggest practical code improvements.

Refactoring Type: {refactor_type.value}
{f"Primary Language: {language}" if language else ""}

Instructions:
{type_instructions[refactor_type]}

Always provide:
- Clear before/after comparisons
- Explanation of benefits
- Implementation guidance
- Consideration of trade-offs

Focus on practical, valuable improvements that maintain functionality."""
    
    def _build_debug_system_prompt(self, language: Optional[str]) -> str:
        """Build system prompt for debug command."""
        return f"""You are an expert debugging assistant for olla-cli. Help users identify and fix code issues.

{f"Primary Language: {language}" if language else ""}

Your debugging approach should:
- Analyze the error systematically
- Identify root causes, not just symptoms
- Provide step-by-step debugging process
- Suggest specific, testable fixes
- Include prevention strategies

Be methodical, clear, and provide working code examples."""
    
    def _build_generate_system_prompt(self, language: str, framework: Optional[str]) -> str:
        """Build system prompt for generate command."""
        return f"""You are an expert code generation assistant for olla-cli. Create high-quality, production-ready code.

Target Language: {language}
{f"Framework: {framework}" if framework else ""}

Your code should be:
- Functional and well-tested
- Following best practices and conventions
- Properly documented with docstrings/comments
- Including appropriate error handling
- Production-ready quality

Provide complete, working implementations with clear documentation."""
    
    def _build_test_system_prompt(self, framework: str, language: str, coverage: bool) -> str:
        """Build system prompt for test command."""
        coverage_note = "Focus on comprehensive coverage including edge cases and error conditions." if coverage else ""
        
        return f"""You are an expert test generation assistant for olla-cli. Create comprehensive, high-quality unit tests.

Testing Framework: {framework}
Language: {language}
{coverage_note}

Your tests should:
- Cover all public methods and functions
- Include happy path and edge case scenarios
- Test error handling and exception cases
- Use clear, descriptive test names
- Include proper setup and teardown
- Follow testing best practices

Generate complete, runnable test suites."""
    
    def _build_document_system_prompt(self, doc_format: str, doc_type: str, language: str) -> str:
        """Build system prompt for document command."""
        return f"""You are an expert documentation assistant for olla-cli. Create clear, comprehensive documentation.

Documentation Format: {doc_format}
Documentation Type: {doc_type}
Language: {language}

Your documentation should:
- Be clear and easy to understand
- Include practical examples
- Follow format conventions
- Explain complex concepts simply
- Provide complete API coverage
- Include usage patterns and best practices

Generate professional, user-friendly documentation."""