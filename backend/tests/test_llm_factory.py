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
from app.llm.factory import NVIDIA_BASE_URL, generation_caps, get_llm
from app.llm.fallback import FallbackChatModel

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


# --- multi-model roster (fallback chain) -------------------------------------


def _roster_settings(**overrides) -> Settings:
    defaults: dict[str, Any] = {
        "llm_enabled": True,
        "llm_models": [
            {
                "provider": "nvidia",
                "model": "z-ai/glm-5.2",
                "api_key": _FAKE_KEY,
            },
            {
                "provider": "nvidia",
                "model": "nvidia/nemotron-3-ultra-550b-a55b",
                "api_key": "nvapi-second-key-not-a-real-secret",
            },
        ],
    }
    defaults.update(overrides)
    return Settings(_env_file=None, **defaults)  # type: ignore[call-arg]


def test_roster_builds_fallback_chain(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    llm = get_llm(_roster_settings())
    assert isinstance(llm, FallbackChatModel)
    assert llm.available_models == ["z-ai/glm-5.2", "nvidia/nemotron-3-ultra-550b-a55b"]
    assert llm.model == "z-ai/glm-5.2"
    assert llm.last_used_model is None
    assert len(llm._clients) == 2
    assert llm._clients[0].kwargs["model"] == "z-ai/glm-5.2"
    assert llm._clients[1].kwargs["model"] == "nvidia/nemotron-3-ultra-550b-a55b"


def test_single_roster_entry_returns_bare_client(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    conf = _roster_settings(llm_models=[_roster_settings().llm_models[0]])
    llm = get_llm(conf)
    assert isinstance(llm, _FakeChatNVIDIA)
    assert not isinstance(llm, FallbackChatModel)


def test_roster_missing_api_key_fails_clearly() -> None:
    bad = {"provider": "nvidia", "model": "z-ai/glm-5.2", "api_key": ""}
    conf = _roster_settings(llm_models=[bad])
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(conf)
    message = str(excinfo.value)
    assert "z-ai/glm-5.2" in message
    assert _FAKE_KEY not in message


def test_roster_invalid_provider_fails_clearly() -> None:
    bad = {"provider": "bedrock", "model": "claude", "api_key": _FAKE_KEY}
    conf = _roster_settings(llm_models=[bad])
    with pytest.raises(LLMConfigurationError) as excinfo:
        get_llm(conf)
    assert "bedrock" in str(excinfo.value)
    assert _FAKE_KEY not in str(excinfo.value)


# --- FallbackChatModel behaviour ---------------------------------------------


class _FakeClient:
    def __init__(self, name: str, fail: bool = False) -> None:
        self.name = name
        self.fail = fail

    def invoke(self, messages, **kwargs):  # type: ignore[no-untyped-def]
        if self.fail:
            raise RuntimeError(f"underlying failure on {self.name}")
        return f"ok:{self.name}"


def test_fallback_switches_to_next_model_on_failure() -> None:
    chain = FallbackChatModel(
        clients=[_FakeClient("model-a", fail=True), _FakeClient("model-b")],
        model_names=["model-a", "model-b"],
    )
    response = chain.invoke([("user", "hi")])
    assert response == "ok:model-b"
    assert chain.last_used_model == "model-b"
    assert chain.model == "model-b"


def test_fallback_returns_primary_when_it_succeeds() -> None:
    chain = FallbackChatModel(
        clients=[_FakeClient("model-a"), _FakeClient("model-b", fail=True)],
        model_names=["model-a", "model-b"],
    )
    response = chain.invoke([("user", "hi")])
    assert response == "ok:model-a"
    assert chain.last_used_model == "model-a"


def test_fallback_all_fail_raises_sanitized_error() -> None:
    chain = FallbackChatModel(
        clients=[_FakeClient("a", fail=True), _FakeClient("b", fail=True)],
        model_names=["model-a", "model-b"],
    )
    with pytest.raises(RuntimeError) as excinfo:
        chain.invoke([("user", "hi")])
    message = str(excinfo.value)
    assert "model-b" in message
    assert "RuntimeError" in message
    # The underlying exception detail (which could echo payloads) is not leaked.
    assert "underlying failure" not in message


# --- per-call generation caps -------------------------------------------------


def test_generation_caps_nvidia_uses_max_completion_tokens() -> None:
    caps = generation_caps(_settings(), max_tokens=1024)
    assert caps == {"max_completion_tokens": 1024}


def test_generation_caps_nvidia_omits_reasoning_budget_when_unset() -> None:
    caps = generation_caps(_settings(), max_tokens=2048)
    assert caps == {"max_completion_tokens": 2048}


def test_generation_caps_nvidia_clamps_reasoning_budget() -> None:
    conf = _roster_settings(
        llm_models=[
            {
                "provider": "nvidia",
                "model": "nvidia/nemotron-3-ultra-550b-a55b",
                "api_key": _FAKE_KEY,
                "reasoning_budget": 16384,
            }
        ]
    )
    caps = generation_caps(conf, max_tokens=2048)
    assert caps == {"max_completion_tokens": 2048, "reasoning_budget": 2048}


def test_generation_caps_openai_uses_max_tokens() -> None:
    caps = generation_caps(_settings(llm_provider="openai", llm_base_url=""), max_tokens=1024)
    assert caps == {"max_tokens": 1024}


def test_generation_caps_openai_compatible_uses_max_tokens() -> None:
    conf = _settings(
        llm_provider="openai-compatible",
        llm_base_url="http://127.0.0.1:8787/v1",
    )
    caps = generation_caps(conf, max_tokens=1024)
    assert caps == {"max_tokens": 1024}


def test_generation_caps_mixed_roster_returns_none(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    conf = _roster_settings(
        llm_models=[
            {"provider": "nvidia", "model": "z-ai/glm-5.2", "api_key": _FAKE_KEY},
            {"provider": "openai", "model": "gpt-x", "api_key": "sk-not-real"},
        ]
    )
    assert generation_caps(conf, max_tokens=1024) is None


# --- provider request timeout -------------------------------------------------


def test_timeout_seconds_default_preserves_provider_default() -> None:
    assert _settings().llm_timeout_seconds == 60


def test_nvidia_client_receives_configured_timeout(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    llm = get_llm(_settings(llm_timeout_seconds=30))
    assert isinstance(llm, _FakeChatNVIDIA)
    assert llm.kwargs["timeout"] == 30


def test_openai_client_receives_configured_timeout() -> None:
    llm = get_llm(
        _settings(
            llm_provider="openai-compatible",
            llm_base_url="http://127.0.0.1:8787/v1",
            llm_timeout_seconds=30,
        )
    )
    assert isinstance(llm, ChatOpenAI)
    assert llm.request_timeout == 30


def test_roster_clients_receive_configured_timeout(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    llm = get_llm(_roster_settings(llm_timeout_seconds=30))
    assert isinstance(llm, FallbackChatModel)
    assert llm._clients[0].kwargs["timeout"] == 30
    assert llm._clients[1].kwargs["timeout"] == 30


def test_roster_entry_can_override_the_global_timeout(monkeypatch) -> None:
    monkeypatch.setattr("app.llm.factory.ChatNVIDIA", _FakeChatNVIDIA)
    conf = _roster_settings(
        llm_timeout_seconds=30,
        llm_models=[
            {
                "provider": "nvidia",
                "model": "z-ai/glm-5.2",
                "api_key": _FAKE_KEY,
                "timeout_seconds": 12,
            },
            {
                "provider": "nvidia",
                "model": "nvidia/nemotron-3-ultra-550b-a55b",
                "api_key": "nvapi-second-key-not-a-real-secret",
            },
        ],
    )
    llm = get_llm(conf)
    assert isinstance(llm, FallbackChatModel)
    assert llm._clients[0].kwargs["timeout"] == 12
    assert llm._clients[1].kwargs["timeout"] == 30


def test_timeout_does_not_change_generation_caps() -> None:
    caps = generation_caps(_settings(llm_timeout_seconds=30), max_tokens=1024)
    assert caps == {"max_completion_tokens": 1024}
