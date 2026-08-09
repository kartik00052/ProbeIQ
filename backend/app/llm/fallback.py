"""Multi-model fallback chat client.

Wraps several LangChain chat models (``ChatNVIDIA`` / ``ChatOpenAI``) into one
object with the same ``invoke(messages)`` surface the ProbeIQ agents use, so a
configured roster behaves like a single chat model -- except that a failed call
automatically retries against the next model in the roster.

No API key is ever included in logs or exception messages; a total-failure
error reports the failing model name and exception type only.
"""

from collections.abc import Iterable, Sequence
from typing import Any


class FallbackChatModel:
    """Tries each configured model in order; returns the first successful response."""

    def __init__(self, clients: Sequence[Any], model_names: Sequence[str]) -> None:
        if not clients or len(clients) != len(model_names):
            raise ValueError("clients and model_names must be non-empty and parallel")
        self._clients = list(clients)
        self._model_names = list(model_names)
        #: Most recently used model (set after the first successful invoke).
        self.last_used_model: str | None = None

    @property
    def model(self) -> str:
        """Name of the primary model (or the last one that responded)."""
        return self.last_used_model or self._model_names[0]

    @property
    def available_models(self) -> list[str]:
        return list(self._model_names)

    def invoke(self, messages: Iterable, **kwargs: Any) -> Any:
        """Forward ``messages`` to each model until one responds.

        Raises ``RuntimeError`` (sanitized -- no key, no underlying message)
        when every model in the roster fails.
        """
        last_exc: Exception | None = None
        for client, name in zip(self._clients, self._model_names, strict=True):
            try:
                response = client.invoke(messages, **kwargs)
            except Exception as exc:  # noqa: BLE001 -- deliberate per-model fallback
                last_exc = exc
                continue
            self.last_used_model = name
            return response
        if last_exc is not None:
            raise RuntimeError(
                f"all {len(self._clients)} LLM models failed; "
                f"last model '{self._model_names[-1]}' raised {type(last_exc).__name__}"
            ) from last_exc
        raise RuntimeError("no LLM models configured")
