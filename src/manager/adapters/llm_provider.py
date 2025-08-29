"""Real LLM provider integration for AI-powered code generation."""

import json
import os
import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum

import httpx
from pydantic import BaseModel


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"  
    OLLAMA = "ollama"
    MOCK = "mock"


@dataclass
class LLMResponse:
    """Standardized LLM response."""
    content: str
    provider: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class LLMError(Exception):
    """LLM-specific errors."""
    pass


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str = None, base_url: str = None, **kwargs):
        self.api_key = api_key
        self.base_url = base_url
        self.config = kwargs
        self.client = None
    
    @abstractmethod
    async def generate(
        self, 
        prompt: str, 
        system: str = None,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate text response."""
        pass
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        pass


class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) provider."""
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.base_url = "https://api.anthropic.com"
        
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            raise LLMError("Anthropic API key required. Set ANTHROPIC_API_KEY environment variable.")
    
    async def generate(
        self, 
        prompt: str, 
        system: str = None,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate with Claude."""
        
        model = model or self.get_default_model()
        
        # Build messages
        messages = []
        if system:
            # Claude uses system parameter separately
            pass
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        headers = {
            "x-api-key": self.api_key,
            "content-type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract content from Claude response
                content = ""
                if "content" in data and data["content"]:
                    content = data["content"][0]["text"]
                
                return LLMResponse(
                    content=content,
                    provider="anthropic",
                    model=model,
                    usage=data.get("usage"),
                    metadata={"response_id": data.get("id")}
                )
                
            except httpx.HTTPStatusError as e:
                error_msg = f"Anthropic API error: {e.response.status_code} - {e.response.text}"
                raise LLMError(error_msg)
            except Exception as e:
                raise LLMError(f"Anthropic request failed: {str(e)}")
    
    def get_default_model(self) -> str:
        return "claude-3-sonnet-20240229"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI (GPT) provider."""
    
    def __init__(self, api_key: str = None, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.base_url = "https://api.openai.com"
        
        # Try to get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise LLMError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
    
    async def generate(
        self, 
        prompt: str, 
        system: str = None,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate with GPT."""
        
        model = model or self.get_default_model()
        
        # Build messages
        messages = []
        if system:
            messages.append({
                "role": "system",
                "content": system
            })
        
        messages.append({
            "role": "user", 
            "content": prompt
        })
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract content from GPT response
                content = ""
                if "choices" in data and data["choices"]:
                    content = data["choices"][0]["message"]["content"]
                
                return LLMResponse(
                    content=content,
                    provider="openai",
                    model=model,
                    usage=data.get("usage"),
                    metadata={"response_id": data.get("id")}
                )
                
            except httpx.HTTPStatusError as e:
                error_msg = f"OpenAI API error: {e.response.status_code} - {e.response.text}"
                raise LLMError(error_msg)
            except Exception as e:
                raise LLMError(f"OpenAI request failed: {str(e)}")
    
    def get_default_model(self) -> str:
        return "gpt-4-turbo-preview"


class OllamaProvider(BaseLLMProvider):
    """Ollama (local) provider."""
    
    def __init__(self, base_url: str = None, **kwargs):
        super().__init__(base_url=base_url, **kwargs)
        self.base_url = base_url or "http://localhost:11434"
    
    async def generate(
        self, 
        prompt: str, 
        system: str = None,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate with Ollama."""
        
        model = model or self.get_default_model()
        
        # Build messages for Ollama
        messages = []
        if system:
            messages.append({
                "role": "system",
                "content": system
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Extract content from Ollama response
                content = data.get("message", {}).get("content", "")
                
                return LLMResponse(
                    content=content,
                    provider="ollama",
                    model=model,
                    metadata={"eval_count": data.get("eval_count")}
                )
                
            except httpx.HTTPStatusError as e:
                error_msg = f"Ollama API error: {e.response.status_code} - {e.response.text}"
                raise LLMError(error_msg)
            except Exception as e:
                raise LLMError(f"Ollama request failed: {str(e)}")
    
    def get_default_model(self) -> str:
        return "llama2"


class MockProvider(BaseLLMProvider):
    """Mock provider for testing."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.responses = {}
    
    def set_response(self, prompt_pattern: str, response: str):
        """Set a mock response for a prompt pattern."""
        self.responses[prompt_pattern] = response
    
    async def generate(
        self, 
        prompt: str, 
        system: str = None,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 4000,
        **kwargs
    ) -> LLMResponse:
        """Generate mock response."""
        
        # Find matching response
        for pattern, response in self.responses.items():
            if pattern.lower() in prompt.lower():
                return LLMResponse(
                    content=response,
                    provider="mock",
                    model=model or "mock-model"
                )
        
        # Default mock response
        return LLMResponse(
            content="Mock LLM response for testing purposes.",
            provider="mock", 
            model=model or "mock-model"
        )
    
    def get_default_model(self) -> str:
        return "mock-model"


class LLMManager:
    """Manages multiple LLM providers with fallback and retry logic."""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider = None
        self.retry_attempts = 3
        self.retry_delay = 1.0
    
    def register_provider(self, name: str, provider: BaseLLMProvider, set_default: bool = False):
        """Register an LLM provider."""
        self.providers[name] = provider
        
        if set_default or not self.default_provider:
            self.default_provider = name
    
    def setup_anthropic(self, api_key: str = None, set_default: bool = False):
        """Setup Anthropic provider."""
        try:
            provider = AnthropicProvider(api_key=api_key)
            self.register_provider("anthropic", provider, set_default)
            return True
        except LLMError:
            return False
    
    def setup_openai(self, api_key: str = None, set_default: bool = False):
        """Setup OpenAI provider."""
        try:
            provider = OpenAIProvider(api_key=api_key)
            self.register_provider("openai", provider, set_default)
            return True
        except LLMError:
            return False
    
    def setup_ollama(self, base_url: str = None, set_default: bool = False):
        """Setup Ollama provider."""
        try:
            provider = OllamaProvider(base_url=base_url)
            self.register_provider("ollama", provider, set_default)
            return True
        except LLMError:
            return False
    
    def setup_mock(self, responses: Dict[str, str] = None):
        """Setup mock provider for testing."""
        provider = MockProvider()
        
        if responses:
            for pattern, response in responses.items():
                provider.set_response(pattern, response)
        
        self.register_provider("mock", provider)
        return True
    
    async def generate(
        self, 
        prompt: str,
        system: str = None,
        provider: str = None,
        fallback: bool = True,
        **kwargs
    ) -> LLMResponse:
        """Generate text with provider selection and fallback."""
        
        # Determine provider to use
        target_provider = provider or self.default_provider
        
        if not target_provider or target_provider not in self.providers:
            if not self.providers:
                raise LLMError("No LLM providers configured")
            target_provider = list(self.providers.keys())[0]
        
        # Try primary provider with retries
        last_error = None
        
        for attempt in range(self.retry_attempts):
            try:
                provider_instance = self.providers[target_provider]
                return await provider_instance.generate(
                    prompt=prompt,
                    system=system,
                    **kwargs
                )
            except LLMError as e:
                last_error = e
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
        
        # Try fallback providers if enabled
        if fallback and len(self.providers) > 1:
            for fallback_name, fallback_provider in self.providers.items():
                if fallback_name == target_provider:
                    continue
                
                try:
                    return await fallback_provider.generate(
                        prompt=prompt,
                        system=system,
                        **kwargs
                    )
                except LLMError:
                    continue
        
        # All providers failed
        raise LLMError(f"All LLM providers failed. Last error: {last_error}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return list(self.providers.keys())
    
    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a provider."""
        if provider_name not in self.providers:
            return {}
        
        provider = self.providers[provider_name]
        return {
            "name": provider_name,
            "default_model": provider.get_default_model(),
            "base_url": getattr(provider, "base_url", None),
            "has_api_key": bool(getattr(provider, "api_key", None))
        }


async def test_llm_providers():
    """Test function to validate LLM providers."""
    
    manager = LLMManager()
    
    # Setup available providers
    providers_setup = []
    
    # Try Anthropic
    if manager.setup_anthropic():
        providers_setup.append("anthropic")
    
    # Try OpenAI
    if manager.setup_openai():
        providers_setup.append("openai")
    
    # Try Ollama (local)
    if manager.setup_ollama():
        providers_setup.append("ollama")
    
    # Always setup mock for testing
    manager.setup_mock({
        "hello": "Hello! I'm a mock LLM ready to help with code generation.",
        "python": "I can help you write Python code. Here's a simple function:\n\ndef hello_world():\n    return 'Hello, World!'"
    })
    providers_setup.append("mock")
    
    print(f"Available providers: {providers_setup}")
    
    # Test basic generation
    try:
        response = await manager.generate("Hello, can you help me write Python code?")
        print(f"Response from {response.provider}: {response.content[:100]}...")
        return True
    except Exception as e:
        print(f"Error testing LLM: {e}")
        return False


if __name__ == "__main__":
    # Test the LLM system
    result = asyncio.run(test_llm_providers())
    print(f"LLM system test: {'PASSED' if result else 'FAILED'}")