"""Utility functions for response parsing and formatting."""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


logger = logging.getLogger('olla-cli')


class ResponseFormatter:
    """Utility class for formatting Ollama responses."""
    
    @staticmethod
    def extract_content(response: Dict[str, Any]) -> str:
        """Extract content from Ollama response.
        
        Args:
            response: Ollama API response
            
        Returns:
            Extracted content string
        """
        if isinstance(response, dict):
            # Chat response format
            if 'message' in response:
                return response['message'].get('content', '')
            
            # Generate/completion response format
            if 'response' in response:
                return response['response']
            
            # Direct content
            if 'content' in response:
                return response['content']
        
        return str(response)
    
    @staticmethod
    def extract_metadata(response: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from Ollama response.
        
        Args:
            response: Ollama API response
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Common metadata fields
        metadata_fields = [
            'model', 'created_at', 'done', 'total_duration',
            'load_duration', 'prompt_eval_count', 'prompt_eval_duration',
            'eval_count', 'eval_duration'
        ]
        
        for field in metadata_fields:
            if field in response:
                metadata[field] = response[field]
        
        return metadata
    
    @staticmethod
    def format_streaming_response(chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine streaming response chunks into final response.
        
        Args:
            chunks: List of response chunks
            
        Returns:
            Combined response
        """
        if not chunks:
            return {'content': '', 'metadata': {}}
        
        # Combine content from all chunks
        content_parts = []
        final_metadata = {}
        
        for chunk in chunks:
            # Extract content
            if 'message' in chunk and 'content' in chunk['message']:
                content_parts.append(chunk['message']['content'])
            elif 'response' in chunk:
                content_parts.append(chunk['response'])
            
            # Update metadata from final chunk
            if chunk.get('done', False):
                final_metadata = ResponseFormatter.extract_metadata(chunk)
        
        combined_content = ''.join(content_parts)
        
        return {
            'content': combined_content,
            'metadata': final_metadata
        }
    
    @staticmethod
    def format_code_response(content: str, language: Optional[str] = None) -> str:
        """Format code in response with proper markdown.
        
        Args:
            content: Response content
            language: Programming language for syntax highlighting
            
        Returns:
            Formatted content with code blocks
        """
        # If content already has code blocks, return as-is
        if '```' in content:
            return content
        
        # Detect if content looks like code
        code_indicators = [
            r'def\s+\w+\s*\(',      # Python function
            r'function\s+\w+\s*\(', # JavaScript function
            r'class\s+\w+\s*[{:]',  # Class definition
            r'import\s+\w+',        # Import statement
            r'#include\s*<',        # C/C++ include
            r'package\s+\w+',       # Go/Java package
        ]
        
        looks_like_code = any(re.search(pattern, content, re.IGNORECASE) for pattern in code_indicators)
        
        if looks_like_code and language:
            return f"```{language}\n{content}\n```"
        elif looks_like_code:
            return f"```\n{content}\n```"
        
        return content
    
    @staticmethod
    def clean_response(content: str) -> str:
        """Clean and normalize response content.
        
        Args:
            content: Raw content
            
        Returns:
            Cleaned content
        """
        if not content:
            return ""
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Remove trailing whitespace from lines
        content = '\n'.join(line.rstrip() for line in content.split('\n'))
        
        # Ensure single final newline
        content = content.strip() + '\n'
        
        return content


class TokenCounter:
    """Utility for estimating token counts."""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for text.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English text
        # This varies by tokenizer but provides a reasonable approximation
        return len(text) // 4
    
    @staticmethod
    def estimate_tokens_precise(text: str) -> int:
        """More precise token estimation.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Split by whitespace and punctuation
        words = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        # Estimate tokens per word (accounting for subword tokenization)
        token_count = 0
        for word in words:
            if len(word) <= 3:
                token_count += 1
            elif len(word) <= 6:
                token_count += 2
            else:
                token_count += max(2, len(word) // 4)
        
        return token_count


class MessageBuilder:
    """Utility for building chat messages."""
    
    @staticmethod
    def build_system_message(content: str) -> Dict[str, str]:
        """Build system message.
        
        Args:
            content: System message content
            
        Returns:
            Message dictionary
        """
        return {"role": "system", "content": content}
    
    @staticmethod
    def build_user_message(content: str) -> Dict[str, str]:
        """Build user message.
        
        Args:
            content: User message content
            
        Returns:
            Message dictionary
        """
        return {"role": "user", "content": content}
    
    @staticmethod
    def build_assistant_message(content: str) -> Dict[str, str]:
        """Build assistant message.
        
        Args:
            content: Assistant message content
            
        Returns:
            Message dictionary
        """
        return {"role": "assistant", "content": content}
    
    @staticmethod
    def build_code_analysis_messages(task: str, code: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """Build messages for code analysis tasks.
        
        Args:
            task: Task type (explain, review, refactor, etc.)
            code: Code to analyze
            context: Additional context
            
        Returns:
            List of messages
        """
        task_prompts = {
            'explain': "Explain what this code does, how it works, and its purpose. Be clear and detailed.",
            'review': "Review this code for best practices, potential issues, and suggest improvements. Focus on code quality, security, and maintainability.",
            'refactor': "Suggest refactoring improvements for this code while maintaining functionality. Focus on code organization, naming, and design patterns.",
            'debug': "Analyze this code for potential bugs and issues. Provide debugging suggestions and solutions.",
            'test': "Generate comprehensive test cases for this code. Include edge cases and different scenarios.",
            'document': "Generate documentation for this code including docstrings, parameter descriptions, and usage examples."
        }
        
        system_prompt = task_prompts.get(task, f"Perform {task} analysis on the provided code.")
        
        messages = [
            MessageBuilder.build_system_message(system_prompt)
        ]
        
        # Add context if provided
        user_content = f"Code to analyze:\n\n```\n{code}\n```"
        
        if context:
            context_parts = []
            if context.get('error'):
                context_parts.append(f"Error encountered: {context['error']}")
            if context.get('language'):
                context_parts.append(f"Programming language: {context['language']}")
            if context.get('framework'):
                context_parts.append(f"Framework: {context['framework']}")
            if context.get('style'):
                context_parts.append(f"Style preference: {context['style']}")
            
            if context_parts:
                user_content = f"Additional context:\n{chr(10).join(context_parts)}\n\n{user_content}"
        
        messages.append(MessageBuilder.build_user_message(user_content))
        
        return messages
    
    @staticmethod
    def build_code_generation_messages(description: str, language: str = 'python', style: Optional[str] = None) -> List[Dict[str, str]]:
        """Build messages for code generation.
        
        Args:
            description: Code description
            language: Programming language
            style: Code style preference
            
        Returns:
            List of messages
        """
        system_prompt = f"Generate high-quality {language} code based on the user's description. Follow best practices and include appropriate comments."
        
        if style:
            system_prompt += f" Use {style} style."
        
        user_content = f"Generate {language} code for: {description}"
        
        messages = [
            MessageBuilder.build_system_message(system_prompt),
            MessageBuilder.build_user_message(user_content)
        ]
        
        return messages


class ProgressTracker:
    """Utility for tracking operation progress."""
    
    def __init__(self):
        self.start_time = None
        self.steps_completed = 0
        self.total_steps = 0
    
    def start(self, total_steps: int = 1) -> None:
        """Start progress tracking.
        
        Args:
            total_steps: Total number of steps
        """
        self.start_time = datetime.now()
        self.steps_completed = 0
        self.total_steps = total_steps
        logger.debug(f"Started progress tracking with {total_steps} steps")
    
    def step(self, message: Optional[str] = None) -> None:
        """Complete a step.
        
        Args:
            message: Optional step message
        """
        self.steps_completed += 1
        progress = (self.steps_completed / self.total_steps) * 100 if self.total_steps > 0 else 0
        
        if message:
            logger.info(f"Step {self.steps_completed}/{self.total_steps}: {message} ({progress:.1f}%)")
        else:
            logger.debug(f"Progress: {self.steps_completed}/{self.total_steps} ({progress:.1f}%)")
    
    def finish(self) -> None:
        """Finish progress tracking."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info(f"Operation completed in {duration.total_seconds():.2f}s")


def parse_model_response(response: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    """Parse and normalize model response.
    
    Args:
        response: Raw response from model
        
    Returns:
        Normalized response dictionary
    """
    if isinstance(response, str):
        return {
            'content': response,
            'metadata': {}
        }
    
    if isinstance(response, dict):
        return {
            'content': ResponseFormatter.extract_content(response),
            'metadata': ResponseFormatter.extract_metadata(response)
        }
    
    return {
        'content': str(response),
        'metadata': {}
    }


def format_error_message(error: Exception, context: Optional[str] = None) -> str:
    """Format error message for user display.
    
    Args:
        error: Exception object
        context: Additional context
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    if context:
        return f"Error in {context}: {error_type} - {error_msg}"
    else:
        return f"{error_type}: {error_msg}"