"""Intent Classification System for intelligent request routing."""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger('olla-cli.routing.intent')


class IntentType(Enum):
    """Types of user intents."""
    CODE_EXPLAIN = "code_explain"
    CODE_REVIEW = "code_review" 
    CODE_GENERATE = "code_generate"
    CODE_REFACTOR = "code_refactor"
    CODE_DEBUG = "code_debug"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_LIST = "file_list"
    WEB_FETCH = "web_fetch"
    WEB_SEARCH = "web_search"
    SHELL_EXECUTE = "shell_execute"
    TASK_COMPLEX = "task_complex"
    CHAT_GENERAL = "chat_general"
    CONFIG_MANAGE = "config_manage"
    MODEL_MANAGE = "model_manage"
    UNKNOWN = "unknown"


@dataclass
class Intent:
    """Represents a classified user intent."""
    type: IntentType
    confidence: float
    parameters: Dict[str, Any]
    raw_input: str
    context_hints: Optional[Dict[str, Any]] = None
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """Check if confidence is above threshold."""
        return self.confidence >= threshold


class IntentClassifier:
    """Classifies user input into intents for intelligent routing."""
    
    def __init__(self):
        self.patterns = self._load_intent_patterns()
        self.context_keywords = self._load_context_keywords()
        
    def classify(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Intent:
        """Classify user input into an intent."""
        user_input = user_input.strip().lower()
        
        # Try pattern matching first
        for intent_type, patterns in self.patterns.items():
            for pattern, confidence_boost in patterns:
                if re.search(pattern, user_input, re.IGNORECASE):
                    confidence = self._calculate_confidence(user_input, intent_type, context)
                    confidence = min(1.0, confidence + confidence_boost)
                    
                    parameters = self._extract_parameters(user_input, intent_type)
                    
                    return Intent(
                        type=intent_type,
                        confidence=confidence,
                        parameters=parameters,
                        raw_input=user_input,
                        context_hints=context
                    )
        
        # Fallback to keyword-based classification
        return self._classify_by_keywords(user_input, context)
    
    def _load_intent_patterns(self) -> Dict[IntentType, List[Tuple[str, float]]]:
        """Load regex patterns for intent classification."""
        return {
            IntentType.CODE_EXPLAIN: [
                (r'\b(explain|understand|what does|how does|describe)\b.*\b(code|function|class|method)\b', 0.3),
                (r'\bexplain\b.*\.(py|js|java|cpp|c|go|rs|php)$', 0.4),
                (r'^explain\s+', 0.5),
            ],
            IntentType.CODE_REVIEW: [
                (r'\b(review|check|analyze|audit|inspect)\b.*\b(code|file)\b', 0.3),
                (r'\b(bugs?|issues?|problems?|errors?)\b.*\b(find|check|look)\b', 0.2),
                (r'^review\s+', 0.5),
            ],
            IntentType.CODE_GENERATE: [
                (r'\b(create|generate|write|build|make)\b.*\bcode\b(?!.*\b(react|vue|angular|app)\b)', 0.3),  # Code but not frameworks/apps
                (r'^(create|generate|write|build)\s+.*\bcode\b(?!.*\b(react|vue|angular|app)\b)', 0.4),  # Code but not frameworks/apps
                (r'\b(implement|develop)\b.*\bcode\b(?!.*\b(react|vue|angular|app)\b)', 0.2),  # Code but not frameworks/apps
            ],
            IntentType.CODE_REFACTOR: [
                (r'\b(refactor|improve|optimize|clean|restructure)\b', 0.4),
                (r'\b(make.*better|improve.*code)\b', 0.3),
                (r'^refactor\s+', 0.5),
            ],
            IntentType.CODE_DEBUG: [
                (r'\b(debug|fix|solve|error|bug|issue|problem)\b', 0.3),
                (r'\b(not working|broken|failing|crash)\b', 0.2),
                (r'^debug\s+', 0.5),
            ],
            IntentType.FILE_READ: [
                (r'\b(read|show|display|open|cat|view)\b.*\bfile\b', 0.3),
                (r'\bread\s+.*\.(py|js|txt|md|json|yaml|yml|toml)$', 0.4),
                (r'^(cat|head|tail|less|more)\s+', 0.4),
            ],
            IntentType.FILE_WRITE: [
                (r'\b(write|save|create|put)\b.*\b(to|in|into)\b.*\bfile\b', 0.3),
                (r'\b(save|write)\s+.*\s+(to|as)\s+.*\.(py|js|txt|md|json)', 0.4),
                (r'^(echo|printf)\s+.*>\s*', 0.3),
                (r'\bcreate\s+.*\bfile\s+(called|named)\b', 0.5),
                (r'\bcreate\s+.*\.(py|js|txt|md|json|yaml|yml)\b', 0.4),
                (r'\bmake\s+.*\bfile\b', 0.3),
            ],
            IntentType.FILE_LIST: [
                (r'\b(list|show|find)\b.*\b(files?|directories?|folders?)\b', 0.3),
                (r'^(ls|dir|find)\s+', 0.4),
                (r'\bwhat.*files\b', 0.2),
            ],
            IntentType.WEB_FETCH: [
                (r'\b(fetch|get|download|retrieve)\b.*\b(url|website|page|link)\b', 0.3),
                (r'\bfrom\s+https?://', 0.4),
                (r'^(curl|wget)\s+', 0.4),
            ],
            IntentType.WEB_SEARCH: [
                (r'\b(search|find|look up|google)\b.*\b(web|internet|online)\b', 0.3),
                (r'\bsearch\s+for\b', 0.3),
                (r'^search\s+', 0.4),
            ],
            IntentType.SHELL_EXECUTE: [
                (r'^(bash|sh|zsh|fish)\s+', 0.5),
                (r'\b(run|execute|exec)\b.*\b(command|script|shell)\b', 0.3),
                (r'^(sudo|npm|pip|git|docker|kubectl)\s+', 0.4),
            ],
            IntentType.TASK_COMPLEX: [
                (r'\b(task|workflow|process|pipeline)\b', 0.3),
                (r'\b(step by step|multi-step|complex)\b', 0.2),
                (r'^task\s+', 0.5),
                (r'\bcreate\s+.*\bfile\s+.*(with|containing).*\b(function|class|code)\b', 0.6),
                (r'\bmake\s+.*\bfile\s+.*\bcontaining\b', 0.5),
                (r'\b(generate|create)\s+.*\band\s+(save|write|create)', 0.4),
                (r'\b(create|generate|build|make)\s+.*\.(py|js|ts|java|cpp|c|h|go|rs|php|rb|txt|md|json|yaml|yml|toml|html|css)\b', 0.7),
                (r'\bcreate\s+.*\bfile\s+(called|named)\s+.*\.(py|js|ts|java|cpp)\b', 0.8),
                (r'\b(write|create|generate)\s+.*\bcode\s+.*\b(to|in|into)\s+.*\.(py|js|ts|java)\b', 0.7),
                (r'\b(implement|develop|build)\s+.*\band\s+(save|write|create|put).*\bfile\b', 0.6),
                (r'\bcreate\s+.*\b(function|class|module|script|program)\b', 0.7),  # Auto-create files for functions/classes
                (r'\bcreate\s+.*\b(app|application)\b', 0.9),  # App creation
                (r'\bcreate\s+.*\b(react|vue|angular|next|nodejs|express)\b', 1.0),  # Framework apps
                (r'\b(todo|task)\s+.*\b(react|app)\b', 1.0),  # Todo/task apps
            ],
            IntentType.CONFIG_MANAGE: [
                (r'\b(config|configuration|settings?|preferences?)\b', 0.3),
                (r'^config\s+', 0.5),
                (r'\b(set|get|show|reset)\b.*\b(config|setting)\b', 0.3),
            ],
            IntentType.MODEL_MANAGE: [
                (r'\b(model|models)\b.*\b(list|info|pull|download)\b', 0.4),
                (r'^models?\s+', 0.5),
                (r'\bollama\s+(pull|list|info)\b', 0.4),
            ],
        }
    
    def _load_context_keywords(self) -> Dict[str, List[str]]:
        """Load context keywords that boost certain intents."""
        return {
            'file_operations': ['file', 'directory', 'folder', 'path', '.py', '.js', '.txt'],
            'code_operations': ['code', 'function', 'class', 'method', 'variable', 'algorithm'],
            'web_operations': ['url', 'http', 'https', 'website', 'api', 'endpoint'],
            'development': ['debug', 'test', 'build', 'deploy', 'git', 'npm', 'pip']
        }
    
    def _calculate_confidence(self, user_input: str, intent_type: IntentType, context: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence score for an intent."""
        base_confidence = 0.5
        
        # Boost confidence based on context
        if context:
            if 'file_path' in context and intent_type in [IntentType.FILE_READ, IntentType.FILE_WRITE, IntentType.CODE_EXPLAIN]:
                base_confidence += 0.2
            if 'code' in context and intent_type in [IntentType.CODE_EXPLAIN, IntentType.CODE_REVIEW, IntentType.CODE_REFACTOR]:
                base_confidence += 0.2
        
        # Check for context keywords
        for category, keywords in self.context_keywords.items():
            keyword_matches = sum(1 for keyword in keywords if keyword in user_input)
            if keyword_matches > 0:
                if category == 'code_operations' and intent_type.value.startswith('code_'):
                    base_confidence += 0.1 * keyword_matches
                elif category == 'file_operations' and intent_type.value.startswith('file_'):
                    base_confidence += 0.1 * keyword_matches
                elif category == 'web_operations' and intent_type.value.startswith('web_'):
                    base_confidence += 0.1 * keyword_matches
        
        return min(1.0, base_confidence)
    
    def _extract_parameters(self, user_input: str, intent_type: IntentType) -> Dict[str, Any]:
        """Extract parameters from user input based on intent type."""
        parameters = {}
        
        # Common patterns for file paths
        file_path_match = re.search(r'([^\s]+\.\w+)(?:\s|$)', user_input)
        if file_path_match:
            parameters['file_path'] = file_path_match.group(1)
        
        # Extract URLs
        url_match = re.search(r'https?://[^\s]+', user_input)
        if url_match:
            parameters['url'] = url_match.group(0)
        
        # Extract programming languages
        lang_patterns = {
            r'\bpython\b': 'python',
            r'\bjavascript\b|\bjs\b': 'javascript', 
            r'\bjava\b': 'java',
            r'\bc\+\+\b|\bcpp\b': 'cpp',
            r'\breact\b': 'javascript',
            r'\bflask\b|\bdjango\b': 'python'
        }
        
        for pattern, language in lang_patterns.items():
            if re.search(pattern, user_input, re.IGNORECASE):
                parameters['language'] = language
                break
        
        # Extract specific command patterns
        if intent_type == IntentType.CODE_GENERATE:
            # Look for template hints
            if 'function' in user_input:
                parameters['template'] = 'function'
            elif 'class' in user_input:
                parameters['template'] = 'class' 
            elif 'app' in user_input or 'application' in user_input:
                parameters['template'] = 'app'
        
        elif intent_type == IntentType.CODE_REVIEW:
            # Look for focus areas
            focus_keywords = {
                'security': r'\b(security|secure|vulnerability|vulnerabilities|safe|unsafe)\b',
                'performance': r'\b(performance|speed|fast|slow|optimize|optimization)\b',
                'style': r'\b(style|format|formatting|convention|clean)\b',
                'bugs': r'\b(bug|bugs|error|errors|issue|issues|problem|problems)\b'
            }
            
            for focus, pattern in focus_keywords.items():
                if re.search(pattern, user_input, re.IGNORECASE):
                    parameters['focus'] = focus
                    break
        
        return parameters
    
    def _classify_by_keywords(self, user_input: str, context: Optional[Dict[str, Any]]) -> Intent:
        """Fallback classification using keywords."""
        # Simple keyword-based classification
        keyword_intents = {
            IntentType.CHAT_GENERAL: ['hello', 'hi', 'help', 'what', 'how', 'why', 'chat'],
            IntentType.CODE_EXPLAIN: ['explain', 'describe', 'what does'],
            IntentType.CODE_GENERATE: ['create', 'generate', 'make', 'build'],
            IntentType.FILE_READ: ['read', 'show', 'display', 'cat'],
            IntentType.CONFIG_MANAGE: ['config', 'settings', 'configure']
        }
        
        best_intent = IntentType.UNKNOWN
        best_score = 0
        
        for intent_type, keywords in keyword_intents.items():
            score = sum(1 for keyword in keywords if keyword in user_input)
            if score > best_score:
                best_score = score
                best_intent = intent_type
        
        confidence = min(0.6, best_score * 0.2) if best_score > 0 else 0.1
        
        return Intent(
            type=best_intent,
            confidence=confidence,
            parameters={},
            raw_input=user_input,
            context_hints=context
        )