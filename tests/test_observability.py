import json

import pytest

from opportunity_finder.main import run
from opportunity_finder.observability import invoke_logged, record_call, summarize, write_run_log


class FakeResponse:
    usage_metadata = {"input_tokens": 120, "output_tokens": 30, "total_tokens": 150}


class FakeLLM:
    def invoke(self, messages):
        return FakeResponse()


class BrokenLLM:
    def invoke(self, messages):
        raise RuntimeError("model server down")


def test_invoke_logged_records_tokens_and_agent():
    resp, rec = invoke_logged(FakeLLM(), ["hi"], "critic", "qwen-test")
    assert isinstance(resp, FakeResponse)
    assert rec["agent"] == "critic" and rec["model"] == "qwen-test"
    assert rec["input_tokens"] == 120 and rec["output_tokens"] == 30
    assert rec["error"] is None and rec["stub"] is False


def test_invoke_logged_keeps_the_error_record():
    with pytest.raises(RuntimeError) as info:
        invoke_logged(BrokenLLM(), ["hi"], "strategist", "qwen-test")
    assert "model server down" in info.value.call_record["error"]


def test_missing_usage_is_none_not_zero():
    rec = record_call("matcher", "qwen-test", response=object())
    assert rec["input_tokens"] is None
    s = summarize([rec])
    assert s["calls_without_usage"] == 1 and s["input_tokens"] == 0


def test_end_to_end_log_matches_model_calls(tmp_path):
    result = run({"name": "Test Co", "industry": "x", "size": "10", "risk_tolerance": 0.4},
                 thread_id="obs-test")
    assert len(result["call_log"]) == result["model_calls"]
    path = write_run_log(result, "obs-test", tmp_path)
    saved = json.loads(path.read_text())
    assert saved["summary"]["calls"] == result["model_calls"]
    assert saved["status"] == result["status"]
