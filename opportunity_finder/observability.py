"""Per-call logging: one record for every model call, saved with the run.

Each record says which agent called which model, how many tokens it used, how long it
took, and whether it failed. Records live in state (`call_log`) so they are checkpointed
and parallel branches can both write. `write_run_log` saves them as one JSON file per run.
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def _tokens(response) -> dict:
    """Read token counts from a LangChain response. Missing counts stay None (not 0),
    because some local servers do not report usage."""
    usage = getattr(response, "usage_metadata", None) or {}
    if not usage:
        usage = (getattr(response, "response_metadata", None) or {}).get("token_usage", {}) or {}
    inp = usage.get("input_tokens", usage.get("prompt_tokens"))
    out = usage.get("output_tokens", usage.get("completion_tokens"))
    return {"input_tokens": inp, "output_tokens": out}


def record_call(agent: str, model: str = "stub", response=None, started: float | None = None,
                error: str | None = None) -> dict:
    """Build one log record. With no response it records a stub call (tokens None)."""
    rec = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "agent": agent,
        "model": model,
        "seconds": round(time.perf_counter() - started, 3) if started is not None else None,
        "error": error,
        "stub": response is None and error is None,
    }
    rec.update(_tokens(response))
    return rec


def invoke_logged(llm, messages, agent: str, model: str):
    """Call an LLM and return (response, record). Never hides an error: the record is
    still produced, then the exception is re-raised with the record attached."""
    started = time.perf_counter()
    try:
        response = llm.invoke(messages)
    except Exception as exc:
        exc.call_record = record_call(agent, model, started=started, error=repr(exc)[:300])
        raise
    return response, record_call(agent, model, response, started)


def summarize(call_log: list) -> dict:
    """Totals for the run summary, overall and per agent. Only REAL model calls are counted:
    records flagged `stub` (written by older versions for agents that did not call a model) are
    left out and reported separately. Token totals skip calls that did not report usage."""
    real = [c for c in call_log if not c.get("stub")]
    by_agent: dict = {}
    for c in real:
        a = by_agent.setdefault(c["agent"], {"calls": 0, "input_tokens": 0, "output_tokens": 0,
                                             "seconds": 0.0, "errors": 0, "models": []})
        a["calls"] += 1
        a["input_tokens"] += c.get("input_tokens") or 0
        a["output_tokens"] += c.get("output_tokens") or 0
        a["seconds"] = round(a["seconds"] + (c.get("seconds") or 0), 3)
        a["errors"] += 1 if c.get("error") else 0
        if c.get("model") and c["model"] not in a["models"]:
            a["models"].append(c["model"])
    return {
        "calls": len(real),
        "calls_by_agent": {k: v["calls"] for k, v in by_agent.items()},
        "by_agent": by_agent,
        "input_tokens": sum(a["input_tokens"] for a in by_agent.values()),
        "output_tokens": sum(a["output_tokens"] for a in by_agent.values()),
        "calls_without_usage": sum(1 for c in real if c.get("input_tokens") is None),
        "errors": sum(1 for c in real if c.get("error")),
        "seconds": round(sum(c["seconds"] for c in real if c.get("seconds")), 3),
        "stub_records_ignored": len(call_log) - len(real),
    }


def write_run_log(result: dict, thread_id: str, out_dir: str | Path = "runs") -> Path:
    """Save the run's call log, summary, status, trace and pruned branches as JSON."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = out / f"{thread_id}-{stamp}.json"
    log = result.get("call_log", [])
    payload = {
        "thread_id": thread_id,
        "status": result.get("status"),
        "review_rounds": result.get("review_round"),
        "summary": summarize(log),
        "call_log": log,
        "verified": result.get("verified"),
        "flags": result.get("flags", []),
        "trace": result.get("trace", []),
        "pruned_log": result.get("pruned_log", []),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path
