"""By default no test talks to a real model server: a fake LLM answers with empty results
(valid JSON for every agent). Tests that care about the model replies install their own fake,
or use the `scripted` fixture to give each agent its own replies."""
import json
from pathlib import Path

import pytest

from opportunity_finder.agents import common, discovery

FIXTURES = Path(__file__).parent / "fixtures"


class _Reply:
    content = '{"practices": [], "processes": [], "candidates": []}'
    usage_metadata = {"input_tokens": 1, "output_tokens": 1}


class _QuietLLM:
    def invoke(self, messages):
        return _Reply()


@pytest.fixture(autouse=True)
def no_real_llm(monkeypatch):
    monkeypatch.setattr(discovery, "get_llm", lambda **kw: _QuietLLM())
    monkeypatch.setattr(common, "get_llm", lambda **kw: _QuietLLM())


@pytest.fixture(autouse=True)
def ignore_dotenv_file(monkeypatch):
    """Tests must not depend on the developer's own .env (for example one that points agents at
    another machine). llm_settings reads .env through python-dotenv, so turn that into a no-op."""
    try:
        import dotenv
    except ImportError:
        return
    monkeypatch.setattr(dotenv, "load_dotenv", lambda *a, **k: False)
    for key in ("LLM_BASE_URL", "LLM_MODEL", "LLM_CRITIC_MODEL", "LLM_CRITIC_BASE_URL",
                "LLM_STRATEGIST_MODEL", "LLM_STRATEGIST_BASE_URL", "LLM_PLANNER_MODEL"):
        monkeypatch.delenv(key, raising=False)


class _Scripted:
    """Fake model for one agent. Replies are used in order and the last one repeats. A reply is
    a JSON string, a dict (dumped to JSON), an Exception (raised) or a function of the prompt."""

    def __init__(self, agent, script, seen):
        self.agent, self.script, self.seen = agent, script, seen

    def invoke(self, messages):
        prompt = messages[-1][1]
        self.seen.setdefault(self.agent, []).append(prompt)
        replies = self.script.get(self.agent)
        if not replies:
            return _Reply()
        r = replies.pop(0) if len(replies) > 1 else replies[0]
        if callable(r):
            r = r(prompt)
        if isinstance(r, Exception):
            raise r
        reply = _Reply()
        reply.content = r if isinstance(r, str) else json.dumps(r)
        reply.usage_metadata = {"input_tokens": len(prompt) // 4, "output_tokens": len(reply.content) // 4}
        return reply


@pytest.fixture
def scripted(monkeypatch):
    """scripted({"critic": [reply, ...], ...}) installs per-agent fake models and returns a dict
    of the prompts each agent received. Agents not in the script get the quiet empty reply."""
    def install(script: dict) -> dict:
        script = {k: (v if isinstance(v, list) else [v]) for k, v in script.items()}
        seen: dict = {}
        make = lambda agent=None, **kw: _Scripted(agent, script, seen)  # noqa: E731
        monkeypatch.setattr(common, "get_llm", make)
        monkeypatch.setattr(discovery, "get_llm", make)
        return seen
    return install


@pytest.fixture
def fixture_case():
    return lambda name: json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
