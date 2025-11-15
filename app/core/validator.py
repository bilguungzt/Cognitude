"""
Cognitude Response Validator

This module contains the ResponseValidator class, responsible for inspecting LLM
responses for common issues and attempting to fix them automatically.
"""
import json
import logging
from typing import Dict, Any, Optional, Tuple, Callable, Awaitable

from sqlalchemy.orm import Session
from openai import AsyncOpenAI

from .. import schemas, models

logger = logging.getLogger(__name__)

class ResponseValidator:
    """
    Inspects LLM responses for common issues and attempts to fix them.
    """
    def __init__(self, db: Session, autopilot_log_id: int):
        self.db = db
        self.autopilot_log_id = autopilot_log_id
        self.MAX_RETRIES = 2

    async def validate_and_fix(
        self,
        response: Any,
        request: schemas.ChatCompletionRequest,
        api_call_function: Callable[[schemas.ChatCompletionRequest], Awaitable[Any]]
    ) -> Any:
        """
        Main validation method. It checks for issues and orchestrates fixes.
        """
        original_response = response
        current_response = response
        # Determine if the original request expects JSON
        original_expects_json = "json" in request.messages[-1].content.lower()
        
        for i in range(self.MAX_RETRIES):
            validation_type = None
            fix_type = None
            
            # 1. Check for empty response
            if self._is_response_empty(current_response):
                validation_type = 'empty_response'
                fix_type = 'retry_with_same_prompt'
            # 2. Check for JSON issues
            elif self._is_json_invalid(current_response, original_expects_json):
                validation_type = 'invalid_json'
                fix_type = 'retry_with_stricter_prompt'
            # 3. Check for truncation
            elif self._is_truncated(current_response):
                validation_type = 'truncated_response'
                fix_type = 'retry_with_increased_max_tokens'

            # If all checks pass, return the valid response
            if validation_type is None:
                return current_response

            # Log the initial failure for this attempt
            self._log_validation_attempt(validation_type, 'N/A', i, False)

            if fix_type:
                # Attempt to fix the issue
                new_response, success = await self._attempt_fix(validation_type, fix_type, request, i, api_call_function, original_expects_json)
                
                if success:
                    # If the fix was successful, we can return the new response immediately
                    # as _attempt_fix already re-validates it.
                    return new_response
                else:
                    # If the fix failed, we continue to the next retry iteration
                    current_response = new_response or original_response
            else:
                # Should not happen if validation_type is not None, but as a safeguard:
                return current_response

        logger.warning(f"Failed to fix response for autopilot_log_id={self.autopilot_log_id} after {self.MAX_RETRIES} retries.")
        return original_response

    def _is_response_empty(self, response: Any) -> bool:
        """Checks if the response content is empty or whitespace."""
        # Handle both object and dictionary formats
        try:
            # Try object format first (OpenAI style)
            if not response.choices or not response.choices[0].message or response.choices[0].message.content is None:
                return True
            content = response.choices[0].message.content
        except AttributeError:
            # Handle dictionary format (Google style)
            if not response.get('choices') or not response['choices'][0].get('message') or response['choices'][0]['message'].get('content') is None:
                return True
            content = response['choices'][0]['message']['content']
        
        return not content.strip()

    def _is_json_invalid(self, response: Any, expects_json: bool) -> bool:
        """Checks for invalid JSON if the prompt expected it."""
        if not expects_json:
            return False
        try:
            # Handle both object and dictionary formats
            try:
                # Try object format first (OpenAI style)
                if not response.choices or not response.choices[0].message or response.choices[0].message.content is None:
                    return True # Consider no content as invalid JSON if JSON was expected
                content = response.choices[0].message.content
            except AttributeError:
                # Handle dictionary format (Google style)
                if not response.get('choices') or not response['choices'][0].get('message') or response['choices'][0]['message'].get('content') is None:
                    return True # Consider no content as invalid JSON if JSON was expected
                content = response['choices'][0]['message']['content']
            
            json.loads(content)
            return False
        except (json.JSONDecodeError, AttributeError, TypeError):
            return True

    def _is_truncated(self, response: Any) -> bool:
        """Checks if the response was likely truncated."""
        # Handle both object and dictionary formats
        try:
            # Try object format first (OpenAI style)
            return response.choices and response.choices[0].finish_reason == 'length'
        except AttributeError:
            # Handle dictionary format (Google style)
            return response.get('choices') and response['choices'][0].get('finish_reason') == 'length'

    async def _attempt_fix(
        self,
        validation_type: str,
        fix_type: str,
        request: schemas.ChatCompletionRequest,
        retry_count: int,
        api_call_function: Callable[[schemas.ChatCompletionRequest], Awaitable[Any]],
        original_expects_json: bool
    ) -> Tuple[Optional[Any], bool]:
        """
        Attempts a specific fix, logs the outcome, and retries the API call.
        """
        modified_request = request.copy(deep=True)
        
        if fix_type == 'retry_with_stricter_prompt':
            # Enhance the prompt for stricter JSON output
            modified_request.messages.append(
                schemas.ChatMessage(role="user", content="Ensure your response is a single, valid, minified JSON object with no extra text or explanations.")
            )
        elif fix_type == 'retry_with_increased_max_tokens':
            # Increase max_tokens, being careful not to exceed model limits
            current_max = modified_request.max_tokens or 1024 # Default if not set
            modified_request.max_tokens = int(current_max * 1.5)
        elif fix_type == 'retry_with_same_prompt':
            # No changes needed for a simple retry
            pass

        try:
            logger.info(f"Attempting fix: {fix_type} for {validation_type} (Retry {retry_count + 1})")
            new_response = await api_call_function(modified_request)
            
            # Re-validate the new response to see if the fix worked
            # Use the original request's context for expects_json
            fix_successful = not (self._is_response_empty(new_response) or
                                  self._is_json_invalid(new_response, original_expects_json) or
                                  self._is_truncated(new_response))

            self._log_validation_attempt(validation_type, fix_type, retry_count + 1, fix_successful)
            return new_response, fix_successful
        except Exception as e:
            logger.error(f"Error during fix attempt '{fix_type}': {e}")
            self._log_validation_attempt(validation_type, fix_type, retry_count + 1, False)
            return None, False


    def _log_validation_attempt(self, validation_type: str, fix_attempted: str, retry_count: int, was_successful: bool):
        """Logs a validation/fix attempt to the database."""
        log_entry = models.ValidationLog(
            autopilot_log_id=self.autopilot_log_id,
            validation_type=validation_type,
            fix_attempted=fix_attempted,
            retry_count=retry_count,
            was_successful=was_successful
        )
        self.db.add(log_entry)
        self.db.commit()