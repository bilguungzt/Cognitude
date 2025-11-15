"""
Cognitude Autopilot Engine

This module contains the core logic for intelligently routing LLM requests to
optimize for cost, latency, and quality.
"""
import logging
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from .. import schemas, models
from ..services.cache_service import CacheService
from ..services.router import ProviderRouter
from .validator import ResponseValidator

logger = logging.getLogger(__name__)

class TaskClassifier:
    """Simple keyword-based task classification for MVP."""
    
    TASK_KEYWORDS = {
        'classification': [
            'classify', 'categorize', 'label', 'is this', 'determine if',
            'spam or not', 'sentiment', 'positive or negative'
        ],
        'extraction': [
            'extract', 'find', 'identify', 'parse', 'get the',
            'what is the', 'pull out', 'retrieve'
        ],
        'translation': [
            'translate', 'in spanish', 'in french', 'into english',
            'language to', 'convert to'
        ],
        'summarization': [
            'summarize', 'summary', 'tldr', 'brief', 'main points',
            'key takeaways', 'in short'
        ],
        'generation': [
            'write', 'create', 'generate', 'compose', 'draft',
            'make a', 'build', 'develop'
        ],
        'reasoning': [
            'explain', 'why', 'how does', 'analyze', 'evaluate',
            'compare', 'what if', 'reasoning', 'think through'
        ],
        'code': [
            'python', 'javascript', 'code', 'script', 'function', 'class',
            'programming', 'debug', 'fix this bug', 'implement', 'algorithm'
        ]
    }

    def classify(self, messages: List[Dict[str, str]]) -> Tuple[str, float]:
        """
        Classify task type from messages.
        
        Returns:
            (task_type, confidence_score)
        """
        prompt = ""
        for msg in reversed(messages):
            if msg.get('role') == 'user':
                prompt = msg.get('content', '').lower()
                break
        
        if not prompt:
            return ('unknown', 0.0)
        
        scores = {task_type: sum(1 for kw in keywords if kw in prompt) 
                  for task_type, keywords in self.TASK_KEYWORDS.items()}
        
        if max(scores.values()) == 0:
            return ('generation', 0.3)
        
        best_task = max(scores, key=lambda k: scores[k])
        total_matches = sum(scores.values())
        confidence = scores[best_task] / total_matches if total_matches > 0 else 0.0
        
        return (best_task, min(confidence, 1.0))

class ModelSelector:
    """Selects optimal model based on task type and constraints."""
    
    MODEL_TIERS = {
        'simple': ['gpt-4o-mini'],
        'medium': ['gpt-4o'],
        'complex': ['gpt-4']
    }
    
    TASK_COMPLEXITY = {
        'classification': 'simple', 'extraction': 'simple', 'translation': 'simple',
        'summarization': 'medium', 'generation': 'medium', 'unknown': 'medium',
        'reasoning': 'complex', 'code': 'complex'
    }

    def select_model(self, task_type: str, confidence: float, original_model: str, optimize_for: str = 'cost') -> Tuple[str, str]:
        """
        Select optimal model.
        
        Returns:
            (selected_model, routing_reason)
        """
        complexity = self.TASK_COMPLEXITY.get(task_type, 'medium')
        reason = f"{optimize_for}_optimized_for_{task_type}_task"

        if confidence < 0.5:
            complexity = 'complex'
            reason = f"low_confidence_{confidence:.2f}_upgraded_to_safe_model"
        
        candidates = self.MODEL_TIERS.get(complexity, ['gpt-4'])
        selected = candidates[0]

        if original_model == 'gpt-4' and selected != 'gpt-4':
            if confidence < 0.8:
                selected = original_model
                reason = f"user_requested_{original_model}_keeping_original"
            else:
                reason = f"high_confidence_{confidence:.2f}_safe_to_downgrade"
        
        return (selected, reason)

