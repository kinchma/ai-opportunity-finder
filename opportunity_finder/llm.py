"""LLM factory with per-agent model settings. Defaults to a local LM Studio server.

Every setting can be overridden per agent. Agent names: discovery_profile,
discovery_research, process_mapper, matcher, strategist, critic, planner. The lookup order is
the function argument, then LLM_<AGENT>_<SETTING>, then LLM_<SETTING>, then the default:

    LLM_BASE_URL / LLM_MODEL / LLM_API_KEY                  (all agents)
    LLM_MATCHER_BASE_URL / LLM_MATCHER_MODEL / ..._API_KEY  (just the matcher)

Privacy guard: a base URL that is not on this computer or its local network counts as
"hosted". Hosted models are refused unless the agent is listed in LLM_ALLOW_HOSTED
(comma-separated agent names, or "all"). So sending data to a hosted model is always an
explicit, per-agent choice. Example for using Claude through OpenRouter in the matcher only:

    LLM_MATCHER_BASE_URL=https://openrouter.ai/api/v1
    LLM_MATCHER_MODEL=<a Claude model id from OpenRouter>
    LLM_MATCHER_API_KEY=<your OpenRouter key>
    LLM_ALLOW_HOSTED=matcher
"""
import ipaddress
import os
from urllib.parse import urlparse

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_MODEL = "qwen2.5-7b-instruct"
DEFAULT_API_KEY = "lm-studio"


class HostedModelNotAllowed(RuntimeError):
    """A hosted (non-local) model was configured for an agent that is not allowed to use one."""


def is_local(base_url: str) -> bool:
    host = urlparse(base_url).hostname or ""
    if host in ("", "localhost") or host.endswith(".local"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private


def _pick(agent: str | None, name: str, default: str) -> str:
    if agent:
        v = os.getenv(f"LLM_{agent.upper()}_{name}")
        if v:
            return v
    return os.getenv(f"LLM_{name}", default)


def llm_settings(agent: str | None = None, model: str | None = None) -> dict:
    """Resolve settings for one agent (see the module docstring for the lookup order)."""
    try:  # optional: read a .env file if python-dotenv is installed
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    base_url = _pick(agent, "BASE_URL", DEFAULT_BASE_URL)
    allow = {a.strip().lower() for a in os.getenv("LLM_ALLOW_HOSTED", "").split(",") if a.strip()}
    hosted = not is_local(base_url)
    return {
        "base_url": base_url,
        "model": model or _pick(agent, "MODEL", DEFAULT_MODEL),
        "api_key": _pick(agent, "API_KEY", DEFAULT_API_KEY),
        "hosted": hosted,
        "hosted_allowed": (not hosted) or "all" in allow or (agent or "").lower() in allow,
    }


def get_llm(agent: str | None = None, model: str | None = None,
            temperature: float = 0.2, timeout: float = 120):
    """Return a chat model for `agent`. Raises HostedModelNotAllowed if that agent points at a
    hosted model without being listed in LLM_ALLOW_HOSTED."""
    from langchain_openai import ChatOpenAI  # imported lazily so stubs run without it

    s = llm_settings(agent, model)
    if not s["hosted_allowed"]:
        raise HostedModelNotAllowed(
            f"{agent or 'this agent'} is configured for a hosted model at {s['base_url']}; "
            f"add '{agent}' to LLM_ALLOW_HOSTED to allow it")
    return ChatOpenAI(model=s["model"], temperature=temperature, base_url=s["base_url"],
                      api_key=s["api_key"], timeout=timeout, max_retries=1)
