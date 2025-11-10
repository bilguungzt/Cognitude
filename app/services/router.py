"""
Multi-provider routing and API client management.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
import httpx
import time

from .. import crud, models


class ProviderRouter:
    """Routes LLM requests to appropriate provider based on model and configuration."""
    
    def __init__(self, db: Session, organization_id: int):
        self.db = db
        self.organization_id = organization_id
        self._providers = None
    
    def get_providers(self, enabled_only: bool = True) -> List[models.ProviderConfig]:
        """Get provider configurations, sorted by priority."""
        if self._providers is None:
            self._providers = crud.get_provider_configs(
                self.db, 
                self.organization_id, 
                enabled_only=enabled_only
            )
        return self._providers
    
    def select_provider(self, model: str) -> Optional[models.ProviderConfig]:
        """
        Select best provider for a model based on:
        1. Model name prefix (gpt-* -> openai, claude-* -> anthropic, etc.)
        2. Provider priority
        3. Provider enabled status
        
        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-opus")
            
        Returns:
            ProviderConfig or None if no suitable provider found
        """
        providers = self.get_providers(enabled_only=True)
        
        if not providers:
            return None
        
        # Determine provider from model name
        provider_name = None
        if model.startswith("gpt-"):
            provider_name = "openai"
        elif model.startswith("claude-"):
            provider_name = "anthropic"
        elif model.startswith("mistral-"):
            provider_name = "mistral"
        elif "llama" in model.lower() or "mixtral" in model.lower() or "gemma" in model.lower():
            provider_name = "groq"
        
        # Find matching provider
        if provider_name:
            matching_providers = [p for p in providers if p.provider == provider_name]
            if matching_providers:
                # Return highest priority
                return max(matching_providers, key=lambda p: p.priority)
        
        # Fallback: return highest priority provider
        return max(providers, key=lambda p: p.priority) if providers else None
    
    async def call_openai(
        self, 
        api_key: str, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call OpenAI API.
        
        Args:
            api_key: OpenAI API key
            model: Model name
            messages: List of message dicts
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Response dict from OpenAI API
        """
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs
            )
            
            # Convert to dict
            return {
                "id": completion.id,
                "model": completion.model,
                "created": completion.created,
                "usage": {
                    "prompt_tokens": completion.usage.prompt_tokens,
                    "completion_tokens": completion.usage.completion_tokens,
                    "total_tokens": completion.usage.total_tokens,
                },
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content,
                        },
                        "finish_reason": choice.finish_reason,
                    }
                    for choice in completion.choices
                ],
            }
        except ImportError:
            raise Exception("openai package not installed")
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def call_anthropic(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Anthropic Claude API.
        
        Args:
            api_key: Anthropic API key
            model: Model name
            messages: List of message dicts
            **kwargs: Additional parameters
            
        Returns:
            Response dict compatible with OpenAI format
        """
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Call Anthropic API
        async with httpx.AsyncClient() as client:
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            payload = {
                "model": model,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", 1024),
            }
            
            if system_message:
                payload["system"] = system_message
            if "temperature" in kwargs:
                payload["temperature"] = kwargs["temperature"]
            
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.text}")
            
            result = response.json()
            
            # Convert to OpenAI-compatible format
            return {
                "id": result["id"],
                "model": result["model"],
                "created": int(time.time()),
                "usage": {
                    "prompt_tokens": result["usage"]["input_tokens"],
                    "completion_tokens": result["usage"]["output_tokens"],
                    "total_tokens": result["usage"]["input_tokens"] + result["usage"]["output_tokens"],
                },
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": result["content"][0]["text"],
                        },
                        "finish_reason": result["stop_reason"],
                    }
                ],
            }
    
    async def call_provider(
        self,
        provider_config: models.ProviderConfig,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Route request to appropriate provider.
        
        Args:
            provider_config: Provider configuration
            model: Model name
            messages: List of message dicts
            **kwargs: Additional parameters
            
        Returns:
            Response dict in OpenAI-compatible format
        """
        provider_name = provider_config.provider
        api_key = provider_config.api_key_encrypted  # TODO: decrypt in production
        
        if provider_name == "openai":
            return await self.call_openai(api_key, model, messages, **kwargs)
        elif provider_name == "anthropic":
            return await self.call_anthropic(api_key, model, messages, **kwargs)
        else:
            raise Exception(f"Provider {provider_name} not yet implemented")
    
    async def call_with_fallback(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call provider with automatic fallback to alternatives on failure.
        
        Args:
            model: Model name
            messages: List of message dicts
            **kwargs: Additional parameters
            
        Returns:
            Response dict from successful provider
            
        Raises:
            Exception if all providers fail
        """
        # Get primary provider
        primary_provider = self.select_provider(model)
        
        if not primary_provider:
            raise Exception("No provider configured for this model")
        
        # Try primary provider
        try:
            return await self.call_provider(primary_provider, model, messages, **kwargs)
        except Exception as primary_error:
            # Try fallback providers
            all_providers = self.get_providers(enabled_only=True)
            fallback_providers = [
                p for p in all_providers 
                if p.id != primary_provider.id
            ]
            
            for fallback in fallback_providers:
                try:
                    return await self.call_provider(fallback, model, messages, **kwargs)
                except Exception:
                    continue
            
            # All providers failed
            raise Exception(f"All providers failed. Primary error: {str(primary_error)}")
