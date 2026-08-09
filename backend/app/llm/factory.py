"""Provider abstraction that builds the configured LangChain chat model(s).

Responsibilities
    - load configuration from ``app.core.config.Settings``
    - validate provider / required settings (fail clearly, never leak the key)
    - construct the chat client(s) for the configured provider(s)
    - return ``None`` when the LLM is disabled so ProbeIQ runs fully offline

Models
    - ``PROBEIQ_LLM_MODELS`` (JSON list) configures a *roster*: the first entry
      is the primary model and the rest are automatic fallbacks. ``get_llm``
      returns a ``FallbackChatModel`` wrapper when more than one model is
      configured, so a failed call retries against the next model with no change
      to the agents that consume it.
    - When the roster is empty, the legacy single-model settings
      (``llm_model`` / ``llm_api_key`` / ...) are used and a bare chat client is
      returned, preserving the previous behavior exactly.

Per-entry providers:

    nvidia           -> ``ChatNVIDIA`` (langchain-nvidia-ai-endpoints) for
                        NVIDIA-hosted models (e.g. ``z-ai/glm-5.2``) at the
                        verified ``https://integrate.api.nvidia.com/v1`` base URL
                        (applied automatically when base_url is empty).
    openai           -> ``ChatOpenAI``, base URL optional.
    openai-compatible-> ``ChatOpenAI`` for any OpenAI-compatible endpoint;
                        base_url required.

Reasoning models (e.g. ``nvidia/nemotron-3-ultra-550b-a55b``,
``minimaxai/minimax-m3``, ``google/gemma-4-31b-it``) can set
``reasoning_budget`` and ``enable_thinking`` per entry.

``z-ai/glm-5.2`` is pre-registered with the NVIDIA client's static model table so
that ``ChatNVIDIA`` construction stays network-free (the package would otherwise
fetch ``/v1/models`` at build time). The ``openai`` / ``openai-compatible``
paths are always lazy -- no network at build time.

No API key is ever included in logs or exception messages.
"""

import warnings
from typing import Any

from langchain_nvidia_ai_endpoints import ChatNVIDIA, Model, register_model
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings, settings
from app.core.exceptions import LLMConfigurationError
from app.llm.fallback import FallbackChatModel

SUPPORTED_PROVIDERS = frozenset({"nvidia", "openai", "openai-compatible"})

#: Verified NVIDIA OpenAI-compatible Chat Completions endpoint (build.nvidia.com).
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

#: Model absent from the NVIDIA client's static table; registering it skips the
#: construction-time registry lookup that would otherwise hit the network.
DEFAULT_NVIDIA_MODEL = "z-ai/glm-5.2"

_GLM_REGISTERED = False


def get_llm(
    config: Settings | None = None,
) -> ChatOpenAI | ChatNVIDIA | FallbackChatModel | None:
    """Return the configured LangChain chat model, or ``None`` when disabled.

    Returns a bare chat client for a single configured model, or a
    ``FallbackChatModel`` wrapper when a roster is configured. Raises
    ``LLMConfigurationError`` when the LLM is enabled but a provider is
    unsupported or required settings are missing. Construction performs no
    network I/O for any provider.
    """
    conf = config or settings
    if not conf.llm_enabled:
        return None
    specs = _resolve_specs(conf)
    clients = [_build_client(spec) for spec in specs]
    if len(clients) == 1:
        return clients[0]
    return FallbackChatModel(clients=clients, model_names=[spec["model"] for spec in specs])


def _resolve_specs(conf: Settings) -> list[dict[str, Any]]:
    """Normalize configuration into an ordered list of model specs."""
    if conf.llm_models:
        specs = [_coerce_spec(spec) for spec in conf.llm_models]
        _validate_specs(specs)
        for spec in specs:
            # Per-entry override wins; otherwise apply the global transport
            # timeout so every client is bounded by PROBEIQ_LLM_TIMEOUT_SECONDS.
            spec["timeout_seconds"] = spec["timeout_seconds"] or conf.llm_timeout_seconds
        return specs
    _validate_legacy(conf)
    return [
        {
            "provider": conf.llm_provider,
            "model": conf.llm_model,
            "api_key": conf.llm_api_key.get_secret_value(),
            "base_url": conf.llm_base_url,
            "temperature": conf.llm_temperature,
            "top_p": conf.llm_top_p,
            "max_tokens": conf.llm_max_tokens,
            "seed": conf.llm_seed,
            "max_retries": conf.llm_max_retries,
            "reasoning_budget": None,
            "enable_thinking": None,
            "timeout_seconds": conf.llm_timeout_seconds,
        }
    ]


