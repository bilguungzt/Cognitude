"""
Cognitude Autopilot Engine

This module contains the core logic for intelligently routing LLM requests to
optimize for cost, latency, and quality.
"""
import json
import hashlib
import logging
from typing import Dict, List, Tuple, Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from .. import schemas, models
from ..services.redis_cache import RedisCache
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
        'simple': ['gpt-3.5-turbo'],
        'medium': ['gpt-4-turbo'],
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
    def __init__(self, db: Session, redis_client: RedisCache):
        self.db = db
        self.redis_client = redis_client
        self.classifier = TaskClassifier()
        self.selector = ModelSelector()

    async def process_request(self, request: schemas.ChatCompletionRequest, organization: models.Organization, openai_api_key: str) -> dict:
        """
        Main autopilot processing method.
        
        CRITICAL: This method must NEVER raise exceptions that break the request.
        Always fall back to original model if anything fails.
        """
        try:
            return await self._process_with_autopilot(request, organization, openai_api_key)
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
            return await self._fallback_direct_call(request, openai_api_key)

    async def _process_with_autopilot(self, request: schemas.ChatCompletionRequest, organization: models.Organization, openai_api_key: str) -> dict:
        """Core autopilot logic."""
        # 1. Classify the task
        messages_dict = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        task_type, confidence = self.classifier.classify(messages_dict)

        # 2. Select the model
        selected_model, routing_reason = self.selector.select_model(
            task_type, confidence, request.model
        )

        # 3. Check cache
        cache_key = self.generate_cache_key(request, selected_model)
        cached_response = self.redis_client.get(cache_key, organization.id)

        if cached_response:
            # Log cache hit and return
            await self.log_autopilot_decision(
                organization_id=organization.id,
                llm_request_id=None, # Will be updated later
                original_model=request.model,
                selected_model=selected_model,
                task_type=task_type,
                routing_reason="cache_hit",
                cost_usd=Decimal(0),
                estimated_savings_usd=Decimal(cached_response['cost_usd']),
                confidence_score=confidence,
                is_cached_response=True,
                prompt_length=len(str(request.messages)),
                temperature=request.temperature or 1.0,
            )
            return {
                'response': cached_response['response_data'],
                'autopilot_metadata': {
                    'enabled': True,
                    'selected_model': selected_model,
                    'routing_reason': 'cache_hit'
                }
            }

        # 4. Call provider
        client = self._get_openai_client(openai_api_key)
        response = await client.chat.completions.create(
            model=selected_model,
            messages=messages_dict,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

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
            return await client.chat.completions.create(
                model=modified_request.model,
                messages=[{"role": m.role, "content": m.content} for m in modified_request.messages],
                temperature=modified_request.temperature,
                max_tokens=modified_request.max_tokens
            )

        validator = ResponseValidator(db=self.db, autopilot_log_id=autopilot_log.id)
        final_response = await validator.validate_and_fix(
            response=response,
            request=request,
            api_call_function=execute_llm_call
        )

        return {
            'response': final_response,
            'autopilot_metadata': {
                'enabled': True,
                'selected_model': selected_model,
                'routing_reason': routing_reason
            }
        }

    def generate_cache_key(self, request: schemas.ChatCompletionRequest, selected_model: str) -> str:
        """
        Generate cache key based on SELECTED model (not original).
        """
        prompt_text = json.dumps([msg.model_dump() for msg in request.messages], sort_keys=True)
        temperature = request.temperature if request.temperature is not None else 1.0
        
        cache_content = f"{selected_model}:{prompt_text}:{temperature}"
        
        return hashlib.md5(cache_content.encode()).hexdigest()

    async def log_autopilot_decision(self, **kwargs):
        """Log autopilot decision to database."""
        log_entry = models.AutopilotLog(**kwargs)
        self.db.add(log_entry)
        self.db.commit()
        self.db.refresh(log_entry)
        return log_entry

    async def _fallback_direct_call(self, request: schemas.ChatCompletionRequest, openai_api_key: str) -> dict:
        """Direct OpenAI call without autopilot (emergency fallback)."""
        client = self._get_openai_client(openai_api_key)
        
        response = await client.chat.completions.create(
            model=request.model,
            messages=[msg.model_dump() for msg in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return {
            'response': response,
            'autopilot_metadata': {
                'enabled': False,
                'fallback_reason': 'autopilot_error'
            }
        }

    def _get_openai_client(self, api_key: str) -> AsyncOpenAI:
        """Creates and returns an AsyncOpenAI client."""
        return AsyncOpenAI(api_key=api_key)