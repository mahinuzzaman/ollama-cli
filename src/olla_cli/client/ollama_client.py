"""Ollama API client for Olla CLI."""

import asyncio
import time
import logging
from typing import Dict, List, Any, Optional, Iterator, AsyncIterator, Union
from urllib.parse import urljoin
import aiohttp
import ollama
from ollama import Client as OllamaSDK

from ..core import (
    OllamaConnectionError, OllamaServerError, ModelNotFoundError, 
    ModelPullError, StreamingError, TimeoutError
)


logger = logging.getLogger('olla-cli')


class OllamaClient:
    """Wrapper client for Ollama API with enhanced error handling and retry logic."""
    
    def __init__(self, host: str = "http://localhost:11434", timeout: int = 30):
        """Initialize Ollama client.
        
        Args:
            host: Ollama server URL
            timeout: Request timeout in seconds
        """
        self.host = host
        self.timeout = timeout
        self._client = OllamaSDK(host=host)
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    def test_connection(self) -> bool:
        """Test connection to Ollama server.
        
        Returns:
            True if connection successful
            
        Raises:
            OllamaConnectionError: If connection fails
        """
        max_retries = 3
        base_delay = 1.0
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                response = self._client.list()
                logger.info("Connection to Ollama server successful")
                return True
            except (ConnectionError, Exception) as e:
                last_exception = e
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_retries + 1} connection attempts failed")
                    break
        
        raise OllamaConnectionError(f"Cannot connect to Ollama server at {self.host}: {last_exception}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models.
        
        Returns:
            List of model dictionaries
            
        Raises:
            OllamaConnectionError: If request fails
        """
        try:
            response = self._client.list()
            models = response.get('models', [])
            logger.info(f"Retrieved {len(models)} models")
            return models
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise OllamaConnectionError(f"Failed to list models: {e}")
    
    def pull_model(self, model: str, stream: bool = True) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Pull a model from Ollama registry.
        
        Args:
            model: Model name to pull
            stream: Whether to stream the pull progress
            
        Returns:
            Pull response or iterator of progress updates
            
        Raises:
            ModelPullError: If pull fails
        """
        try:
            logger.info(f"Pulling model: {model}")
            if stream:
                return self._client.pull(model, stream=True)
            else:
                response = self._client.pull(model, stream=False)
                logger.info(f"Successfully pulled model: {model}")
                return response
        except Exception as e:
            logger.error(f"Failed to pull model {model}: {e}")
            raise ModelPullError(f"Failed to pull model {model}: {e}")
    
    def get_model_info(self, model: str) -> Dict[str, Any]:
        """Get information about a specific model.
        
        Args:
            model: Model name
            
        Returns:
            Model information dictionary
            
        Raises:
            ModelNotFoundError: If model not found
            OllamaServerError: If server error occurs
        """
        try:
            response = self._client.show(model)
            logger.debug(f"Retrieved info for model: {model}")
            return response
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "404" in error_msg:
                raise ModelNotFoundError(f"Model '{model}' not found")
            logger.error(f"Failed to get model info for {model}: {e}")
            raise OllamaServerError(f"Failed to get model info: {e}")
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Union[Dict[str, Any], Iterator[Dict[str, Any]]]:
        """Send chat request to Ollama.
        
        Args:
            model: Model name to use
            messages: List of message dictionaries
            stream: Whether to stream response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Chat response or iterator for streaming
            
        Raises:
            ModelNotFoundError: If model not found
            OllamaServerError: If server error occurs
            StreamingError: If streaming fails
        """
        options = {}
        if temperature is not None:
            options['temperature'] = temperature
        if max_tokens is not None:
            options['num_predict'] = max_tokens
        
        options.update(kwargs)
        
        try:
            logger.debug(f"Sending chat request to model: {model}")
            
            if stream:
                return self._stream_chat(model, messages, options)
            else:
                response = self._client.chat(
                    model=model,
                    messages=messages,
                    options=options,
                    stream=False
                )
                logger.debug("Chat request completed successfully")
                return response
                
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "model" in error_msg:
                raise ModelNotFoundError(f"Model '{model}' not found")
            logger.error(f"Chat request failed: {e}")
            raise OllamaServerError(f"Chat request failed: {e}")
    
    def _stream_chat(self, model: str, messages: List[Dict[str, str]], options: Dict[str, Any]) -> Iterator[Dict[str, Any]]:
        """Handle streaming chat response.
        
        Args:
            model: Model name
            messages: Chat messages
            options: Request options
            
        Yields:
            Response chunks
            
        Raises:
            StreamingError: If streaming fails
        """
        try:
            stream = self._client.chat(
                model=model,
                messages=messages,
                options=options,
                stream=True
            )
            
            for chunk in stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            raise StreamingError(f"Streaming failed: {e}")
    
    async def async_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Async chat request to Ollama.
        
        Args:
            model: Model name to use
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Chat response
            
        Raises:
            ModelNotFoundError: If model not found
            OllamaServerError: If server error occurs
        """
        if not self._session:
            raise RuntimeError("Async session not initialized. Use async context manager.")
        
        options = {}
        if temperature is not None:
            options['temperature'] = temperature
        if max_tokens is not None:
            options['num_predict'] = max_tokens
        options.update(kwargs)
        
        url = urljoin(self.host, '/api/chat')
        payload = {
            'model': model,
            'messages': messages,
            'options': options,
            'stream': False
        }
        
        try:
            logger.debug(f"Sending async chat request to model: {model}")
            
            async with self._session.post(url, json=payload) as response:
                if response.status == 404:
                    raise ModelNotFoundError(f"Model '{model}' not found")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise OllamaServerError(f"Server error {response.status}: {error_text}")
                
                result = await response.json()
                logger.debug("Async chat request completed successfully")
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"Async chat request failed: {e}")
            raise OllamaServerError(f"Async chat request failed: {e}")
    
    async def async_stream_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        """Async streaming chat request.
        
        Args:
            model: Model name to use
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
            
        Raises:
            ModelNotFoundError: If model not found
            StreamingError: If streaming fails
        """
        if not self._session:
            raise RuntimeError("Async session not initialized. Use async context manager.")
        
        options = {}
        if temperature is not None:
            options['temperature'] = temperature
        if max_tokens is not None:
            options['num_predict'] = max_tokens
        options.update(kwargs)
        
        url = urljoin(self.host, '/api/chat')
        payload = {
            'model': model,
            'messages': messages,
            'options': options,
            'stream': True
        }
        
        try:
            logger.debug(f"Starting async streaming chat with model: {model}")
            
            async with self._session.post(url, json=payload) as response:
                if response.status == 404:
                    raise ModelNotFoundError(f"Model '{model}' not found")
                elif response.status >= 400:
                    error_text = await response.text()
                    raise StreamingError(f"Streaming failed {response.status}: {error_text}")
                
                async for line in response.content:
                    if line:
                        try:
                            import json
                            chunk = json.loads(line.decode('utf-8').strip())
                            yield chunk
                        except json.JSONDecodeError:
                            continue
                            
        except aiohttp.ClientError as e:
            logger.error(f"Async streaming failed: {e}")
            raise StreamingError(f"Async streaming failed: {e}")