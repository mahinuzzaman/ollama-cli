"""Response parsing utilities."""

import json
import re
from typing import Any, Dict, Optional, Union


def parse_model_response(response: Union[str, Dict[str, Any]]) -> str:
    """Parse and clean model response."""
    if isinstance(response, dict):
        # Extract content from structured response
        if 'message' in response:
            content = response['message'].get('content', '')
        elif 'response' in response:
            content = response['response']
        else:
            content = str(response)
    else:
        content = str(response)
    
    # Clean up the response
    content = content.strip()
    
    # Remove markdown artifacts if present
    content = _clean_markdown_artifacts(content)
    
    return content


def _clean_markdown_artifacts(text: str) -> str:
    """Clean common markdown artifacts from model responses."""
    # Remove excessive code block markers
    text = re.sub(r'^```\w*\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n```$', '', text, flags=re.MULTILINE)
    
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def parse_json_response(response: str) -> Optional[Dict[str, Any]]:
    """Try to parse JSON from a response string."""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        return None


def extract_numbered_list(text: str) -> list:
    """Extract numbered list items from text."""
    pattern = r'^\d+\.\s*(.+)$'
    matches = re.findall(pattern, text, re.MULTILINE)
    return [match.strip() for match in matches]


def extract_bullet_list(text: str) -> list:
    """Extract bullet list items from text."""
    pattern = r'^[•\-\*]\s*(.+)$'
    matches = re.findall(pattern, text, re.MULTILINE)
    return [match.strip() for match in matches]