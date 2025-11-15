"""
Multi-provider routing and API client management.
"""
import asyncio
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
        self._providers: Optional[List[models.ProviderConfig]] = None
    
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
        """
        providers = self.get_providers(enabled_only=True)
        
        if not providers:
            return None
        
        provider_name = None
        if model.startswith("gpt-") or model.startswith("o1-") or model.startswith("o4-"):
            provider_name = "openai"
        elif model.startswith("claude-"):
            provider_name = "anthropic"
        elif model.startswith("gemini-") or "gemini" in model.lower():
            provider_name = "google"
        elif "llama" in model.lower() or "mixtral" in model.lower() or "gemma" in model.lower() or "groq" in model.lower() or model.startswith("fast-"):
            provider_name = "groq"
        
        if provider_name:
            matching_providers = [p for p in providers if str(p.provider) == provider_name]
            if matching_providers:
                return max(matching_providers, key=lambda p: p.priority)
        
        return max(providers, key=lambda p: p.priority) if providers else None
    
    async def call_openai(
        self, 
        api_key: str, 
        model: str, 
        messages: List[Dict[str, str]], 
        **kwargs
    ) -> Dict[str, Any]:
        """Call OpenAI API."""
        request_timeout = kwargs.pop("request_timeout", 60.0)

        def _execute_call():
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise Exception("openai package not installed") from exc

            client = OpenAI(api_key=api_key, timeout=request_timeout)
            completion = client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                **kwargs,
            )
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

        try:
            return await asyncio.to_thread(_execute_call)
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def call_anthropic(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Call Anthropic Claude API."""
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})
        
        timeout = kwargs.get("request_timeout", 60.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
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
            )
            
            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.text}")
            
            result = response.json()
            
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
                        "message": {"role": "assistant", "content": result["content"][0]["text"]},
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
        """Call Google Gemini API."""
        request_timeout = kwargs.get("request_timeout", 60.0)

        def _execute_call():
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold

            genai.configure(api_key=api_key)

            model_map = {
                'gemini-pro': 'gemini-2.0-flash-exp',
                'gemini-flash': 'gemini-2.5-flash-lite',
                'gemini-2.5-flash-lite': 'gemini-2.5-flash-lite',
                'gemini-2.5-flash': 'gemini-2.5-flash',
                'gemini-2.5-pro': 'gemini-2.5-pro',
            }
            gemini_model_name = model_map.get(model, model)

            gen_model = genai.GenerativeModel(
                model_name=gemini_model_name,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )

            generation_config = {
                "temperature": kwargs.get("temperature", 0.9),
                "top_p": kwargs.get("top_p", 1),
                "top_k": kwargs.get("top_k", 1),
                "max_output_tokens": kwargs.get("max_tokens", 2048),
            }

            contents = []
            for msg in messages:
                if msg["role"] == "system":
                    continue
                contents.append({"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]})

            response = gen_model.generate_content(
                contents,
                generation_config=generation_config,  # type: ignore
                stream=False,
            )

            response_text = ""
            if response.candidates and response.candidates[0].content.parts:
                response_text = "".join(part.text for part in response.candidates[0].content.parts)
            elif getattr(response.prompt_feedback, "block_reason", None):
                response_text = f"Request blocked due to {response.prompt_feedback.block_reason.name}"
            else:
                response_text = "No response from model."

            try:
                prompt_tokens = gen_model.count_tokens(contents).total_tokens
            except Exception:
                prompt_tokens = len(str(contents))

            try:
                completion_tokens = gen_model.count_tokens(response_text).total_tokens
            except Exception:
                completion_tokens = len(response_text)

            return {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": gemini_model_name,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": response_text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            }

        try:
            return await asyncio.to_thread(_execute_call)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "API key" in error_msg or "authentication" in error_msg.lower():
                raise Exception(f"Google Gemini authentication error: {error_msg}. Please verify your API key is correct and has not been revoked.")
            else:
                raise Exception(f"Google Gemini API error: {error_msg}")
    
    async def call_groq(
        self,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Call Groq API (OpenAI-compatible)."""
        request_timeout = kwargs.pop("request_timeout", 60.0)

        def _execute_call():
            from openai import OpenAI

            client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1",
                timeout=request_timeout,
            )

            completion = client.chat.completions.create(
                model=model,
                messages=messages,  # type: ignore
                **kwargs,
            )

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

        try:
            return await asyncio.to_thread(_execute_call)
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")

    async def call_provider(
        self,
        provider_config: models.ProviderConfig,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Route request to appropriate provider."""
        provider_name = str(provider_config.provider)
        api_key = provider_config.get_api_key()
        
        if provider_name == "openai":
            return await self.call_openai(api_key, model, messages, **kwargs)
        elif provider_name == "anthropic":
            return await self.call_anthropic(api_key, model, messages, **kwargs)
        elif provider_name == "google":
            return await self.call_google(api_key, model, messages, **kwargs)
        elif provider_name == "groq":
            return await self.call_groq(api_key, model, messages, **kwargs)
        else:
            raise Exception(f"Provider {provider_name} not yet implemented")
    
    async def call_with_fallback(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Call provider with automatic fallback to alternatives on failure."""
        primary_provider = self.select_provider(model)
        
        if not primary_provider:
            raise Exception("No provider configured for this model")
        
        try:
            return await self.call_provider(primary_provider, model, messages, **kwargs)
        except Exception as primary_error:
            all_providers = self.get_providers(enabled_only=True)
            fallback_providers = [p for p in all_providers if p.id != primary_provider.id]
            
            for fallback in fallback_providers:
                try:
                    return await self.call_provider(fallback, model, messages, **kwargs)
                except Exception:
                    continue
            
            raise Exception(f"All providers failed. Primary error: {str(primary_error)}")
    
    async def test_provider_connection(
        self,
        provider_name: str,
        api_key: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Test connection to a provider without requiring a saved config."""
        if provider_name == "openai":
            return await self.call_openai(api_key, model, messages, **kwargs)
        elif provider_name == "anthropic":
            return await self.call_anthropic(api_key, model, messages, **kwargs)
        elif provider_name == "google":
            return await self.call_google(api_key, model, messages, **kwargs)
        else:
            raise Exception(f"Provider {provider_name} not supported for testing")