def _coerce_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Fill defaults for a roster entry so downstream code can rely on all keys."""
    return {
        "provider": spec.get("provider", "nvidia"),
        "model": spec.get("model", ""),
        "api_key": spec.get("api_key", ""),
        "base_url": spec.get("base_url", ""),
        "temperature": spec.get("temperature", 0.0),
        "top_p": spec.get("top_p", 1.0),
        "max_tokens": spec.get("max_tokens", 16384),
        "seed": spec.get("seed", 42),
        "max_retries": spec.get("max_retries", 2),
        "reasoning_budget": spec.get("reasoning_budget"),
        "enable_thinking": spec.get("enable_thinking") or False,
        "timeout_seconds": spec.get("timeout_seconds"),
    }


def _validate_specs(specs: list[dict[str, Any]]) -> None:
    for spec in specs:
        provider = spec["provider"]
        if provider not in SUPPORTED_PROVIDERS:
            raise LLMConfigurationError(
                f"Unsupported LLM provider '{provider}' for model '{spec['model']}'. "
                f"Supported providers: {', '.join(sorted(SUPPORTED_PROVIDERS))}."
            )
        if not spec["api_key"]:
            raise LLMConfigurationError(
                f"LLM model '{spec['model']}' is missing an api_key in PROBEIQ_LLM_MODELS."
            )
        if not spec["model"]:
            raise LLMConfigurationError(
                "An LLM roster entry is missing its model in PROBEIQ_LLM_MODELS."
            )
        if provider == "openai-compatible" and not spec["base_url"]:
            raise LLMConfigurationError(
                f"LLM model '{spec['model']}' uses provider 'openai-compatible' and "
                "requires a base_url."
            )


def _validate_legacy(conf: Settings) -> None:
    if conf.llm_provider not in SUPPORTED_PROVIDERS:
        raise LLMConfigurationError(
            f"Unsupported LLM provider '{conf.llm_provider}'. "
            f"Supported providers: {', '.join(sorted(SUPPORTED_PROVIDERS))}."
        )
    if not conf.llm_api_key.get_secret_value():
        raise LLMConfigurationError(
            "LLM is enabled but PROBEIQ_LLM_API_KEY is not set."
        )
    if not conf.llm_model:
        raise LLMConfigurationError(
            "LLM is enabled but PROBEIQ_LLM_MODEL is not set."
        )
    if conf.llm_provider == "openai-compatible" and not conf.llm_base_url:
        raise LLMConfigurationError(
            "LLM provider 'openai-compatible' requires PROBEIQ_LLM_BASE_URL to be set."
        )


def _register_default_model() -> None:
    """Register ``z-ai/glm-5.2`` so ChatNVIDIA skips the registry lookup."""
    global _GLM_REGISTERED
    if _GLM_REGISTERED:
        return
    with warnings.catch_warnings():
        # Re-registering is harmless (idempotent table write).
        warnings.simplefilter("ignore")
        register_model(
            Model(
                id=DEFAULT_NVIDIA_MODEL,
                model_type="chat",
                client="ChatNVIDIA",
                endpoint="{base_url}/chat/completions",
            )
        )
    _GLM_REGISTERED = True


def _build_client(spec: dict[str, Any]) -> ChatOpenAI | ChatNVIDIA:
    if spec["provider"] == "nvidia":
        return _build_chat_nvidia(spec)
    return ChatOpenAI(
        model=spec["model"],
        api_key=SecretStr(spec["api_key"]),
        base_url=_spec_base_url(spec),
        temperature=spec["temperature"],
        max_tokens=spec["max_tokens"],  # type: ignore[call-arg]
        top_p=spec["top_p"],
        seed=spec["seed"],
        max_retries=spec["max_retries"],
        request_timeout=spec["timeout_seconds"],
    )


def _build_chat_nvidia(spec: dict[str, Any]) -> ChatNVIDIA:
    if spec["model"] == DEFAULT_NVIDIA_MODEL:
        _register_default_model()
    try:
        kwargs: dict[str, Any] = {
            "model": spec["model"],
            "api_key": spec["api_key"],
            "base_url": _spec_base_url(spec),
            "temperature": spec["temperature"],
            "max_completion_tokens": spec["max_tokens"],
            "top_p": spec["top_p"],
            "seed": spec["seed"],
            "timeout": spec["timeout_seconds"],
        }
        if spec.get("reasoning_budget"):
            kwargs["reasoning_budget"] = spec["reasoning_budget"]
        if spec.get("enable_thinking"):
            kwargs["chat_template_kwargs"] = {"enable_thinking": True}
        with warnings.catch_warnings():
            # Non-default params (reasoning_budget, chat_template_kwargs) are
            # routed to model_kwargs by the client; the notice is expected.
            warnings.simplefilter("ignore")
            return ChatNVIDIA(**kwargs)
    except Exception as exc:  # client init failure
        raise LLMConfigurationError(
            f"Failed to initialize NVIDIA chat model '{spec['model']}': "
            f"{type(exc).__name__}"
        ) from exc


def _spec_base_url(spec: dict[str, Any]) -> str | None:
    if spec["base_url"]:
        return spec["base_url"]
    if spec["provider"] == "nvidia":
        return NVIDIA_BASE_URL
    return None


def generation_caps(conf: Settings, *, max_tokens: int) -> dict[str, Any] | None:
    """Provider-correct per-call kwargs that bound output length and latency.

    The ProbeIQ agents share one chat client but ask short questions and produce
    short evaluations/feedback, so every invocation should cap its own completion
    budget instead of inheriting a large constructor default. This helper maps
    that cap to the field name the configured provider's API expects:

    - ``nvidia``            -> ``max_completion_tokens``, plus a ``reasoning_budget``
      clamped to ``max_tokens`` when a roster entry configured one (bounds thinking
      on NVIDIA reasoning models).
    - ``openai``/``openai-compatible`` -> ``max_tokens``.

    Returns ``None`` when the roster mixes providers (a single call-kwargs dict
    cannot name both fields safely); those setups keep their constructor defaults.
    """
    specs = _resolve_specs(conf)
    providers = {spec["provider"] for spec in specs}
    if len(providers) != 1:
        return None
    provider = providers.pop()
    if provider == "nvidia":
        kwargs: dict[str, Any] = {"max_completion_tokens": max_tokens}
        budgets = [spec["reasoning_budget"] for spec in specs if spec.get("reasoning_budget")]
        if budgets:
            kwargs["reasoning_budget"] = min(max_tokens, *budgets)
        return kwargs
    return {"max_tokens": max_tokens}
