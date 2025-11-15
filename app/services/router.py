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
            model: Model identifier (e.g., "gpt-4-0125-preview", "claude-3-opus-20240229")
            
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
        # Mistral provider support removed (deprecated in this deployment)
        elif "llama" in model.lower() or "mixtral" in model.lower() or "gemma" in model.lower():
            provider_name = "groq"
        elif "gemini" in model.lower():
            provider_name = "google"
        
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
    
    async def call_google(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Google Gemini API.
        
        Args:
            api_key: Google AI API key
            model: Model name (e.g., "gemini-pro", "gemini-1.5-flash")
            messages: List of message dicts
            **kwargs: Additional parameters
            
        Returns:
            Response dict compatible with OpenAI format
        """
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=api_key)
            
            # Initialize the model
            gemini_model = genai.GenerativeModel(model)
            
            # Convert messages to Gemini format
            # For simplicity, combine all messages into a single prompt
            conversation_parts = []
            
            for msg in messages:
                if msg["role"] == "system":
                    conversation_parts.append(f"System: {msg['content']}")
                elif msg["role"] == "user":
                    conversation_parts.append(f"User: {msg['content']}")
                elif msg["role"] == "assistant":
                    conversation_parts.append(f"Assistant: {msg['content']}")
            
            # Combine conversation
            prompt = "\n".join(conversation_parts)
            
            # Generate response
            response = gemini_model.generate_content(
                prompt,
                generation_config={
                    "temperature": kwargs.get("temperature", 1.0),
                    "max_output_tokens": kwargs.get("max_tokens", 2048),
                }
            )
            
            # Convert to OpenAI-compatible format
            return {
                "id": f"gemini-{int(time.time())}",
                "model": model,
                "created": int(time.time()),
                "usage": {
                    "prompt_tokens": len(prompt.split()),  # Rough estimate
                    "completion_tokens": len(response.text.split()),  # Rough estimate
                    "total_tokens": len(prompt.split()) + len(response.text.split()),
                },
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response.text,
                        },
                        "finish_reason": "stop",
                    }
                ],
            }
        except ImportError:
            raise Exception("google-generativeai package not installed")
        except Exception as e:
            raise Exception(f"Google Gemini API error: {str(e)}")
    
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
        api_key = provider_config.api_key  # This property decrypts api_key_encrypted
        
        if provider_name == "openai":
            return await self.call_openai(api_key, model, messages, **kwargs)
        elif provider_name == "anthropic":
            return await self.call_anthropic(api_key, model, messages, **kwargs)
        elif provider_name == "google":
            return await self.call_google(api_key, model, messages, **kwargs)
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
    
    async def test_provider_connection(
        self,
        provider_name: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Test connection to a provider without requiring a saved config.
        
        Args:
            provider_name: Provider name (openai, anthropic, google)
            api_key: API key to test
            model: Model name
            messages: Test messages
            **kwargs: Additional parameters
            
        Returns:
            Response dict from the provider
        """
        if provider_name == "openai":
            return await self.call_openai(api_key, model, messages, **kwargs)
        elif provider_name == "anthropic":
            return await self.call_anthropic(api_key, model, messages, **kwargs)
        elif provider_name == "google":
            return await self.call_google(api_key, model, messages, **kwargs)
        else:
            raise Exception(f"Provider {provider_name} not supported for testing")
