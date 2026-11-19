import pytest

from opportunity_finder.llm import HostedModelNotAllowed, get_llm, is_local, llm_settings


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    import os
    for k in list(os.environ):
        if k.startswith("LLM_"):
            monkeypatch.delenv(k)


def test_per_agent_settings_override_global(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "global-model")
    monkeypatch.setenv("LLM_CRITIC_MODEL", "critic-model")
    assert llm_settings(agent="critic")["model"] == "critic-model"
    assert llm_settings(agent="strategist")["model"] == "global-model"
    assert llm_settings(agent="critic", model="explicit")["model"] == "explicit"


def test_is_local():
    assert is_local("http://localhost:1234/v1") and is_local("http://192.168.1.20:1234/v1")
    assert is_local("http://nuc.local:11434/v1")
    assert not is_local("https://openrouter.ai/api/v1") and not is_local("https://api.anthropic.com/v1")


def test_hosted_model_is_refused_unless_allowed(monkeypatch):
    monkeypatch.setenv("LLM_MATCHER_BASE_URL", "https://openrouter.ai/api/v1")
    with pytest.raises(HostedModelNotAllowed):
        get_llm(agent="matcher")
    assert llm_settings(agent="matcher")["hosted"] is True
    monkeypatch.setenv("LLM_ALLOW_HOSTED", "matcher")
    assert get_llm(agent="matcher").model_name  # allowed now
    with pytest.raises(HostedModelNotAllowed):      # other agents are still blocked if hosted
        monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
        get_llm(agent="critic")


def test_local_agents_unaffected_by_another_agents_hosted_setting(monkeypatch):
    monkeypatch.setenv("LLM_MATCHER_BASE_URL", "https://openrouter.ai/api/v1")
    assert llm_settings(agent="strategist")["hosted"] is False
