"""Discovery agent: two phases (profile, then best-practice research).

discovery_profile: if company_input has a "website", fetch the page and ask the LLM to
guess the industry (the owner then confirms or corrects it in owner_confirm). Without a
website it falls back to the synthetic stub so the rest of the demo still runs.
"""
import json
import re

from ..llm import get_llm, llm_settings
from ..observability import invoke_logged, record_call
from .common import json_object, match_chunk_id
from .website import assess_website
from ..tools import guard, kb
from ..tools.web import fetch_site_text

SYSTEM_PROMPT = (
    "You classify businesses from website text. Reply with ONLY a JSON object: "
    '{"name": string, "industry": string, "confidence": "low"|"medium"|"high", '
    '"evidence": string}. "industry" is a short phrase such as "trailer manufacturing" '
    'or "regional law firm". "evidence" is one sentence pointing at what on the site '
    'supports your guess. If the text is not enough to tell, use industry "unknown" '
    'and confidence "low". Do not add any other text.'
)
MIN_TEXT_CHARS = 80


_json_object = json_object


def _parse_json(content: str) -> dict | None:
    data = _json_object(content)
    if data is None:
        return None
    industry = data.get("industry")
    if not isinstance(industry, str) or not industry.strip():
        return None
    conf = str(data.get("confidence", "low")).lower()
    return {"name": str(data.get("name") or "").strip(),
            "industry": industry.strip(),
            "confidence": conf if conf in ("low", "medium", "high") else "low",
            "evidence": str(data.get("evidence") or "").strip()}


def _profile_from_website(src: dict) -> tuple[dict, list, str, dict]:
    """Returns (profile, call_records, site_text, site). Never raises: problems become profile['note']."""
    site = fetch_site_text(src["website"])
    site["flags"] = []  # guardrail: cut instruction-like text out of the page before a model sees it
    for field in ("title", "description", "text"):
        site[field], found = guard.scrub(site.get(field) or "", f"website {field}")
        site["flags"] += found
    owner_desc = (src.get("description") or "").strip()
    profile = {"name": src.get("name") or site["title"] or "unknown", "website": site["url"],
               "industry": "unknown", "size": src.get("size", "unknown"),
               "confidence": "low", "evidence": "", "note": "",
               # where the evidence came from: the one page read (title, meta description and
               # visible text), so the owner can check the claim against it
               "evidence_source": {"page": site["url"], "fields": ["title", "description", "text"],
                                   "local_fixture": bool(site.get("local_fixture"))}}
    records: list = []
    if site["error"]:
        profile["note"] = site["error"]
        if not owner_desc:
            return profile, records, "", site
        profile["note"] += " (used the description you provided instead)"
    body = (site["description"] + " " + site["text"] + " " + owner_desc).strip()
    if not owner_desc and len(body) < MIN_TEXT_CHARS:  # an owner's short description is enough
        profile["note"] = "page had almost no readable text (it may need JavaScript)"
        return profile, records, body, site

    user_msg = (f"URL: {site['url']}\nTitle: {site['title']}\n"
                f"Description: {site['description']}\nPage text:\n{site['text']}")
    if owner_desc:
        user_msg += f"\nOwner-provided description: {owner_desc}"
    messages = [("system", SYSTEM_PROMPT), ("human", user_msg)]
    model_name = llm_settings(agent="discovery_profile")["model"]
    try:
        llm = get_llm(agent="discovery_profile", temperature=0.0)
    except Exception as exc:  # for example the hosted-model guard
        profile["note"] = f"model not available: {exc}"[:200]
        return profile, records, body, site
    for attempt in (1, 2):  # one retry if the reply is not valid JSON
        try:
            resp, rec = invoke_logged(llm, messages, "discovery_profile", model_name)
        except Exception as exc:
            records.append(getattr(exc, "call_record", record_call(
                "discovery_profile", model_name, error=repr(exc)[:300])))
            profile["note"] = f"LLM call failed: {exc}"[:200]
            return profile, records, body, site
        records.append(rec)
        parsed = _parse_json(resp.content)
        if parsed:
            profile.update({k: v for k, v in parsed.items() if k != "name" or v})
            return profile, records, body, site
    profile["note"] = "the model did not return valid JSON"
    return profile, records, body, site


def discovery_profile(state: dict) -> dict:
    src = state.get("company_input", {})
    if src.get("website"):
        profile, records, site_text, site = _profile_from_website(src)
        assessment = None
        flags = list(site.get("flags", []))
        linkedin, found = guard.scrub(src.get("linkedin_text", ""), "pasted LinkedIn text")
        flags += found
        if flags:
            profile["note"] = (profile["note"] + f" {len(flags)} instruction-like phrase(s) were found in the "
                               "fetched text and removed before the model read it.").strip()
        if site.get("signals") and not site["error"]:
            assessment, more = assess_website(site, profile, linkedin)
            records = records + more
        label = f"{profile['industry']} ({profile['confidence']})"
        trace = f"discovery_profile: website guess -> {label}" + (
            f" [{profile['note']}]" if profile["note"] else "")
        if assessment:
            trace += f" | website rating {assessment['rating']}/10, chatbot: {assessment['chatbot']['status']}"
        if flags:
            trace += f" | INJECTION SCAN: {len(flags)} phrase(s) removed"
        out = {"profile": profile, "site_text": site_text, "model_calls": len(records),
               "call_log": records, "flags": flags, "trace": [trace]}
        if assessment:
            out["website_assessment"] = assessment
        return out

    profile = {"name": src.get("name", "Synthetic Co"), "industry": src.get("industry", "unknown"),
               "size": src.get("size", "unknown")}
    return {"profile": profile, "model_calls": 0, "call_log": [],  # no model was called
            "trace": ["discovery_profile: draft profile (stub, no website given)"]}


