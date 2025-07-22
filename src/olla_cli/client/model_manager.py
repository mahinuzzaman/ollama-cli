"""Model management for Olla CLI."""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .ollama_client import OllamaClient
from ..core import ModelNotFoundError, ContextLimitExceededError


logger = logging.getLogger('olla-cli')


@dataclass
class ModelInfo:
    """Model information container."""
    name: str
    size: int
    digest: str
    family: str
    parameter_size: str
    quantization_level: str
    context_length: int = 4096
    capabilities: List[str] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []


class ModelManager:
    """Manages model selection, validation, and context limits."""
    
    # Known model context limits
    MODEL_CONTEXT_LIMITS = {
        'llama2': 4096,
        'llama2:7b': 4096,
        'llama2:13b': 4096,
        'llama2:70b': 4096,
        'codellama': 16384,
        'codellama:7b': 16384,
        'codellama:13b': 16384,
        'codellama:34b': 16384,
        'mistral': 8192,
        'mistral:7b': 8192,
        'mixtral': 32768,
        'mixtral:8x7b': 32768,
        'neural-chat': 4096,
        'starling-lm': 8192,
        'openchat': 8192,
        'vicuna': 4096,
        'orca-mini': 4096,
        'phind-codellama': 16384,
        'wizard-coder': 16384,
        'llama3': 8192,
        'llama3.1': 131072,
        'llama3.2': 131072,
        'qwen': 32768,
        'gemma': 8192,
    }
    
    # Model family detection patterns
    FAMILY_PATTERNS = {
        'llama': r'llama\d*',
        'codellama': r'code[\-_]?llama',
        'mistral': r'mistral',
        'mixtral': r'mixtral',
        'gemma': r'gemma',
        'qwen': r'qwen',
        'vicuna': r'vicuna',
        'orca': r'orca',
        'neural-chat': r'neural[\-_]?chat',
        'starling': r'starling',
        'openchat': r'openchat',
        'phind': r'phind',
        'wizard': r'wizard',
    }
    
    def __init__(self, client: OllamaClient):
        """Initialize ModelManager.
        
        Args:
            client: OllamaClient instance
        """
        self.client = client
        self._available_models: List[ModelInfo] = []
        self._models_cache_valid = False
    
    def refresh_models(self) -> None:
        """Refresh the list of available models."""
        try:
            models_data = self.client.list_models()
            self._available_models = []
            
            for model_data in models_data:
                model_info = self._parse_model_data(model_data)
                self._available_models.append(model_info)
            
            self._models_cache_valid = True
            logger.info(f"Refreshed model list: {len(self._available_models)} models available")
            
        except Exception as e:
            logger.error(f"Failed to refresh models: {e}")
            raise
    
    def _parse_model_data(self, model_data: Dict[str, Any]) -> ModelInfo:
        """Parse model data from Ollama API response.
        
        Args:
            model_data: Raw model data from API
            
        Returns:
            ModelInfo object
        """
        name = model_data.get('name', '')
        size = model_data.get('size', 0)
        digest = model_data.get('digest', '')
        
        # Extract family and parameter info from name
        family = self._detect_model_family(name)
        parameter_size = self._extract_parameter_size(name)
        quantization_level = self._extract_quantization_level(name)
        
        # Determine context length
        context_length = self._get_model_context_limit(name)
        
        # Determine capabilities based on model family
        capabilities = self._determine_capabilities(family, name)
        
        return ModelInfo(
            name=name,
            size=size,
            digest=digest,
            family=family,
            parameter_size=parameter_size,
            quantization_level=quantization_level,
            context_length=context_length,
            capabilities=capabilities
        )
    
    def _detect_model_family(self, model_name: str) -> str:
        """Detect model family from name.
        
        Args:
            model_name: Model name
            
        Returns:
            Model family name
        """
        name_lower = model_name.lower()
        
        for family, pattern in self.FAMILY_PATTERNS.items():
            if re.search(pattern, name_lower):
                return family
        
        return 'unknown'
    
    def _extract_parameter_size(self, model_name: str) -> str:
        """Extract parameter size from model name.
        
        Args:
            model_name: Model name
            
        Returns:
            Parameter size string
        """
        # Look for patterns like :7b, :13b, :70b, etc.
        match = re.search(r':(\d+\.?\d*[bBmM])', model_name.lower())
        if match:
            return match.group(1).upper()
        
        # Look for patterns like -7B, -13B, etc.
        match = re.search(r'[-_](\d+\.?\d*[bBmM])', model_name.lower())
        if match:
            return match.group(1).upper()
        
        return 'unknown'
    
    def _extract_quantization_level(self, model_name: str) -> str:
        """Extract quantization level from model name.
        
        Args:
            model_name: Model name
            
        Returns:
            Quantization level
        """
        name_lower = model_name.lower()
        
        if 'q4_0' in name_lower or 'q4-0' in name_lower:
            return 'Q4_0'
        elif 'q4_1' in name_lower or 'q4-1' in name_lower:
            return 'Q4_1'
        elif 'q5_0' in name_lower or 'q5-0' in name_lower:
            return 'Q5_0'
        elif 'q5_1' in name_lower or 'q5-1' in name_lower:
            return 'Q5_1'
        elif 'q8_0' in name_lower or 'q8-0' in name_lower:
            return 'Q8_0'
        elif 'f16' in name_lower:
            return 'F16'
        elif 'f32' in name_lower:
            return 'F32'
        
        return 'unknown'
    
    def _get_model_context_limit(self, model_name: str) -> int:
        """Get context limit for a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Context limit in tokens
        """
        name_lower = model_name.lower()
        
        # Check exact matches first
        if name_lower in self.MODEL_CONTEXT_LIMITS:
            return self.MODEL_CONTEXT_LIMITS[name_lower]
        
        # Check family-based matches
        for model_pattern, context_limit in self.MODEL_CONTEXT_LIMITS.items():
            if model_pattern in name_lower:
                return context_limit
        
        # Default context limit
        return 4096
    
    def _determine_capabilities(self, family: str, model_name: str) -> List[str]:
        """Determine model capabilities based on family and name.
        
        Args:
            family: Model family
            model_name: Model name
            
        Returns:
            List of capabilities
        """
        capabilities = ['chat', 'completion']
        
        # Code-specific models
        if 'code' in family or 'code' in model_name.lower():
            capabilities.extend(['code_generation', 'code_explanation', 'code_review'])
        
        # Chat-specific models
        if 'chat' in family or 'chat' in model_name.lower():
            capabilities.append('conversation')
        
        # Instruction-following models
        if any(keyword in model_name.lower() for keyword in ['instruct', 'chat', 'assistant']):
            capabilities.append('instruction_following')
        
        return capabilities
    
    def get_available_models(self, refresh: bool = False) -> List[ModelInfo]:
        """Get list of available models.
        
        Args:
            refresh: Whether to refresh the model list
            
        Returns:
            List of ModelInfo objects
        """
        if refresh or not self._models_cache_valid:
            self.refresh_models()
        
        return self._available_models.copy()
    
    def validate_model(self, model_name: str) -> ModelInfo:
        """Validate that a model exists and return its info.
        
        Args:
            model_name: Model name to validate
            
        Returns:
            ModelInfo for the model
            
        Raises:
            ModelNotFoundError: If model not found
        """
        if not self._models_cache_valid:
            self.refresh_models()
        
        for model in self._available_models:
            if model.name == model_name:
                logger.debug(f"Model validated: {model_name}")
                return model
        
        # Try to get model info directly from Ollama
        try:
            model_data = self.client.get_model_info(model_name)
            logger.info(f"Model found via direct query: {model_name}")
            # Create a basic ModelInfo for this model
            return ModelInfo(
                name=model_name,
                size=0,
                digest='',
                family=self._detect_model_family(model_name),
                parameter_size=self._extract_parameter_size(model_name),
                quantization_level=self._extract_quantization_level(model_name),
                context_length=self._get_model_context_limit(model_name),
                capabilities=self._determine_capabilities(self._detect_model_family(model_name), model_name)
            )
        except Exception:
            pass
        
        raise ModelNotFoundError(f"Model '{model_name}' not found")
    
    def get_best_model_for_task(self, task: str, available_models: Optional[List[str]] = None) -> str:
        """Get the best model for a specific task.
        
        Args:
            task: Task name (e.g., 'code', 'chat', 'explain')
            available_models: List of available model names to choose from
            
        Returns:
            Best model name for the task
        """
        if not self._models_cache_valid:
            self.refresh_models()
        
        models = self._available_models
        if available_models:
            models = [m for m in models if m.name in available_models]
        
        if not models:
            raise ModelNotFoundError("No models available")
        
        # Task-specific model preferences
        task_preferences = {
            'code': ['codellama', 'phind', 'wizard'],
            'explain': ['codellama', 'llama'],
            'review': ['codellama', 'phind'],
            'refactor': ['codellama', 'wizard'],
            'debug': ['codellama', 'phind'],
            'generate': ['codellama', 'wizard'],
            'test': ['codellama', 'phind'],
            'document': ['llama', 'codellama'],
            'chat': ['llama', 'mistral', 'openchat']
        }
        
        preferred_families = task_preferences.get(task, ['llama'])
        
        # Score models based on task preferences
        scored_models = []
        for model in models:
            score = 0
            
            # Family preference score
            for i, family in enumerate(preferred_families):
                if family in model.family:
                    score += (len(preferred_families) - i) * 10
                    break
            
            # Capability score
            task_capability_map = {
                'code': 'code_generation',
                'explain': 'code_explanation',
                'review': 'code_review',
                'chat': 'conversation'
            }
            
            required_capability = task_capability_map.get(task)
            if required_capability and required_capability in model.capabilities:
                score += 5
            
            # Parameter size preference (larger is generally better)
            param_size = model.parameter_size.lower()
            if 'b' in param_size:
                try:
                    size_num = float(param_size.replace('b', ''))
                    if size_num >= 13:
                        score += 3
                    elif size_num >= 7:
                        score += 2
                    else:
                        score += 1
                except ValueError:
                    pass
            
            scored_models.append((score, model))
        
        # Sort by score (descending) and return the best model
        scored_models.sort(key=lambda x: x[0], reverse=True)
        best_model = scored_models[0][1]
        
        logger.info(f"Selected model '{best_model.name}' for task '{task}'")
        return best_model.name
    
    def check_context_limit(self, model_name: str, text: str, max_tokens: int = 0) -> Tuple[bool, int, int]:
        """Check if text fits within model's context limit.
        
        Args:
            model_name: Model name
            text: Text to check
            max_tokens: Additional tokens for response
            
        Returns:
            Tuple of (fits, estimated_tokens, context_limit)
            
        Raises:
            ModelNotFoundError: If model not found
        """
        model_info = self.validate_model(model_name)
        context_limit = model_info.context_length
        
        # Rough token estimation (1 token ≈ 4 characters)
        estimated_tokens = len(text) // 4
        total_needed = estimated_tokens + max_tokens
        
        fits = total_needed <= context_limit
        
        logger.debug(f"Context check for {model_name}: {estimated_tokens} + {max_tokens} = {total_needed} / {context_limit}")
        
        return fits, estimated_tokens, context_limit
    
    def truncate_to_context_limit(self, model_name: str, text: str, max_response_tokens: int = 1000) -> str:
        """Truncate text to fit within model's context limit.
        
        Args:
            model_name: Model name
            text: Text to truncate
            max_response_tokens: Tokens reserved for response
            
        Returns:
            Truncated text
            
        Raises:
            ModelNotFoundError: If model not found
        """
        model_info = self.validate_model(model_name)
        context_limit = model_info.context_length
        
        # Reserve space for response and system messages
        available_tokens = context_limit - max_response_tokens - 100  # 100 for system overhead
        
        if available_tokens <= 0:
            raise ContextLimitExceededError(f"Model {model_name} context too small for response tokens")
        
        # Rough token estimation and truncation
        estimated_chars = available_tokens * 4
        
        if len(text) <= estimated_chars:
            return text
        
        # Truncate with ellipsis
        truncated = text[:estimated_chars - 100] + "\n\n[... text truncated to fit context limit ...]"
        
        logger.warning(f"Text truncated from {len(text)} to {len(truncated)} characters for model {model_name}")
        
        return truncated