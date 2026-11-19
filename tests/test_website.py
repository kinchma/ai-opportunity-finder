from opportunity_finder.agents import discovery, matcher, website
from opportunity_finder.tools.site_signals import analyze_html

HTML_PLAIN = ("<html><head><title>Acme</title><meta name='description' content='x'>"
              "<meta name='viewport' content='width=device-width'></head><body><h1>Acme Trailers</h1>"
              "<p>Contact us for a free estimate. <a href='tel:5551234'>Call</a></p><img src='a.jpg' alt='trailer'></body></html>")
HTML_CHAT = HTML_PLAIN.replace("</body>", "<script src='https://widget.intercom.io/widget/abc'></script></body>")


class Reply:
    usage_metadata = {"input_tokens": 1, "output_tokens": 1}

    def __init__(self, content):
        self.content = content


class FakeLLM:
    def __init__(self, *replies):
        self.replies = list(replies)

    def invoke(self, messages):
        self.last = messages
        return Reply(self.replies.pop(0))


GOOD = ('{"clarity": 8, "clarity_reason": "says trailers", "action": 6, "action_reason": "estimate link", '
        '"trust": 4, "trust_reason": "no reviews", "starter_prompts": ["Get a quote", "Dealer pricing", "Call me back"]}')


def site(html):
    return {"url": "https://acme.example", "title": "Acme", "description": "", "text": "We build trailers.",
            "error": None, "signals": analyze_html(html, "https://acme.example")}


def test_signals_find_widget_and_basics():
    s = analyze_html(HTML_CHAT, "https://x.example")
    assert s["chat_widgets"] == ["Intercom"] and s["mobile_viewport"] and s["phone_link"] and s["h1_count"] == 1
    assert analyze_html(HTML_PLAIN)["chat_widgets"] == []


def test_chatbot_not_found_wording_and_status():
    c = website.chatbot_finding(analyze_html(HTML_PLAIN))
    assert c["status"] == "not_found" and "pages read" in c["message"]


def test_rating_is_calculated_by_code(monkeypatch):
    monkeypatch.setattr(website, "ask_json", lambda agent, msgs, v: (v(__import__("json").loads(GOOD)), [], ""))
    a, _ = website.assess_website(site(HTML_PLAIN), {"name": "Acme"})
    subs = {s["name"]: s for s in a["sub_ratings"]}
    assert subs["Clear offer"]["basis"] == "model" and subs["Mobile-ready"]["basis"] == "code"
    expected = website.rate({s["name"]: (s["score"], "") for s in a["sub_ratings"]})
    assert a["rating"] == expected and 1 <= a["rating"] <= 10 and not a["partial"]
    assert a["starter_prompts"] == ["Get a quote", "Dealer pricing", "Call me back"]


def test_model_failure_gives_partial_code_only_rating(monkeypatch):
    monkeypatch.setattr(website, "ask_json", lambda agent, msgs, v: (None, [], "model not available"))
    a, _ = website.assess_website(site(HTML_PLAIN), {})
    assert a["partial"] and all(s["basis"] == "code" for s in a["sub_ratings"]) and a["rating"]
    assert a["starter_prompts"] == website.DEFAULT_PROMPTS


def test_linkedin_text_is_labelled_and_capped(monkeypatch):
    seen = {}
    monkeypatch.setattr(website, "ask_json", lambda agent, msgs, v: (seen.update(m=msgs[1][1]) or None, [], ""))
    a, _ = website.assess_website(site(HTML_PLAIN), {}, "Q" * 5000)
    assert "Pasted by the owner from the company's LinkedIn page" in seen["m"] and seen["m"].count("Q") == 2000
    assert a["linkedin_used"]


def test_discovery_stores_assessment(monkeypatch):
    monkeypatch.setattr(discovery, "fetch_site_text", lambda url: site(HTML_PLAIN))
    llm = FakeLLM('{"name": "Acme", "industry": "trailers", "confidence": "high", "evidence": "e"}', GOOD)
    monkeypatch.setattr(discovery, "get_llm", lambda **kw: llm)
    from opportunity_finder.agents import common
    monkeypatch.setattr(common, "get_llm", lambda **kw: llm)
    out = discovery.discovery_profile({"company_input": {"website": "acme.example"}})
    assert out["website_assessment"]["chatbot"]["status"] == "not_found" and out["model_calls"] == 2


def test_matcher_adds_assistant_only_when_no_chat():
    none_found = {"chatbot": {"status": "not_found", "message": "No chat widget found on the pages read."},
                  "starter_prompts": ["Get a quote", "Ask a question", "Call me back"]}
    c = matcher.website_assistant_candidate(none_found, 0.5)
    assert c["name"] == "Website AI assistant" and 0 <= c["score"] <= 1 and "Get a quote" in c["what_the_agent_does"]
    assert matcher.website_assistant_candidate({"chatbot": {"status": "found"}}, 0.5) is None
    assert matcher.website_assistant_candidate(None, 0.5) is None
