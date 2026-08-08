"""Provider abstraction that builds the configured LangChain chat model.

Responsibilities
    - load configuration from ``app.core.config.Settings``
    - validate provider / required settings (fail clearly, never leak the key)
    - construct the chat client for the configured provider
    - return ``None`` when the LLM is disabled so ProbeIQ runs fully offline

Providers:

    nvidia           -> ``ChatNVIDIA`` (langchain-nvidia-ai-endpoints) for
                        NVIDIA-hosted models (e.g. ``z-ai/glm-5.2``) at the
                        verified ``https://integrate.api.nvidia.com/v1`` base URL
                        (applied automatically when base_url is empty).
    openai           -> ``ChatOpenAI``, base URL optional.
    openai-compatible-> ``ChatOpenAI`` for any OpenAI-compatible endpoint;
                        base_url required.

``z-ai/glm-5.2`` is pre-registered with the NVIDIA client's static model table so
that ``ChatNVIDIA`` construction stays network-free (the package would otherwise
fetch ``/v1/models`` at build time). The ``openai`` / ``openai-compatible``
paths are always lazy -- no network at build time.

No API key is ever included in logs or exception messages.
"""

import warnings

from langchain_nvidia_ai_endpoints import ChatNVIDIA, Model, register_model
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings, settings
from app.core.exceptions import LLMConfigurationError

SUPPORTED_PROVIDERS = frozenset({"nvidia", "openai", "openai-compatible"})

#: Verified NVIDIA OpenAI-compatible Chat Completions endpoint (build.nvidia.com).
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

#: Model absent from the NVIDIA client's static table; registering it skips the
#: construction-time registry lookup that would otherwise hit the network.
DEFAULT_NVIDIA_MODEL = "z-ai/glm-5.2"

_GLM_REGISTERED = False


def get_llm(config: Settings | None = None) -> ChatOpenAI | ChatNVIDIA | None:
    """Return a configured LangChain chat model, or ``None`` when the LLM is disabled.

    Raises ``LLMConfigurationError`` when the LLM is enabled but the provider is
    unsupported or a required setting is missing. Construction performs no
    network I/O for any provider.
    """
    conf = config or settings
    if not conf.llm_enabled:
        return None
    _validate(conf)
    if conf.llm_provider == "nvidia":
        return _build_chat_nvidia(conf)
    return ChatOpenAI(
        model=conf.llm_model,
        api_key=SecretStr(conf.llm_api_key.get_secret_value()),
        base_url=_base_url(conf),
        temperature=conf.llm_temperature,
        max_tokens=conf.llm_max_tokens,  # type: ignore[call-arg]
        top_p=conf.llm_top_p,
        seed=conf.llm_seed,
        max_retries=conf.llm_max_retries,
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


def _build_chat_nvidia(conf: Settings) -> ChatNVIDIA:
    if conf.llm_model == DEFAULT_NVIDIA_MODEL:
        _register_default_model()
    try:
        return ChatNVIDIA(
            model=conf.llm_model,
            api_key=conf.llm_api_key.get_secret_value(),
            base_url=_base_url(conf),
            temperature=conf.llm_temperature,
            max_completion_tokens=conf.llm_max_tokens,
            top_p=conf.llm_top_p,
            seed=conf.llm_seed,
        )
    except Exception as exc:  # client init failure
        raise LLMConfigurationError(
            f"Failed to initialize NVIDIA chat model '{conf.llm_model}': "
            f"{type(exc).__name__}"
        ) from exc


def _base_url(conf: Settings) -> str | None:
    if conf.llm_base_url:
        return conf.llm_base_url
    if conf.llm_provider == "nvidia":
        return NVIDIA_BASE_URL
    return None


def _validate(conf: Settings) -> None:
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
