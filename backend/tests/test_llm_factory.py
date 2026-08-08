"""LLM factory configuration tests (offline; no network, no real API key).

Verifies that ``get_llm`` returns ``None`` when disabled, fails clearly on
missing/invalid configuration, builds a correctly-configured chat client for
each supported provider (``ChatNVIDIA`` for ``nvidia``, ``ChatOpenAI`` for
``openai`` / ``openai-compatible``), and never leaks the API key in error
messages or ``repr`` output.

``ChatNVIDIA`` construction normally queries the NVIDIA model registry, so the
``nvidia``-provider tests monkeypatch the factory's ``ChatNVIDIA`` with a
recording stub to stay deterministic and offline.
"""

from typing import Any

import pytest
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings
from app.core.exceptions import LLMConfigurationError
from app.llm.factory import NVIDIA_BASE_URL, get_llm

_FAKE_KEY = "nvapi-fake-key-never-used-outside-tests"


class _FakeChatNVIDIA:
    """Records constructor kwargs so nvidia-provider tests stay offline."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs


def _settings(**overrides) -> Settings:
    defaults: dict[str, Any] = {
        "llm_enabled": True,
        "llm_provider": "nvidia",
        "llm_api_key": _FAKE_KEY,
        "llm_model": "z-ai/glm-5.2",
        "llm_base_url": "",
    }
    defaults.update(overrides)
    # _env_file=None keeps tests isolated from the developer's real backend/.env.
    return Settings(_env_file=None, **defaults)  # type: ignore[call-arg]


# --- disabled / offline mode --------------------------------------------------


def test_disabled_llm_returns_none_without_any_credentials() -> None:
    conf = Settings(_env_file=None, llm_enabled=False)  # type: ignore[call-arg]
    assert get_llm(conf) is None


# --- configuration validation -------------------------------------------------


def test_missing_api_key_fails_clearly() -> None:
    conf = _settings(llm_api_key="")
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(conf)
    assert "PROBEIQ_LLM_API_KEY" in str(excinfo.value)


def test_missing_model_fails_clearly() -> None:
    conf = _settings(llm_model="")
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(conf)
    assert "PROBEIQ_LLM_MODEL" in str(excinfo.value)


def test_invalid_provider_fails_clearly() -> None:
    conf = _settings(llm_provider="huggingface")
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(conf)
    message = str(excinfo.value)
    assert "huggingface" in message
    assert "nvidia" in message


def test_openai_compatible_requires_base_url() -> None:
    conf = _settings(llm_provider="openai-compatible", llm_base_url="")
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(conf)
    assert "PROBEIQ_LLM_BASE_URL" in str(excinfo.value)


# --- model construction -------------------------------------------------------


def test_valid_nvidia_config_builds_chat_nvidia(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    llm = get_llm(_settings())
    assert llm is not None
    assert isinstance(llm, _FakeChatNVIDIA)
    assert llm.kwargs["model"] == "z-ai/glm-5.2"
    assert llm.kwargs["api_key"] == _FAKE_KEY
    assert llm.kwargs["base_url"] == NVIDIA_BASE_URL
    assert llm.kwargs["max_completion_tokens"] == 16384
    assert llm.kwargs["top_p"] == 1.0
    assert llm.kwargs["seed"] == 42


def test_nvidia_base_url_can_be_overridden(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    llm = get_llm(_settings(llm_base_url="http://127.0.0.1:8787/v1"))
    assert isinstance(llm, _FakeChatNVIDIA)
    assert llm.kwargs["base_url"] == "http://127.0.0.1:8787/v1"


def test_nvidia_construction_failure_fails_clearly(monkeypatch) -> None:
    class _ExplodingChatNVIDIA:
        def __init__(self, **kwargs) -> None:
            raise RuntimeError("registry unreachable")

    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _ExplodingChatNVIDIA)
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(_settings())
    assert "RuntimeError" in str(excinfo.value)
    assert _FAKE_KEY not in str(excinfo.value)


def test_nvidia_construction_does_not_fetch_registry(monkeypatch) -> None:
    def _explode(self) -> None:
        raise AssertionError("ChatNVIDIA construction fetched the model registry")

    monkeypatch.setattr(ChatNVIDIA, "available_models", property(_explode))
    llm = get_llm(_settings())
    assert llm is not None


def test_openai_provider_builds_without_base_url() -> None:
    llm = get_llm(_settings(llm_provider="openai", llm_base_url=""))
    assert isinstance(llm, ChatOpenAI)
    assert llm.model_name == "z-ai/glm-5.2"


def test_openai_compatible_builds_with_base_url() -> None:
    llm = get_llm(
        _settings(
            llm_provider="openai-compatible",
            llm_base_url="https://integrate.api.nvidia.com/v1",
            llm_model="z-ai/glm-5.2",
        )
    )
    assert isinstance(llm, ChatOpenAI)
    assert llm.openai_api_base == "https://integrate.api.nvidia.com/v1"


def test_custom_retry_count_is_respected() -> None:
    llm = get_llm(
        _settings(
            llm_provider="openai-compatible",
            llm_base_url="http://127.0.0.1:8787/v1",
            llm_max_retries=1,
        )
    )
    assert isinstance(llm, ChatOpenAI)
    assert llm.max_retries == 1


# --- API key safety -----------------------------------------------------------


def test_api_key_is_never_exposed_in_exceptions() -> None:
    # Missing model with a key configured: the error must not echo the key.
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(_settings(llm_model=""))
    assert _FAKE_KEY not in str(excinfo.value)

    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(_settings(llm_provider="bogus"))
    assert _FAKE_KEY not in str(excinfo.value)


def test_settings_hold_the_api_key_as_a_secret() -> None:
    conf = _settings()
    assert isinstance(conf.llm_api_key, SecretStr)
    assert _FAKE_KEY not in repr(conf.llm_api_key)
    assert _FAKE_KEY not in repr(conf)
    assert conf.llm_api_key.get_secret_value() == _FAKE_KEY


def test_default_settings_never_require_a_key_when_disabled() -> None:
    # The application default (LLM disabled) must construct without any key.
    conf = Settings(_env_file=None)  # type: ignore[call-arg]
    assert get_llm(conf) is None
