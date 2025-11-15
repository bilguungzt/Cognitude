import hashlib
import json
from typing import Any, Dict, List, Optional

from app import schemas


class CacheKeyBuilder:
    """
    Utility responsible for producing deterministic cache keys.

    Keys follow the format: "{organization_id}:{sha256_digest}"
    where the digest is calculated over a normalized representation
    of the request payload.
    """

    @staticmethod
    def _normalize_messages(messages: List[schemas.ChatMessage]) -> List[Dict[str, str]]:
        normalized: List[Dict[str, str]] = []
        for message in messages:
            normalized.append(
                {
                    "role": message.role,
                    "content": message.content,
                }
            )
        return normalized

    @classmethod
    def chat_completion_key(
        cls,
        organization_id: int,
        request: schemas.ChatCompletionRequest,
        *,
        model_override: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build a deterministic key for chat completion requests.

        Args:
            organization_id: Owning organization
            request: Incoming chat completion payload
            model_override: Optional model selected by Autopilot
            extra_metadata: Additional inputs that affect cacheability (e.g. schema id)
        """
        payload: Dict[str, Any] = {
            "model": model_override or request.model,
            "messages": cls._normalize_messages(request.messages),
            "temperature": request.temperature if request.temperature is not None else 1.0,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": bool(request.stream),
        }

        if extra_metadata:
            payload["meta"] = extra_metadata

        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"{organization_id}:{digest}"

    @staticmethod
    def prompt_hash(request: schemas.ChatCompletionRequest) -> str:
        """
        Lightweight hash of the prompt payload for relational storage.
        """
        payload = json.dumps(
            {
                "messages": [
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
                "model": request.model,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.md5(payload.encode("utf-8")).hexdigest()

