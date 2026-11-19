from opportunity_finder.llm import DEFAULT_BASE_URL, DEFAULT_MODEL, llm_settings


def test_defaults_point_at_lm_studio(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    s = llm_settings()
    assert s["base_url"] == DEFAULT_BASE_URL and s["model"] == DEFAULT_MODEL


def test_environment_and_argument_override(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("LLM_MODEL", "env-model")
    assert llm_settings()["base_url"] == "https://openrouter.ai/api/v1"
    assert llm_settings()["model"] == "env-model"
    assert llm_settings(model="critic-model")["model"] == "critic-model"
