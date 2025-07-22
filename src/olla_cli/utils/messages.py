"""Message building utilities."""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class MessageBuilder:
    """Builder for constructing messages to language models."""
    
    def __init__(self):
        self.messages = []
        self.context = {}
    
    def add_system_message(self, content: str) -> 'MessageBuilder':
        """Add a system message."""
        self.messages.append({
            'role': 'system',
            'content': content
        })
        return self
    
    def add_user_message(self, content: str) -> 'MessageBuilder':
        """Add a user message.""" 
        self.messages.append({
            'role': 'user',
            'content': content
        })
        return self
    
    def add_assistant_message(self, content: str) -> 'MessageBuilder':
        """Add an assistant message."""
        self.messages.append({
            'role': 'assistant',
            'content': content
        })
        return self
    
    def add_context(self, key: str, value: Any) -> 'MessageBuilder':
        """Add context information."""
        self.context[key] = value
        return self
    
    def add_file_context(self, file_path: str, content: str) -> 'MessageBuilder':
        """Add file context."""
        self.add_context('files', self.context.get('files', {}))
        self.context['files'][file_path] = content
        return self
    
    def build_chat_messages(self) -> List[Dict[str, str]]:
        """Build messages for chat API."""
        return self.messages.copy()
    
    def build_completion_prompt(self) -> str:
        """Build a single prompt for completion API."""
        prompt_parts = []
        
        for message in self.messages:
            role = message['role'].title()
            content = message['content']
            prompt_parts.append(f"{role}: {content}")
        
        return '\n\n'.join(prompt_parts)
    
    def build_context_aware_prompt(self) -> str:
        """Build a prompt with context information."""
        prompt_parts = []
        
        # Add context if available
        if self.context:
            prompt_parts.append("Context:")
            if 'files' in self.context:
                for file_path, content in self.context['files'].items():
                    prompt_parts.append(f"\nFile: {file_path}")
                    prompt_parts.append(f"```\n{content}\n```")
            
            for key, value in self.context.items():
                if key != 'files':
                    prompt_parts.append(f"{key}: {value}")
            
            prompt_parts.append("\n" + "="*50 + "\n")
        
        # Add messages
        prompt_parts.append(self.build_completion_prompt())
        
        return '\n'.join(prompt_parts)
    
    def clear(self) -> 'MessageBuilder':
        """Clear all messages and context."""
        self.messages.clear()
        self.context.clear()
        return self
    
    def get_message_count(self) -> int:
        """Get the number of messages."""
        return len(self.messages)
    
    def get_last_message(self) -> Optional[Dict[str, str]]:
        """Get the last message."""
        return self.messages[-1] if self.messages else None