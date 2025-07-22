"""Response formatting utilities."""

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
        """Extract content from Ollama response."""
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
        """Extract metadata from Ollama response."""
        metadata = {}
        
        if isinstance(response, dict):
            # Common metadata fields
            for field in ['model', 'created_at', 'done', 'total_duration', 'load_duration',
                         'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration']:
                if field in response:
                    metadata[field] = response[field]
        
        return metadata
    
    @staticmethod
    def format_streaming_response(chunk: Dict[str, Any]) -> str:
        """Format a streaming response chunk."""
        return ResponseFormatter.extract_content(chunk)
    
    @staticmethod
    def format_code_block(content: str, language: str = "") -> str:
        """Format content as a code block."""
        return f"```{language}\n{content}\n```"
    
    @staticmethod
    def extract_code_blocks(text: str) -> List[Dict[str, str]]:
        """Extract code blocks from text."""
        pattern = r'```(\w*)\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        blocks = []
        for language, code in matches:
            blocks.append({
                'language': language,
                'code': code.strip()
            })
        
        return blocks