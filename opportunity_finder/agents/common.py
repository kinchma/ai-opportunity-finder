"""Shared helper for agents that ask the LLM for one JSON object."""
import json
import re

from ..llm import get_llm, llm_settings
from ..observability import invoke_logged, record_call


def json_object(content: str) -> dict | None:
    """First JSON object in a reply (tolerates <think> blocks and code fences)."""
    content = re.sub(r"<think>.*?</think>", "", content or "", flags=re.S)
    m = re.search(r"\{.*\}", content, flags=re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def match_chunk_id(cid, by_id: dict) -> str | None:
    """Map the id a model wrote to a retrieved passage id. Accepts the exact id, or the id with
    brackets, quotes, backticks, spaces or different capitals around it, or inside a longer
    string such as "[a#1] (Test Source)". Returns the real id, or None if it matches nothing."""
    if not isinstance(cid, str):
        return None
    if cid in by_id:
        return cid
    text = cid.strip().strip("[](){}<>\"'`").strip().lower()
    for real in by_id:
        if text == real.lower():
            return real
    # a real id inside a longer string; prefer the longest id, and do not match part of another id
    for real in sorted(by_id, key=len, reverse=True):
        if re.search(r"(?<![\w#-])" + re.escape(real.lower()) + r"(?![\w#])", cid.lower()):
            return real
    return None


def ask_json(agent: str, messages: list, validate, temperature: float = 0.0, attempts: int = 2,
             raw_out: list | None = None):
    """Call the agent's model and validate the reply. Returns (result, records, note).

    `validate(dict | None)` returns the cleaned result or None if unusable. One retry on bad
    JSON. Never raises: a model that is missing, blocked by the hosted-model guard or failing
    comes back as (None, records, note), with every real call recorded."""
    model_name = llm_settings(agent=agent)["model"]
    try:
        llm = get_llm(agent=agent, temperature=temperature)
    except Exception as exc:
        return None, [], f"model not available: {exc}"[:200]
    records: list = []
    for _ in range(attempts):
        try:
            resp, rec = invoke_logged(llm, messages, agent, model_name)
        except Exception as exc:
            records.append(getattr(exc, "call_record", record_call(
                agent, model_name, error=repr(exc)[:300])))
            return None, records, f"LLM call failed: {exc}"[:200]
        records.append(rec)
        if raw_out is not None:  # lets the caller keep a sample of what the model actually wrote
            raw_out.append(str(resp.content or "")[:500])
        result = validate(json_object(resp.content))
        if result is not None:
            return result, records, ""
    return None, records, "the model did not return valid JSON"