class AutopilotEngine:
    """
    Orchestrates the entire request processing flow, including classification,
    model selection, caching, and logging.
    """
    def __init__(self, db: Session, cache_service: CacheService, provider_router: Optional[ProviderRouter] = None):
        self.db = db
        self.cache_service = cache_service
        self.provider_router = provider_router
        self.classifier = TaskClassifier()
        self.selector = ModelSelector()

    async def process_request(self, request: schemas.ChatCompletionRequest, organization: models.Organization, provider: models.ProviderConfig) -> dict:
        """
        Main autopilot processing method.
        
        CRITICAL: This method must NEVER raise exceptions that break the request.
        Always fall back to original model if anything fails.
        """
        try:
            return await self._process_with_autopilot(request, organization, provider)
        except Exception as e:
            logger.error(f"Autopilot failed unexpectedly: {str(e)}", exc_info=True)
            # Log failure to database
            await self.log_autopilot_decision(
                organization_id=organization.id,
                llm_request_id=None,
                original_model=request.model,
                selected_model=request.model,
                task_type="unknown",
                routing_reason=f"autopilot_error: {str(e)}",
                cost_usd=Decimal(0),
                estimated_savings_usd=None,
                confidence_score=0.0,
                is_cached_response=False,
                prompt_length=len(str(request.messages)),
                temperature=request.temperature or 1.0,
                error_message=str(e)
            )
            return await self._fallback_direct_call(request, provider)

    async def _process_with_autopilot(self, request: schemas.ChatCompletionRequest, organization: models.Organization, provider: models.ProviderConfig) -> dict:
        """Core autopilot logic."""
        # 1. Classify the task
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        task_type, confidence = self.classifier.classify(messages_dict)

        # 2. Select the model
        selected_model, routing_reason = self.selector.select_model(
            task_type, confidence, request.model
        )

        # 3. Check cache
        cache_hit = self.cache_service.get_response(
            db=self.db,
            organization_id=getattr(organization, 'id'),
            request=request,
            model_override=selected_model,
        )

        if cache_hit:
            # Log cache hit and return
            await self.log_autopilot_decision(
                organization_id=organization.id,
                llm_request_id=None, # Will be updated later
                original_model=request.model,
                selected_model=selected_model,
                task_type=task_type,
                routing_reason="cache_hit",
                cost_usd=Decimal(0),
                estimated_savings_usd=Decimal(cache_hit.payload.get('cost_usd', 0)),
                confidence_score=confidence,
                is_cached_response=True,
                prompt_length=len(str(request.messages)),
                temperature=request.temperature or 1.0,
            )
            return {
                'response': cache_hit.payload['response_data'],
                'autopilot_metadata': {
                    'enabled': True,
                    'selected_model': selected_model,
                    'routing_reason': 'cache_hit',
                    'provider_info': {
                        'name': cache_hit.payload.get('provider', 'unknown'),
                        'model': selected_model,
                        'cost': 0.0  # Cached responses have zero cost
                    },
                    'cache_key': cache_hit.cache_key,
                }
            }

        # 4. Call provider
        api_key = provider.get_api_key()
        provider_name = str(provider.provider)
        
        # Ensure model is compatible with provider
        # If using Google provider, make sure the model name is appropriate for Google
        final_model = selected_model
        if provider_name == "google":
            # For Google provider, ensure we're using a Google-compatible model
            if selected_model.startswith("gpt-") or selected_model.startswith("claude-"):
                # Fallback to Google's default model if an incompatible model was selected
                final_model = "gemini-flash"  # Use the alias that maps to the correct model
            else:
                final_model = selected_model
        
        # Create a temporary router for the call
        temp_router = ProviderRouter(self.db, getattr(organization, 'id'))
        
        if provider_name == "openai":
            response = await temp_router.call_openai(
                api_key=api_key,
                model=final_model,
                messages=messages_dict,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider_name == "google":
            response = await temp_router.call_google(
                api_key=api_key,
                model=final_model,
                messages=messages_dict,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider_name == "anthropic":
            response = await temp_router.call_anthropic(
                api_key=api_key,
                model=final_model,
                messages=messages_dict,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider_name == "groq":
            response = await temp_router.call_groq(
                api_key=api_key,
                model=final_model,
                messages=messages_dict,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        else:
            raise Exception(f"Unsupported provider: {provider_name}")

        # 5. Log decision to get an ID for the validator
        autopilot_log = await self.log_autopilot_decision(
            organization_id=organization.id,
            llm_request_id=None, # Will be updated later
            original_model=request.model,
            selected_model=selected_model,
            task_type=task_type,
            routing_reason=routing_reason,
            cost_usd=Decimal(0), # Will be updated later
            estimated_savings_usd=None, # Will be calculated later
            confidence_score=confidence,
            is_cached_response=False,
            prompt_length=len(str(request.messages)),
            temperature=request.temperature or 1.0,
        )
        # self.db.flush() is no longer needed as db.refresh() is used in log_autopilot_decision

        # 6. Validate and Fix Response
        async def execute_llm_call(modified_request: schemas.ChatCompletionRequest):
            # Ensure model is compatible with provider for validation calls
            final_model = modified_request.model
            if provider_name == "google":
                # For Google provider, ensure we're using a Google-compatible model
                if modified_request.model.startswith("gpt-") or modified_request.model.startswith("claude-"):
                    # Fallback to Google's default model if an incompatible model was selected
                    final_model = "gemini-flash"  # Use the alias that maps to the correct model
                else:
                    final_model = modified_request.model
            
            if provider_name == "openai":
                return await temp_router.call_openai(
                    api_key=api_key,
                    model=final_model,
                    messages=[{"role": m.role, "content": m.content} for m in modified_request.messages],
                    temperature=modified_request.temperature,
                    max_tokens=modified_request.max_tokens
                )
            elif provider_name == "google":
                return await temp_router.call_google(
                    api_key=api_key,
                    model=final_model,
                    messages=[{"role": m.role, "content": m.content} for m in modified_request.messages],
                    temperature=modified_request.temperature,
                    max_tokens=modified_request.max_tokens
                )
            elif provider_name == "anthropic":
                return await temp_router.call_anthropic(
                    api_key=api_key,
                    model=final_model,
                    messages=[{"role": m.role, "content": m.content} for m in modified_request.messages],
                    temperature=modified_request.temperature,
                    max_tokens=modified_request.max_tokens
                )
            elif provider_name == "groq":
                return await temp_router.call_groq(
                    api_key=api_key,
                    model=final_model,
                    messages=[{"role": m.role, "content": m.content} for m in modified_request.messages],
                    temperature=modified_request.temperature,
                    max_tokens=modified_request.max_tokens
                )
            else:
                raise Exception(f"Unsupported provider: {provider_name}")

        validator = ResponseValidator(db=self.db, autopilot_log_id=getattr(autopilot_log, 'id'))
        final_response = await validator.validate_and_fix(
            response=response,
            request=request,
            api_call_function=execute_llm_call
        )

        # Calculate cost from the response
        from ..services.pricing import calculate_cost
        usage = final_response.get('usage', {})
        cost = calculate_cost(
            model=selected_model,
            prompt_tokens=usage.get('prompt_tokens', 0),
            completion_tokens=usage.get('completion_tokens', 0)
        )
        
        return {
            'response': final_response,
            'autopilot_metadata': {
                'enabled': True,
                'selected_model': selected_model,
                'routing_reason': routing_reason,
                'provider_info': {
                    'name': provider_name,
                    'model': selected_model,
                    'cost': float(cost)
                }
            }
        }

    async def log_autopilot_decision(self, **kwargs):
        """Log autopilot decision to database."""
        log_entry = models.AutopilotLog(**kwargs)
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    async def _fallback_direct_call(self, request: schemas.ChatCompletionRequest, provider: models.ProviderConfig) -> dict:
        """Direct provider call without autopilot (emergency fallback)."""
        from ..services.pricing import calculate_cost
        
        api_key = provider.get_api_key()
        provider_name = str(provider.provider)
        
        # Ensure model is compatible with provider for fallback
        final_model = request.model
        if provider_name == "google":
            # For Google provider, ensure we're using a Google-compatible model
            if request.model.startswith("gpt-") or request.model.startswith("claude-"):
                # Fallback to Google's default model if an incompatible model was selected
                final_model = "gemini-flash"  # Use the alias that maps to the correct model
            else:
                final_model = request.model
        
        temp_router = ProviderRouter(self.db, getattr(provider, 'organization_id', 0))
        
        # If the primary provider is Google and it fails due to authentication,
        # try to find another available provider as fallback
        if provider_name == "google":
            try:
                response = await temp_router.call_google(
                    api_key=api_key,
                    model=final_model,
                    messages=[msg.model_dump() for msg in request.messages],
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )
                
                # Calculate cost
                usage = response.get('usage', {})
                cost = calculate_cost(
                    model=final_model,
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0)
                )
                
                return {
                    'response': response,
                    'autopilot_metadata': {
                        'enabled': False,
                        'fallback_reason': 'autopilot_error',
                        'provider_info': {
                            'name': provider_name,
                            'model': final_model,
                            'cost': float(cost)
                        }
                    }
                }
            except Exception as e:
                error_msg = str(e)
                # If it's an authentication error, try other providers
                if "authentication" in error_msg.lower() or "403" in error_msg or "API key" in error_msg:
                    logger.warning(f"Google authentication failed: {error_msg}. Trying other providers as fallback.")
                    
                    # Get other available providers for this organization
                    all_providers = temp_router.get_providers(enabled_only=True)
                    other_providers = [p for p in all_providers if str(p.provider) != "google"]
                    
                    for other_provider in other_providers:
                        try:
                            other_api_key = other_provider.get_api_key()
                            other_provider_name = str(other_provider.provider)
                            
                            if other_provider_name == "openai":
                                response = await temp_router.call_openai(
                                    api_key=other_api_key,
                                    model=final_model,
                                    messages=[msg.model_dump() for msg in request.messages],
                                    temperature=request.temperature,
                                    max_tokens=request.max_tokens
                                )
                            elif other_provider_name == "anthropic":
                                response = await temp_router.call_anthropic(
                                    api_key=other_api_key,
                                    model=final_model,
                                    messages=[msg.model_dump() for msg in request.messages],
                                    temperature=request.temperature,
                                    max_tokens=request.max_tokens
                                )
                            else:
                                continue  # Skip unsupported providers
                            
                            # Calculate cost
                            usage = response.get('usage', {})
                            cost = calculate_cost(
                                model=final_model,
                                prompt_tokens=usage.get('prompt_tokens', 0),
                                completion_tokens=usage.get('completion_tokens', 0)
                            )
                            
                            logger.info(f"Successfully used {other_provider_name} as fallback for Google failure")
                            return {
                                'response': response,
                                'autopilot_metadata': {
                                    'enabled': False,
                                    'fallback_reason': 'google_auth_failed_switched_to_other_provider',
                                    'provider_info': {
                                        'name': other_provider_name,
                                        'model': final_model,
                                        'cost': float(cost)
                                    }
                                }
                            }
                        except Exception as fallback_error:
                            logger.warning(f"Fallback to {other_provider_name} also failed: {fallback_error}")
                            continue
                    
                    # If all fallbacks fail, raise the original Google error
                    raise Exception(f"Google authentication failed and no fallback providers available: {error_msg}")
                else:
                    # For non-authentication errors, raise as is
                    raise e
        
        # For non-Google providers, use the original logic
        if provider_name == "openai":
            response = await temp_router.call_openai(
                api_key=api_key,
                model=final_model,
                messages=[msg.model_dump() for msg in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider_name == "anthropic":
            response = await temp_router.call_anthropic(
                api_key=api_key,
                model=final_model,
                messages=[msg.model_dump() for msg in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        elif provider_name == "groq":
            response = await temp_router.call_groq(
                api_key=api_key,
                model=final_model,
                messages=[msg.model_dump() for msg in request.messages],
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
        else:
            raise Exception(f"Unsupported provider: {provider_name}")
        
        # Calculate cost
        usage = response.get('usage', {})
        cost = calculate_cost(
            model=final_model,
            prompt_tokens=usage.get('prompt_tokens', 0),
            completion_tokens=usage.get('completion_tokens', 0)
        )
        
        return {
            'response': response,
            'autopilot_metadata': {
                'enabled': False,
                'fallback_reason': 'autopilot_error',
                'provider_info': {
                    'name': provider_name,
                    'model': final_model,
                    'cost': float(cost)
                }
            }
        }

    def _get_openai_client(self, api_key: str) -> AsyncOpenAI:
        """Creates and returns an AsyncOpenAI client."""
        return AsyncOpenAI(api_key=api_key)