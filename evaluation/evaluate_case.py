"""Post-run evaluation of a FROZEN case result against an answer key. Evaluator-only code.

This file is never imported by the pipeline (opportunity_finder/) and the agents have no tool
that reaches it or the expectations file. Run it only after a case has finished; it reads
cases/<id>/result.json and writes evaluations/<id>/report.json (outside the case folder, so the
agent's own files stay untouched).

Expectations file (JSON, written by the evaluator from the case's answer key; keep it in the
evaluator-only folder of the case, never in documents/):
{
  "expected_industry": "trailer manufacturing",
  "expected_top_picks": [["quote", "spec"], ["inventory", "shortage"], ["warranty"]],
      # each pick is a list of keywords; a recommended idea matches a pick if its name or
      # description contains every keyword (case-insensitive)
  "planted_issues": [["purchase order", "approval"], ...],   # optional; same matching, any idea
  "forbidden_claims": ["linkedin.com/company", "tiktok", "@laurelrun"],   # strings that must not
      # appear anywhere in the recommendation text (invented profiles, handles, outages)
  "min_citation_coverage": 0.6
}

    python evaluation/evaluate_case.py <case_id> <expectations.json> [--cases-dir cases]
"""
import argparse
import json
import sys
from pathlib import Path


def _text_of(result: dict) -> str:
    """Every piece of model-written text in the result, lower-cased, for forbidden-claim checks."""
    parts = []
    for o in result.get("scored_opportunities", []):
        parts += [o.get("name", ""), o.get("what_the_agent_does", ""), o.get("gap", ""), o.get("rating_reason", "")]
    for r in result.get("roadmaps", []):
        parts += [r.get("rationale", ""), r.get("pilot_reason", ""), r.get("assumption", "")]
    for p in result.get("process_map", {}).get("processes", []):
        parts += [p.get("description", ""), *p.get("pain_points", [])]
    fr = result.get("final_recommendation") or {}
    parts += [json.dumps(fr.get("roadmap", {})), json.dumps(result.get("website_assessment", {}))]
    return "\n".join(str(x) for x in parts).lower()


def _matches(idea: dict, keywords: list) -> bool:
    hay = f"{idea.get('name', '')} {idea.get('what_the_agent_does', '')} {idea.get('gap', '')}".lower()
    return all(k.lower() in hay for k in keywords)


def evaluate(result: dict, exp: dict, profile: dict | None = None) -> dict:
    opps = result.get("scored_opportunities", [])
    rec = ((result.get("final_recommendation") or {}).get("roadmap") or {}).get("opportunities", [])
    by_name = {o["name"]: o for o in opps}
    recommended = [by_name[n] for n in rec if n in by_name]
    report = {"status": result.get("status"), "verified": result.get("verified"),
              "model_calls": result.get("model_calls"), "recommended": rec}
    # 1. industry
    ind = (profile or result.get("profile") or {}).get("industry", "")
    report["industry"] = {"expected": exp.get("expected_industry"), "got": ind,
                          "match": bool(exp.get("expected_industry")) and exp["expected_industry"].lower() in ind.lower()}
    # 2. agreement with expected picks (top 3 recommended vs the key)
    picks = exp.get("expected_top_picks", [])
    hits = [any(_matches(o, kw) for o in recommended) for kw in picks]
    report["expected_picks"] = {"total": len(picks), "in_recommendation": sum(hits),
                                "detail": [{"keywords": kw, "found": h} for kw, h in zip(picks, hits)],
                                "anywhere_in_candidates": sum(any(_matches(o, kw) for o in opps) for kw in picks)}
    # 3. planted issues surfaced anywhere in the candidate list
    planted = exp.get("planted_issues", [])
    report["planted_issues"] = {"total": len(planted),
                                "surfaced": sum(any(_matches(o, kw) for o in opps) for kw in planted)}
    # 4. citation coverage of the recommended ideas (Verifier's claims)
    claims = ((result.get("final_recommendation") or {}).get("verification") or {}).get("claims", [])
    grounded = sum(1 for c in claims if c.get("grounded"))
    cov = grounded / len(claims) if claims else 0.0
    doc_cited = sum(1 for c in claims if any(b.get("type") == "document" for b in c.get("basis", [])))
    report["citations"] = {"grounded": grounded, "claims": len(claims), "coverage": round(cov, 2),
                           "with_document_citation": doc_cited,
                           "meets_minimum": cov >= exp.get("min_citation_coverage", 0.6)}
    # 5. forbidden claims (invented profiles, handles, outages)
    text = _text_of(result)
    found = [f for f in exp.get("forbidden_claims", []) if f.lower() in text]
    report["forbidden_claims"] = {"checked": len(exp.get("forbidden_claims", [])), "found": found}
    # 6. honesty signals
    report["placeholders_used"] = any(o.get("placeholder") for o in opps)
    report["social_presence_reported"] = (result.get("website_assessment") or {}).get("social_presence")
    report["pass"] = (report["industry"]["match"] and report["citations"]["meets_minimum"]
                      and not found and not report["placeholders_used"])
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case_id")
    ap.add_argument("expectations")
    ap.add_argument("--cases-dir", default="cases")
    a = ap.parse_args()
    case = Path(a.cases_dir) / a.case_id
    result = json.loads((case / "result.json").read_text(encoding="utf-8"))
    profile = json.loads((case / "profile.json").read_text(encoding="utf-8")) if (case / "profile.json").exists() else None
    exp = json.loads(Path(a.expectations).read_text(encoding="utf-8"))
    report = evaluate(result, exp, profile)
    out = Path("evaluations") / a.case_id / "report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nwritten to {out}")
    sys.exit(0 if report["pass"] else 1)


if __name__ == "__main__":
    main()
