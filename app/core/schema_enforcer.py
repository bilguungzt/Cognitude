import json
import json
from typing import Tuple, Optional
from jsonschema import validate, ValidationError, Draft7Validator
from sqlalchemy.orm import Session
from app import crud, models

def validate_user_schema(schema: dict):
    """
    Validates a user-provided JSON schema for security and correctness.
    """
    # Size Limit (10KB)
    schema_str = json.dumps(schema)
    if len(schema_str.encode('utf-8')) > 10 * 1024:
        raise ValueError("Schema size exceeds the 10KB limit.")

    # Dangerous Patterns
    dangerous_keywords = ["eval", "exec", "__import__", "subprocess"]
    if any(keyword in schema_str for keyword in dangerous_keywords):
        raise ValueError("Schema contains potentially dangerous keywords.")

    # Valid JSON Schema
    try:
        Draft7Validator.check_schema(schema)
    except Exception as e:
        raise ValueError(f"Invalid JSON Schema: {e}")

# Prompt Templates
SCHEMA_ENFORCEMENT_PROMPT = """
Please ensure your response STRICTLY follows this JSON schema:
{schema}
"""

RETRY_PROMPT = """
Your previous response failed validation with the following error:
{error}

Please correct your response and ensure it STRICTLY follows this JSON schema:
{schema}
"""

class SchemaEnforcer:
    def __init__(self, db: Session, llm_provider, max_retries: int = 3):
        self.db = db
        self.llm_provider = llm_provider
        self.max_retries = max_retries

    def enforce_schema(self, request: dict, schema: dict) -> dict:
        """
        Injects schema enforcement instructions into the request's system prompt.
        """
        system_prompt = request.get("messages", [{}])[0].get("content", "")
        schema_prompt = self._generate_schema_prompt(schema)
        
        if "messages" in request and request["messages"]:
            if request["messages"][0].get("role") == "system":
                request["messages"][0]["content"] = f"{system_prompt}\n{schema_prompt}"
            else:
                request["messages"].insert(0, {"role": "system", "content": schema_prompt})
        else:
            request["messages"] = [{"role": "system", "content": schema_prompt}]
            
        return request

    def validate_and_retry(self, request: dict, schema: dict, response: dict, project_id: int) -> dict:
        """
        Validates the response against the schema.
        NOTE: This method is deprecated. Schema validation retries should be handled at the proxy level
        to avoid circular dependencies with the LLM provider.
        """
        is_valid, error_message = self._validate_json_schema(response, schema)
        
        if is_valid:
            self._log_validation(project_id, request, response, True, "", 0)
            return response
        else:
            self._log_validation(project_id, request, response, False, error_message, 0)
            # Just return the original response since retries are handled at the proxy level
            return response

    def _generate_schema_prompt(self, schema: dict) -> str:
        """
        Generates the initial prompt for schema enforcement.
        """
        return SCHEMA_ENFORCEMENT_PROMPT.format(schema=json.dumps(schema, indent=2))

    def _generate_retry_prompt(self, schema: dict, error: str) -> str:
        """
        Generates a stricter prompt for retrying a failed validation.
        """
        return RETRY_PROMPT.format(schema=json.dumps(schema, indent=2), error=error)

    def _validate_json_schema(self, response: dict, schema: dict) -> Tuple[bool, str]:
        """
        Validates a JSON response against a given schema.
        """
        try:
            # Assuming the response content is in a specific part of the response object
            response_content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            response_json = json.loads(response_content)
            validate(instance=response_json, schema=schema)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"JSON Decode Error: {e}"
        except ValidationError as e:
            return False, f"Schema Validation Error: {e.message}"
        except Exception as e:
            return False, f"An unexpected error occurred: {e}"

    def _log_validation(self, project_id: int, request: dict, response: dict, is_valid: bool, error: Optional[str], attempt: int):
        """
        Logs the result of a schema validation attempt to the database.
        """
        log_entry = models.SchemaValidationLog(
            organization_id=project_id,
            provided_schema=json.dumps(request.get("messages", [])),
            llm_response=json.dumps(response),
            is_valid=is_valid,
            validation_error=error,
            retry_count=attempt,
            was_successful=is_valid
        )
        self.db.add(log_entry)
        self.db.commit()