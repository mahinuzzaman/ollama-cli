"""Context-Aware Decision Engine for intelligent routing and behavior."""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

from ..routing.intent import Intent, IntentType
from .session_memory import SessionMemory
from .context_analyzer import ContextAnalyzer
from .smart_defaults import SmartDefaultsSystem

logger = logging.getLogger('olla-cli.intelligence.decision')


@dataclass
class DecisionContext:
    """Context information for decision making."""
    user_input: str
    intent: Intent
    session_history: List[Dict[str, Any]] = field(default_factory=list)
    project_context: Dict[str, Any] = field(default_factory=dict)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    current_directory: Optional[str] = None
    recent_files: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


class DecisionEngine:
    """Context-aware decision engine that enhances routing with intelligence."""
    
    def __init__(self):
        self.session_memory = SessionMemory()
        self.context_analyzer = ContextAnalyzer()
        self.smart_defaults = SmartDefaultsSystem()
        self.decision_history: List[Dict[str, Any]] = []
        
    async def enhance_intent(self, intent: Intent, raw_context: Optional[Dict[str, Any]] = None) -> Intent:
        """Enhance an intent with context-aware intelligence."""
        
        # Build decision context
        context = await self._build_decision_context(intent, raw_context)
        
        # Apply context-aware enhancements
        enhanced_intent = await self._apply_context_enhancements(intent, context)
        
        # Apply smart defaults
        enhanced_intent = await self.smart_defaults.apply_defaults(enhanced_intent, context)
        
        # Learn from this decision
        await self._record_decision(enhanced_intent, context)
        
        return enhanced_intent
    
    async def _build_decision_context(self, intent: Intent, raw_context: Optional[Dict[str, Any]]) -> DecisionContext:
        """Build comprehensive decision context."""
        
        # Get session history
        session_history = await self.session_memory.get_recent_interactions(limit=10)
        
        # Analyze project context
        project_context = await self.context_analyzer.analyze_project_context(
            current_dir=raw_context.get('current_directory') if raw_context else None
        )
        
        # Get user preferences
        user_preferences = await self.session_memory.get_user_preferences()
        
        # Get recent files from context or session
        recent_files = []
        if raw_context and 'recent_files' in raw_context:
            recent_files = raw_context['recent_files']
        else:
            recent_files = await self._extract_recent_files_from_history(session_history)
        
        return DecisionContext(
            user_input=intent.raw_input,
            intent=intent,
            session_history=session_history,
            project_context=project_context,
            user_preferences=user_preferences,
            current_directory=raw_context.get('current_directory') if raw_context else None,
            recent_files=recent_files
        )
    
    async def _apply_context_enhancements(self, intent: Intent, context: DecisionContext) -> Intent:
        """Apply context-aware enhancements to the intent."""
        
        enhanced_parameters = intent.parameters.copy()
        enhanced_confidence = intent.confidence
        
        # File path inference
        if intent.type in [IntentType.CODE_EXPLAIN, IntentType.CODE_REVIEW, IntentType.FILE_READ]:
            if 'file_path' not in enhanced_parameters:
                inferred_path = await self._infer_file_path(intent, context)
                if inferred_path:
                    enhanced_parameters['file_path'] = inferred_path
                    enhanced_confidence = min(1.0, enhanced_confidence + 0.2)
        
        # Language inference
        if intent.type in [IntentType.CODE_GENERATE, IntentType.CODE_EXPLAIN]:
            if 'language' not in enhanced_parameters:
                inferred_language = await self._infer_language(intent, context)
                if inferred_language:
                    enhanced_parameters['language'] = inferred_language
                    enhanced_confidence = min(1.0, enhanced_confidence + 0.1)
        
        # Framework inference for generation
        if intent.type == IntentType.CODE_GENERATE:
            if 'framework' not in enhanced_parameters:
                inferred_framework = await self._infer_framework(intent, context)
                if inferred_framework:
                    enhanced_parameters['framework'] = inferred_framework
        
        # Context-based focus for reviews
        if intent.type == IntentType.CODE_REVIEW:
            if 'focus' not in enhanced_parameters:
                suggested_focus = await self._suggest_review_focus(intent, context)
                if suggested_focus:
                    enhanced_parameters['focus'] = suggested_focus
        
        # Template inference for generation
        if intent.type == IntentType.CODE_GENERATE:
            if 'template' not in enhanced_parameters:
                suggested_template = await self._suggest_template(intent, context)
                if suggested_template:
                    enhanced_parameters['template'] = suggested_template
        
        # Return enhanced intent
        return Intent(
            type=intent.type,
            confidence=enhanced_confidence,
            parameters=enhanced_parameters,
            raw_input=intent.raw_input,
            context_hints=intent.context_hints
        )
    
    async def _infer_file_path(self, intent: Intent, context: DecisionContext) -> Optional[str]:
        """Infer file path from context."""
        
        # Check if user mentioned a file in input
        import re
        file_patterns = [
            r'([^\s]+\.(py|js|java|cpp|c|go|rs|php|rb|kt|swift|ts|jsx|tsx|vue|html|css|scss|less|json|yaml|yml|xml|md|txt))\b',
            r'([^\s/]+/[^\s]+\.(py|js|java|cpp|c|go|rs|php|rb|kt|swift|ts|jsx|tsx|vue|html|css|scss|less|json|yaml|yml|xml|md|txt))\b'
        ]
        
        for pattern in file_patterns:
            match = re.search(pattern, intent.raw_input)
            if match:
                return match.group(1)
        
        # Check recent files from context
        if context.recent_files:
            # If user said "this file" or similar, use most recent
            if any(word in intent.raw_input.lower() for word in ['this file', 'current file', 'the file']):
                return context.recent_files[0]
        
        # Check session history for recent file operations
        for interaction in context.session_history:
            if interaction.get('type') in ['file_read', 'code_explain', 'code_review']:
                if 'file_path' in interaction.get('parameters', {}):
                    return interaction['parameters']['file_path']
        
        return None
    
    async def _infer_language(self, intent: Intent, context: DecisionContext) -> Optional[str]:
        """Infer programming language from context."""
        
        # Check explicit mentions
        language_keywords = {
            'python': ['python', 'py', '.py', 'django', 'flask', 'pytest'],
            'javascript': ['javascript', 'js', '.js', 'node', 'npm', 'react', 'vue', 'angular'],
            'typescript': ['typescript', 'ts', '.ts', '.tsx'],
            'java': ['java', '.java', 'spring', 'maven', 'gradle'],
            'go': ['go', 'golang', '.go'],
            'rust': ['rust', '.rs', 'cargo'],
            'cpp': ['c++', 'cpp', '.cpp', '.cc', '.cxx'],
            'c': [' c ', '.c ', 'gcc'],
            'php': ['php', '.php', 'laravel', 'symfony'],
            'ruby': ['ruby', '.rb', 'rails', 'gem']
        }
        
        input_lower = intent.raw_input.lower()
        for language, keywords in language_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return language
        
        # Infer from project context
        if context.project_context.get('primary_language'):
            return context.project_context['primary_language']
        
        # Infer from recent files
        if context.recent_files:
            file_extensions = {
                '.py': 'python',
                '.js': 'javascript', 
                '.ts': 'typescript',
                '.tsx': 'typescript',
                '.jsx': 'javascript',
                '.java': 'java',
                '.go': 'go',
                '.rs': 'rust',
                '.cpp': 'cpp',
                '.cc': 'cpp',
                '.c': 'c',
                '.php': 'php',
                '.rb': 'ruby'
            }
            
            for file_path in context.recent_files:
                for ext, lang in file_extensions.items():
                    if file_path.endswith(ext):
                        return lang
        
        # Check user preferences
        if context.user_preferences.get('preferred_language'):
            return context.user_preferences['preferred_language']
        
        return None
    
    async def _infer_framework(self, intent: Intent, context: DecisionContext) -> Optional[str]:
        """Infer framework from context."""
        
        framework_keywords = {
            'react': ['react', 'jsx', 'tsx', 'next.js', 'nextjs'],
            'vue': ['vue', 'vuejs', 'nuxt'],
            'angular': ['angular', '@angular'],
            'django': ['django', 'models.py', 'views.py'],
            'flask': ['flask', 'app.py', '@app.route'],
            'express': ['express', 'app.js', 'server.js'],
            'spring': ['spring', '@Controller', '@Service'],
            'laravel': ['laravel', 'artisan', 'composer.json']
        }
        
        input_lower = intent.raw_input.lower()
        for framework, keywords in framework_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return framework
        
        # Check project context
        if context.project_context.get('frameworks'):
            return context.project_context['frameworks'][0]  # Return primary framework
        
        return None
    
    async def _suggest_review_focus(self, intent: Intent, context: DecisionContext) -> Optional[str]:
        """Suggest review focus based on context."""
        
        # Check explicit mentions
        focus_keywords = {
            'security': ['security', 'secure', 'vulnerability', 'safe', 'auth', 'password'],
            'performance': ['performance', 'speed', 'fast', 'slow', 'optimize', 'efficient'],
            'style': ['style', 'format', 'clean', 'readable', 'convention'],
            'bugs': ['bug', 'error', 'issue', 'problem', 'broken', 'fix']
        }
        
        input_lower = intent.raw_input.lower()
        for focus, keywords in focus_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return focus
        
        # Default based on file type or project context
        if context.recent_files:
            # Security focus for auth/login related files
            if any('auth' in f.lower() or 'login' in f.lower() or 'security' in f.lower() 
                   for f in context.recent_files):
                return 'security'
        
        return 'all'  # Default to comprehensive review
    
    async def _suggest_template(self, intent: Intent, context: DecisionContext) -> Optional[str]:
        """Suggest code template based on context."""
        
        template_keywords = {
            'function': ['function', 'method', 'def ', 'func '],
            'class': ['class', 'object', 'struct'],
            'api_endpoint': ['api', 'endpoint', 'route', 'controller', 'handler'],
            'component': ['component', 'widget', 'element'],
            'app': ['app', 'application', 'program', 'project']
        }
        
        input_lower = intent.raw_input.lower()
        for template, keywords in template_keywords.items():
            if any(keyword in input_lower for keyword in keywords):
                return template
        
        return None
    
    async def _extract_recent_files_from_history(self, history: List[Dict[str, Any]]) -> List[str]:
        """Extract recent files from session history."""
        recent_files = []
        
        for interaction in history:
            if 'parameters' in interaction and 'file_path' in interaction['parameters']:
                file_path = interaction['parameters']['file_path']
                if file_path not in recent_files:
                    recent_files.append(file_path)
        
        return recent_files[:5]  # Return up to 5 recent files
    
    async def _record_decision(self, enhanced_intent: Intent, context: DecisionContext) -> None:
        """Record decision for learning purposes."""
        decision_record = {
            'timestamp': context.timestamp.isoformat(),
            'original_input': context.user_input,
            'intent_type': enhanced_intent.type.value,
            'confidence': enhanced_intent.confidence,
            'enhancements_applied': {
                'parameters_added': list(set(enhanced_intent.parameters.keys()) - set(context.intent.parameters.keys())),
                'confidence_boost': enhanced_intent.confidence - context.intent.confidence
            },
            'context_factors': {
                'had_project_context': bool(context.project_context),
                'had_session_history': len(context.session_history) > 0,
                'had_recent_files': len(context.recent_files) > 0
            }
        }
        
        self.decision_history.append(decision_record)
        
        # Keep only recent decisions (last 100)
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
        
        # Save to session memory for persistence
        await self.session_memory.record_interaction({
            'type': 'decision',
            'timestamp': decision_record['timestamp'],
            'data': decision_record
        })
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """Get statistics about decision making."""
        if not self.decision_history:
            return {'total_decisions': 0}
        
        total = len(self.decision_history)
        confidence_boosts = [d['enhancements_applied']['confidence_boost'] for d in self.decision_history]
        
        return {
            'total_decisions': total,
            'average_confidence_boost': sum(confidence_boosts) / len(confidence_boosts),
            'decisions_with_enhancements': len([d for d in self.decision_history 
                                              if d['enhancements_applied']['parameters_added']]),
            'most_common_intent_types': self._get_most_common_intents(),
            'context_utilization': {
                'project_context_usage': len([d for d in self.decision_history 
                                             if d['context_factors']['had_project_context']]) / total,
                'session_history_usage': len([d for d in self.decision_history 
                                             if d['context_factors']['had_session_history']]) / total,
                'recent_files_usage': len([d for d in self.decision_history 
                                          if d['context_factors']['had_recent_files']]) / total
            }
        }
    
    def _get_most_common_intents(self) -> Dict[str, int]:
        """Get most common intent types from decision history."""
        intent_counts = {}
        for decision in self.decision_history:
            intent_type = decision['intent_type']
            intent_counts[intent_type] = intent_counts.get(intent_type, 0) + 1
        
        # Sort by count and return top 5
        sorted_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_intents[:5])