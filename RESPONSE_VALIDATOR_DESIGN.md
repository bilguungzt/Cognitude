# Response Validator Design Document

This document outlines the design and integration plan for the new `ResponseValidator` feature in the Autopilot Engine.

## 1. `ResponseValidator` Class Design

The `ResponseValidator` class will be responsible for validating and attempting to fix common issues with LLM responses.

**File Location:** `app/core/validator.py`

### Class Structure

```python
import json
import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from openai.types.chat import ChatCompletion
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
        response: ChatCompletion,
        request: schemas.ChatCompletionRequest,
        api_call_function: callable
    ) -> ChatCompletion:
        """
        Main validation method. It checks for issues and orchestrates fixes.

        Args:
            response: The initial response from the LLM.
            request: The original ChatCompletionRequest.
            api_call_function: A callable function to re-execute the LLM call.

        Returns:
            A validated (and potentially fixed) ChatCompletion object.
        """
        # Implementation will iterate through validation checks
        # and call attempt_fix if an issue is found.
        pass

    def _is_response_empty(self, response: ChatCompletion) -> bool:
        """Checks if the response content is empty or whitespace."""
        pass

    def _is_json_invalid(self, response: ChatCompletion, expects_json: bool) -> bool:
        """Checks for invalid JSON if the prompt expected it."""
        pass

    def _is_truncated(self, response: ChatCompletion) -> bool:
        """Checks if the response was likely truncated."""
        pass

    async def _attempt_fix(
        self,
        validation_type: str,
        fix_type: str,
        request: schemas.ChatCompletionRequest,
        api_call_function: callable,
        retry_count: int
    ) -> Tuple[Optional[ChatCompletion], bool]:
        """
        Attempts a specific fix and logs the outcome.

        Args:
            validation_type: The type of validation that failed (e.g., 'invalid_json').
            fix_type: The fix being attempted (e.g., 'retry_with_stricter_prompt').
            request: The original request, which may be modified for the retry.
            api_call_function: The function to call the LLM.
            retry_count: The current retry attempt number.

        Returns:
            A tuple of (new_response, was_successful).
        """
        # 1. Log the fix attempt to the new validation_logs table.
        # 2. Modify the request (e.g., add a system message, increase max_tokens).
        # 3. Call the api_call_function with the modified request.
        # 4. Log the result (success/failure) of the fix.
        # 5. Return the new response and success status.
        pass

    def _log_validation_attempt(self, validation_type: str, fix_attempted: str, retry_count: int, was_successful: bool):
        """Logs a validation/fix attempt to the database."""
        # This will create and commit a new ValidationLog entry.
        pass
```

## 2. Integration with `AutopilotEngine`

The `ResponseValidator` will be integrated into the `_process_with_autopilot` method in `app/core/autopilot.py`.

### Changes in `app/core/autopilot.py`

1.  **Import:** Add `from .validator import ResponseValidator` at the top of the file.
2.  **Instantiate Validator:** In `_process_with_autopilot`, after the initial `log_autopilot_decision` call, a `ResponseValidator` instance will be created. This requires the `autopilot_log` entry to be created and flushed to the DB first to get its ID.
3.  **Wrap API Call:** The `client.chat.completions.create` call will be wrapped in a helper function so it can be passed to the validator for retries.
4.  **Call Validator:** The `validate_and_fix` method will be called immediately after the initial response is received.

### Pseudocode for `_process_with_autopilot`

```python
# In AutopilotEngine._process_with_autopilot...

# ... (after model selection and cache check)

# 4. Log initial decision to get an ID
autopilot_log = await self.log_autopilot_decision(...)
# self.db.flush() # Ensure autopilot_log.id is available

# 5. Call provider
client = self._get_openai_client(openai_api_key)

async def execute_llm_call(modified_request):
    return await client.chat.completions.create(
        model=modified_request.model,
        messages=[{"role": m.role, "content": m.content} for m in modified_request.messages],
        # ... other params
    )

initial_response = await execute_llm_call(request)

# 6. Validate and Fix Response
validator = ResponseValidator(db=self.db, autopilot_log_id=autopilot_log.id)
final_response = await validator.validate_and_fix(
    response=initial_response,
    request=request,
    api_call_function=execute_llm_call
)

# 7. Return final response
return {
    'response': final_response,
    'autopilot_metadata': { ... }
}
```

## 3. Database Schema for `validation_logs`

A new table, `validation_logs`, will be added to `app/models.py` to track validation failures and fix attempts.

### SQLAlchemy Model in `app/models.py`

```python
# Add this new class to app/models.py

class ValidationLog(Base):
    """Logs response validation failures and fix attempts."""
    __tablename__ = "validation_logs"

    id = Column(BigInteger, primary_key=True, index=True)
    autopilot_log_id = Column(BigInteger, ForeignKey("autopilot_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    validation_type = Column(String(100), nullable=False, index=True) # e.g., 'invalid_json', 'empty_response'
    fix_attempted = Column(String(255), nullable=False) # e.g., 'retry_with_stricter_prompt'
    retry_count = Column(Integer, nullable=False)
    was_successful = Column(Boolean, nullable=False)

    # Relationship to AutopilotLog
    autopilot_log = relationship("AutopilotLog", back_populates="validation_logs")

    def __repr__(self):
        return f"<ValidationLog(id={self.id}, type='{self.validation_type}', success={self.was_successful})>"

# Also, add the back-populating relationship to the AutopilotLog model:
# In class AutopilotLog(Base):
#   validation_logs = relationship("ValidationLog", back_populates="autopilot_log", cascade="all, delete-orphan")