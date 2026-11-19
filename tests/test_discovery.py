from opportunity_finder.agents import discovery
from opportunity_finder.tools.web import extract_text, normalize_url

LONG_TEXT = "We build custom aluminum cargo trailers and dump trailers for contractors. " * 3


def fake_site(text=LONG_TEXT, error=None):
    return lambda url: {"url": "https://acme.example", "title": "Acme Trailers", "description": "",
                        "text": text if not error else "", "error": error}


class Reply:
    def __init__(self, content):
        self.content = content
        self.usage_metadata = {"input_tokens": 200, "output_tokens": 40}


class FakeLLM:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = 0

    def invoke(self, messages):
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return Reply(r)


def run_discovery(monkeypatch, llm, site=None):
    monkeypatch.setattr(discovery, "fetch_site_text", site or fake_site())
    monkeypatch.setattr(discovery, "get_llm", lambda **kw: llm)
    return discovery.discovery_profile({"company_input": {"website": "acme.example"}})


GOOD = '{"name": "Acme Trailers", "industry": "trailer manufacturing", "confidence": "high", "evidence": "sells trailers"}'


def test_good_json_fills_profile_and_logs_tokens(monkeypatch):
    out = run_discovery(monkeypatch, FakeLLM(GOOD))
    assert out["profile"]["industry"] == "trailer manufacturing"
    assert out["profile"]["confidence"] == "high"
    assert out["model_calls"] == 1 and out["call_log"][0]["input_tokens"] == 200


def test_think_block_and_code_fence_are_tolerated(monkeypatch):
    reply = "<think>hmm</think>\n```json\n" + GOOD + "\n```"
    assert run_discovery(monkeypatch, FakeLLM(reply))["profile"]["industry"] == "trailer manufacturing"


def test_bad_json_retries_once_then_gives_unknown(monkeypatch):
    llm = FakeLLM("not json", "still not json")
    out = run_discovery(monkeypatch, llm)
    assert llm.calls == 2 and out["model_calls"] == 2
    assert out["profile"]["industry"] == "unknown" and out["profile"]["note"]


def test_bad_json_then_good_json_recovers(monkeypatch):
    out = run_discovery(monkeypatch, FakeLLM("oops", GOOD))
    assert out["profile"]["industry"] == "trailer manufacturing" and out["model_calls"] == 2


def test_llm_failure_is_logged_not_raised(monkeypatch):
    out = run_discovery(monkeypatch, FakeLLM(RuntimeError("server down")))
    assert out["profile"]["industry"] == "unknown"
    assert "LLM call failed" in out["profile"]["note"]
    assert out["call_log"][0]["error"] and out["model_calls"] == 1


def test_fetch_error_makes_no_model_call(monkeypatch):
    llm = FakeLLM()
    out = run_discovery(monkeypatch, llm, fake_site(error="HTTP 403 from the site"))
    assert llm.calls == 0 and out["model_calls"] == 0 and out["call_log"] == []
    assert out["profile"]["note"] == "HTTP 403 from the site"


def test_thin_page_makes_no_model_call(monkeypatch):
    llm = FakeLLM()
    out = run_discovery(monkeypatch, llm, fake_site(text="Loading..."))
    assert llm.calls == 0 and "JavaScript" in out["profile"]["note"]


def test_no_website_keeps_the_stub():
    out = discovery.discovery_profile({"company_input": {"name": "X", "industry": "y"}})
    assert out["profile"]["industry"] == "y" and out["call_log"] == [] and out["model_calls"] == 0


def test_extract_text_skips_scripts_and_reads_meta():
    html = ("<html><head><title> Acme </title><meta name='description' content='Trailers'>"
            "<style>.a{}</style></head><body><script>var x=1</script><h1>Hello</h1><p>World</p></body></html>")
    r = extract_text(html)
    assert r["title"] == "Acme" and r["description"] == "Trailers" and r["text"] == "Hello World"


def test_normalize_url():
    assert normalize_url("acme.com") == "https://acme.com"
    assert normalize_url("http://acme.com") == "http://acme.com"


def test_blocked_site_with_owner_description_still_guesses(monkeypatch):
    monkeypatch.setattr(discovery, "fetch_site_text", fake_site(error="HTTP 403 from the site"))
    llm = FakeLLM(GOOD)
    monkeypatch.setattr(discovery, "get_llm", lambda **kw: llm)
    out = discovery.discovery_profile({"company_input": {
        "website": "acme.example", "description": "Acme builds custom aluminum cargo trailers for contractors."}})
    assert llm.calls == 1 and out["profile"]["industry"] == "trailer manufacturing"
    assert "HTTP 403" in out["profile"]["note"] and "description you provided" in out["profile"]["note"]
