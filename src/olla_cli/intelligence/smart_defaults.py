"""Smart Defaults System for intelligent parameter inference."""

from typing import Dict, Any, Optional, List, Tuple
import logging

from ..routing.intent import Intent, IntentType
from .session_memory import SessionMemory

logger = logging.getLogger('olla-cli.intelligence.defaults')


class SmartDefaultsSystem:
    """Applies intelligent defaults based on context and user preferences."""
    
    def __init__(self, session_memory: Optional[SessionMemory] = None):
        self.session_memory = session_memory or SessionMemory()
        self.default_rules = self._initialize_default_rules()
        
    def _initialize_default_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize default rules for different intent types."""
        return {
            'code_generate': {
                'language': 'python',
                'style': 'clean',
                'include_tests': False,
                'include_docs': True,
                'framework': None
            },
            'code_explain': {
                'detail_level': 'normal',
                'include_examples': True,
                'focus_areas': ['functionality', 'logic']
            },
            'code_review': {
                'focus': 'all',
                'severity_threshold': 'medium',
                'include_suggestions': True,
                'check_performance': True,
                'check_security': True,
                'check_style': True
            },
            'code_refactor': {
                'preserve_functionality': True,
                'improve_readability': True,
                'optimize_performance': False,
                'update_patterns': True
            },
            'code_debug': {
                'include_traces': True,
                'suggest_fixes': True,
                'check_common_issues': True
            },
            'code_test': {
                'test_type': 'unit',
                'coverage_target': 80,
                'include_edge_cases': True,
                'mock_dependencies': True
            },
            'file_operations': {
                'backup_before_modify': True,
                'preserve_permissions': True,
                'validate_changes': True
            }
        }
    
    async def apply_defaults(self, intent: Intent, context) -> Intent:
        """Apply smart defaults to an intent based on context."""
        # Import here to avoid circular imports
        from .decision_engine import DecisionContext
        
        enhanced_parameters = intent.parameters.copy()
        
        # Get user preferences
        user_prefs = await self.session_memory.get_user_preferences()
        
        # Apply intent-specific defaults
        intent_defaults = await self._get_intent_defaults(intent, context, user_prefs)
        
        # Apply defaults without overriding existing parameters
        for key, default_value in intent_defaults.items():
            if key not in enhanced_parameters:
                enhanced_parameters[key] = default_value
        
        # Apply context-specific defaults
        context_defaults = await self._get_context_defaults(intent, context, user_prefs)
        for key, default_value in context_defaults.items():
            if key not in enhanced_parameters:
                enhanced_parameters[key] = default_value
        
        # Apply user preference defaults
        pref_defaults = await self._get_preference_defaults(intent, user_prefs)
        for key, default_value in pref_defaults.items():
            if key not in enhanced_parameters:
                enhanced_parameters[key] = default_value
        
        # Apply smart inference defaults
        smart_defaults = await self._get_smart_inference_defaults(intent, context)
        for key, default_value in smart_defaults.items():
            if key not in enhanced_parameters:
                enhanced_parameters[key] = default_value
        
        return Intent(
            type=intent.type,
            confidence=intent.confidence,
            parameters=enhanced_parameters,
            raw_input=intent.raw_input,
            context_hints=intent.context_hints
        )
    
    async def _get_intent_defaults(self, intent: Intent, context, user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Get defaults specific to the intent type."""
        intent_key = intent.type.value.lower().replace('_', '_')
        
        # Map intent types to rule keys
        rule_mapping = {
            'code_generate': 'code_generate',
            'code_explain': 'code_explain', 
            'code_review': 'code_review',
            'code_refactor': 'code_refactor',
            'code_debug': 'code_debug',
            'code_test': 'code_test',
            'file_read': 'file_operations',
            'file_write': 'file_operations',
            'file_create': 'file_operations'
        }
        
        rule_key = rule_mapping.get(intent_key, 'general')
        return self.default_rules.get(rule_key, {}).copy()
    
    async def _get_context_defaults(self, intent: Intent, context, user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Get defaults based on project context."""
        # Import here to avoid circular imports
        from .decision_engine import DecisionContext
        
        if not isinstance(context, DecisionContext):
            return {}
        
        defaults = {}
        
        # Language defaults from project context
        if intent.type in [IntentType.CODE_GENERATE, IntentType.CODE_EXPLAIN]:
            if context.project_context.get('primary_language'):
                defaults['language'] = context.project_context['primary_language']
        
        # Framework defaults
        if intent.type == IntentType.CODE_GENERATE:
            frameworks = context.project_context.get('frameworks', [])
            if frameworks:
                defaults['framework'] = frameworks[0]  # Use primary framework
        
        # File extension based defaults
        if context.recent_files:
            most_recent = context.recent_files[0]
            file_ext = most_recent.split('.')[-1].lower() if '.' in most_recent else ''
            
            if intent.type == IntentType.CODE_GENERATE:
                ext_to_lang = {
                    'py': 'python',
                    'js': 'javascript',
                    'ts': 'typescript',
                    'java': 'java',
                    'go': 'go',
                    'rs': 'rust',
                    'cpp': 'cpp',
                    'c': 'c',
                    'php': 'php',
                    'rb': 'ruby'
                }
                if file_ext in ext_to_lang:
                    defaults['language'] = ext_to_lang[file_ext]
        
        # Project type specific defaults
        project_type = context.project_context.get('project_type')
        if project_type == 'react_app' and intent.type == IntentType.CODE_GENERATE:
            defaults['framework'] = 'react'
            defaults['language'] = 'javascript'
        elif project_type == 'vue_app' and intent.type == IntentType.CODE_GENERATE:
            defaults['framework'] = 'vue'
            defaults['language'] = 'javascript'
        elif project_type == 'python_package' and intent.type == IntentType.CODE_GENERATE:
            defaults['language'] = 'python'
            defaults['include_tests'] = True
        
        return defaults
    
    async def _get_preference_defaults(self, intent: Intent, user_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Get defaults based on user preferences."""
        defaults = {}
        
        # Language preferences
        if intent.type in [IntentType.CODE_GENERATE, IntentType.CODE_EXPLAIN]:
            if user_prefs.get('preferred_language'):
                defaults['language'] = user_prefs['preferred_language']
        
        # Framework preferences
        if intent.type == IntentType.CODE_GENERATE:
            if user_prefs.get('preferred_framework'):
                defaults['framework'] = user_prefs['preferred_framework']
        
        # Review preferences
        if intent.type == IntentType.CODE_REVIEW:
            review_prefs = user_prefs.get('review_preferences', {})
            defaults.update(review_prefs)
        
        # Code style preferences
        if intent.type in [IntentType.CODE_GENERATE, IntentType.CODE_REFACTOR]:
            style_prefs = user_prefs.get('code_style', {})
            defaults.update(style_prefs)
        
        # Testing preferences
        if intent.type == IntentType.CODE_TEST:
            test_prefs = user_prefs.get('testing_preferences', {})
            defaults.update(test_prefs)
        
        return defaults
    
    async def _get_smart_inference_defaults(self, intent: Intent, context) -> Dict[str, Any]:
        """Get defaults through smart inference from various sources."""
        # Import here to avoid circular imports
        from .decision_engine import DecisionContext
        
        if not isinstance(context, DecisionContext):
            return {}
        
        defaults = {}
        
        # Infer complexity level based on input length
        input_length = len(intent.raw_input)
        if intent.type == IntentType.CODE_GENERATE:
            if input_length < 50:
                defaults['complexity'] = 'simple'
            elif input_length < 200:
                defaults['complexity'] = 'moderate'
            else:
                defaults['complexity'] = 'complex'
        
        # Infer detail level for explanations
        if intent.type == IntentType.CODE_EXPLAIN:
            if any(word in intent.raw_input.lower() for word in ['simple', 'brief', 'quick']):
                defaults['detail_level'] = 'brief'
            elif any(word in intent.raw_input.lower() for word in ['detailed', 'deep', 'thorough']):
                defaults['detail_level'] = 'detailed'
        
        # Infer focus areas for reviews
        if intent.type == IntentType.CODE_REVIEW:
            focus_keywords = {
                'security': ['security', 'safe', 'vulnerability', 'auth'],
                'performance': ['performance', 'speed', 'optimize', 'fast'],
                'style': ['style', 'format', 'clean', 'readable'],
                'bugs': ['bug', 'error', 'issue', 'problem']
            }
            
            input_lower = intent.raw_input.lower()
            detected_focuses = []
            for focus, keywords in focus_keywords.items():
                if any(keyword in input_lower for keyword in keywords):
                    detected_focuses.append(focus)
            
            if detected_focuses:
                defaults['focus'] = detected_focuses[0]  # Use first detected focus
        
        # Infer output format
        if any(word in intent.raw_input.lower() for word in ['json', 'yaml', 'xml']):
            format_word = next(word for word in ['json', 'yaml', 'xml'] 
                             if word in intent.raw_input.lower())
            defaults['output_format'] = format_word
        
        # Infer test type
        if intent.type == IntentType.CODE_TEST:
            if 'unit' in intent.raw_input.lower():
                defaults['test_type'] = 'unit'
            elif 'integration' in intent.raw_input.lower():
                defaults['test_type'] = 'integration'
            elif 'e2e' in intent.raw_input.lower() or 'end-to-end' in intent.raw_input.lower():
                defaults['test_type'] = 'e2e'
        
        return defaults
    
    async def learn_from_interaction(self, intent: Intent, parameters: Dict[str, Any], 
                                   context, success: bool) -> None:
        """Learn from user interactions to improve future defaults."""
        # Import here to avoid circular imports
        from .decision_engine import DecisionContext
        
        if not success:
            return  # Don't learn from failed interactions
        
        # Record successful parameter combinations
        learning_data = {
            'intent_type': intent.type.value,
            'parameters': parameters,
            'context_factors': {}
        }
        
        if isinstance(context, DecisionContext):
            learning_data['context_factors'] = {
                'project_type': context.project_context.get('project_type'),
                'primary_language': context.project_context.get('primary_language'),
                'frameworks': context.project_context.get('frameworks', [])
            }
        
        # Store in session memory for future reference
        await self.session_memory.record_interaction({
            'type': 'parameter_learning',
            'data': learning_data
        })
        
        # Update user preferences based on patterns
        await self._update_preferences_from_learning(intent, parameters, context)
    
    async def _update_preferences_from_learning(self, intent: Intent, parameters: Dict[str, Any], 
                                              context) -> None:
        """Update user preferences based on successful interactions."""
        user_prefs = await self.session_memory.get_user_preferences()
        updates = {}
        
        # Learn language preferences
        if 'language' in parameters:
            lang_usage = user_prefs.get('language_usage', {})
            lang = parameters['language']
            lang_usage[lang] = lang_usage.get(lang, 0) + 1
            updates['language_usage'] = lang_usage
            
            # Update preferred language if this one is becoming dominant
            current_pref = user_prefs.get('preferred_language')
            if not current_pref or lang_usage[lang] > lang_usage.get(current_pref, 0):
                updates['preferred_language'] = lang
        
        # Learn framework preferences  
        if 'framework' in parameters:
            fw_usage = user_prefs.get('framework_usage', {})
            fw = parameters['framework']
            fw_usage[fw] = fw_usage.get(fw, 0) + 1
            updates['framework_usage'] = fw_usage
            
            # Update preferred framework
            current_pref = user_prefs.get('preferred_framework')
            if not current_pref or fw_usage[fw] > fw_usage.get(current_pref, 0):
                updates['preferred_framework'] = fw
        
        # Learn review preferences
        if intent.type == IntentType.CODE_REVIEW:
            review_prefs = user_prefs.get('review_preferences', {})
            for key in ['focus', 'severity_threshold', 'include_suggestions']:
                if key in parameters:
                    review_prefs[key] = parameters[key]
            updates['review_preferences'] = review_prefs
        
        # Learn testing preferences
        if intent.type == IntentType.CODE_TEST:
            test_prefs = user_prefs.get('testing_preferences', {})
            for key in ['test_type', 'coverage_target', 'include_edge_cases']:
                if key in parameters:
                    test_prefs[key] = parameters[key]
            updates['testing_preferences'] = test_prefs
        
        # Save updates
        if updates:
            await self.session_memory.update_user_preferences(updates)
    
    def get_available_defaults(self, intent_type: IntentType) -> Dict[str, Any]:
        """Get available default options for an intent type."""
        intent_key = intent_type.value.lower()
        
        rule_mapping = {
            'code_generate': 'code_generate',
            'code_explain': 'code_explain',
            'code_review': 'code_review',
            'code_refactor': 'code_refactor',
            'code_debug': 'code_debug',
            'code_test': 'code_test'
        }
        
        rule_key = rule_mapping.get(intent_key, 'general')
        return self.default_rules.get(rule_key, {}).copy()
    
    def update_default_rules(self, intent_type: str, new_rules: Dict[str, Any]) -> None:
        """Update default rules for an intent type."""
        if intent_type in self.default_rules:
            self.default_rules[intent_type].update(new_rules)
        else:
            self.default_rules[intent_type] = new_rules
        
        logger.info(f"Updated default rules for {intent_type}")
    
    def get_defaults_stats(self) -> Dict[str, Any]:
        """Get statistics about defaults usage."""
        return {
            'total_rule_types': len(self.default_rules),
            'rules_by_type': {k: len(v) for k, v in self.default_rules.items()},
            'most_used_defaults': self._get_most_used_defaults()
        }
    
    def _get_most_used_defaults(self) -> Dict[str, int]:
        """Get statistics on most commonly used default values."""
        # This would typically be tracked over time
        # For now, return a placeholder
        return {
            'language_python': 0,
            'language_javascript': 0,
            'framework_react': 0,
            'detail_level_normal': 0
        }