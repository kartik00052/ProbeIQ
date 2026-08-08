"""Small helpers shared by LLM-backed agents (no model dependency at import time)."""

import json

from app.core.exceptions import InterviewEngineError


def extract_text(response: object) -> str:
    """Extract plain text from a chat-model response object or string."""
    if isinstance(response, str):
        return response
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if text:
                    parts.append(str(text))
            else:
                text = getattr(block, "text", None) or getattr(block, "content", None)
                if text:
                    parts.append(str(text))
        if parts:
            return "\n".join(parts)
    if isinstance(content, dict) and content.get("text"):
        return str(content["text"])
    return str(content or "")


def extract_json(text: str) -> dict | None:
    """Extract the first JSON object from a model response (strips fences)."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def invoke_json(chat_model: object, prompt: str) -> dict:
    """Call ``chat_model.invoke`` with a system prompt and return parsed JSON.

    Raises ``InterviewEngineError`` when the model is unavailable or its output
    is not valid JSON, so callers can never commit a fabricated structure and a
    failed call can be retried without corrupting session state.
    """
    messages = [("system", prompt)]
    try:
        response = chat_model.invoke(messages)  # type: ignore[attr-defined]
    except Exception as exc:
        raise InterviewEngineError("LLM call failed; no state was changed.") from exc
    payload = extract_json(extract_text(response))
    if payload is None:
        raise InterviewEngineError("LLM returned output that is not valid JSON.")
    return payload