RESEARCH_PROMPT = (
    "You extract business best practices from numbered passages. Use ONLY the passages; "
    "do not add outside knowledge. Reply with ONLY a JSON object: "
    '{"practices": [{"practice": string, "why_it_matters": string, "chunk_id": string}]}. '
    "Give at most 6 practices that an AI agent could help with. Every item must copy its "
    'chunk_id exactly as shown in square brackets. If nothing is relevant, return {"practices": []}.'
)


def _validate_practices(data: dict | None, hits: list) -> tuple[list, int] | None:
    """Keep only practices that cite a retrieved chunk. Returns (kept, dropped) or None if
    the reply is not usable at all."""
    if not data or not isinstance(data.get("practices"), list):
        return None
    by_id = {h["id"]: h for h in hits}
    kept, dropped, seen = [], 0, set()
    for item in data["practices"]:
        cid = match_chunk_id(item.get("chunk_id"), by_id) if isinstance(item, dict) else None
        text = str(item.get("practice", "")).strip() if isinstance(item, dict) else ""
        if cid is None or not text or text.lower() in seen:
            dropped += 1
            continue
        seen.add(text.lower())
        kept.append({"practice": text, "why_it_matters": str(item.get("why_it_matters", "")).strip(),
                     "chunk_id": cid, "source": by_id[cid]["source"], "url": by_id[cid]["url"]})
    return kept, dropped


def discovery_research(state: dict) -> dict:
    """Retrieve curated best-practice passages for the confirmed industry, then have the
    LLM turn them into practices. Every practice must cite a retrieved passage. Runs in
    parallel with process_mapper."""
    industry = state.get("profile", {}).get("industry", "unknown")
    hits, note = kb.retrieve(industry)
    result = {"industry": industry, "practices": [], "note": note,
              "sources": sorted({h["source"] for h in hits}),
              "passages": [{"id": h["id"], "source": h["source"]} for h in hits]}
    records: list = []
    if hits:
        passages = "\n\n".join(f"[{h['id']}] ({h['source']})\n{h['text']}" for h in hits)
        messages = [("system", RESEARCH_PROMPT), ("human", f"Industry: {industry}\n\nPassages:\n{passages}")]
        model_name = llm_settings(agent="discovery_research")["model"]
        try:
            llm = get_llm(agent="discovery_research", temperature=0.0)
        except Exception as exc:  # for example the hosted-model guard
            llm = None
            result["note"] = (result["note"] + f" model not available: {exc}"[:200]).strip()
        last = None  # (kept, dropped) of the latest usable reply
        for attempt in (1, 2) if llm else ():
            try:
                resp, rec = invoke_logged(llm, messages, "discovery_research", model_name)
            except Exception as exc:
                records.append(getattr(exc, "call_record", record_call(
                    "discovery_research", model_name, error=repr(exc)[:300])))
                result["note"] = (result["note"] + f" LLM call failed: {exc}"[:200]).strip()
                break
            records.append(rec)
            checked = _validate_practices(_json_object(resp.content), hits)
            if checked is None or not checked[0]:
                # unusable, or every practice was dropped: keep a short sample of the raw reply so
                # the cause can be diagnosed later, then try once more
                result["raw_reply_sample"] = str(resp.content or "")[:500]
            if checked is not None:
                last = checked
                if checked[0]:
                    break
        else:
            if llm and last is None:
                result["note"] = (result["note"] + " the model did not return valid JSON.").strip()
        if last is not None:
            result["practices"], dropped = last
            if dropped:
                result["note"] = (result["note"] + f" {dropped} practice(s) dropped: no valid source passage.").strip()
            if not result["practices"]:
                result["note"] = (result["note"] + " No usable practices: later agents run without knowledge-base grounding.").strip()
        elif llm and records and not result["practices"] and "LLM call failed" not in result["note"]:
            result["note"] = (result["note"] + " No usable practices: later agents run without knowledge-base grounding.").strip()
    else:
        result["note"] = (result["note"] + " The knowledge base has no passages to search.").strip()

    return {"best_practices": result, "model_calls": len(records), "call_log": records,
            "trace": [f"discovery_research: {len(result['practices'])} practices from "
                      f"{len(hits)} passages" + (f" [{result['note']}]" if result["note"] else "")]}
