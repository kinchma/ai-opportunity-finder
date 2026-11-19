"""Run a synthetic company test case through the case workspace, stage by stage, offline.

A synthetic case is a folder with a case_manifest.json (see cases/Laurel_Run_Test_Case). The
manifest is test-harness metadata: this script reads it to find the local website and the
owner-authorized material; the agents never see the manifest, the generation prompt or the
evaluator-only folder. Each command corresponds to one owner action in app_cases.py, so the
same gate (owner confirmation before any analysis) applies here.

    python scripts/synthetic_case.py create  <case_folder> [--site file|http://127.0.0.1:8000/] [--risk 0.4]
    python scripts/synthetic_case.py discover <case_id>
    python scripts/synthetic_case.py confirm  <case_id> [--industry "..."] [--name "..."] [--note "..."]
    python scripts/synthetic_case.py reject   <case_id> [--reason "..."]
    python scripts/synthetic_case.py share    <case_id> <case_folder> [--only processes,interviews,company,data]
    python scripts/synthetic_case.py analyze  <case_id>
    python scripts/synthetic_case.py status   <case_id>

Evaluation against the case's answer key is a separate step with separate code:
    python evaluation/evaluate_case.py <case_id> <case_folder>/02_evaluator_only_DO_NOT_SHARE/expectations.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opportunity_finder import case_runner, cases  # noqa: E402


def read_manifest(folder: Path) -> dict:
    m = json.loads((folder / "case_manifest.json").read_text(encoding="utf-8"))
    if not m.get("fictional"):
        print("WARNING: manifest does not say fictional: true; use only synthetic or anonymized cases")
    return m


def cmd_create(a):
    folder = Path(a.case_folder).expanduser().resolve()
    m = read_manifest(folder)
    site_root = folder / m["website"]["local_site_root"]
    website = site_root.as_uri() if a.site == "file" else a.site
    company = {"website": website, "risk_tolerance": a.risk}
    if a.linkedin:  # a pasted LinkedIn text fixture, if this synthetic company has one
        company["linkedin_text"] = Path(a.linkedin).read_text(encoding="utf-8")
    cid = cases.create_case(m.get("display_name") or m["case_id"], company)
    cases.add_decision(cid, "synthetic_case", {"manifest_case_id": m["case_id"], "website": website,
                                               "note": "local fixture site; manifest is harness metadata, not evidence"})
    print(f"created case {cid}\n  website: {website}\n  next: discover {cid}")


def cmd_discover(a):
    profile = case_runner.discover(a.case_id)
    src = profile.get("evidence_source", {})
    print(f"industry guess: {profile.get('industry')} ({profile.get('confidence')} confidence)")
    print(f"evidence: {profile.get('evidence') or '(none)'}")
    print(f"read from: {src.get('page')}" + (" [local fixture]" if src.get("local_fixture") else ""))
    if profile.get("note"):
        print(f"note: {profile['note']}")
    print("PAUSED for the owner: run confirm or reject")


def cmd_confirm(a):
    corrections = {k: v for k, v in {"industry": a.industry, "name": a.name}.items() if v}
    p = case_runner.confirm(a.case_id, corrections, note=a.note or "")
    print(f"confirmed: industry={p.get('industry')} corrections={p.get('owner_corrections')}")


def cmd_reject(a):
    case_runner.reject(a.case_id, a.reason or "")
    print("rejected: the case will not proceed until the owner confirms a corrected profile")


def cmd_share(a):
    folder = Path(a.case_folder).expanduser().resolve()
    m = read_manifest(folder)
    root = folder / m["stage_sources"]["later_company_analysis"]
    include = [x.strip() for x in a.only.split(",") if x.strip()] if a.only else None
    try:
        out = case_runner.share(a.case_id, root, include)
    except case_runner.ConfirmationRequired as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
    print(f"shared {len(out['copied'])} file(s) from {out['source_root']}")
    for r in out["refused"]:
        print(f"  refused {r['path']}: {r['reason']}")


def cmd_analyze(a):
    try:
        r = case_runner.analyze(a.case_id)
    except case_runner.ConfirmationRequired as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
    rec = (r.get("final_recommendation") or {}).get("roadmap") or {}
    print(f"status: {r.get('status')}  verified: {r.get('verified')}  model calls: {r.get('model_calls')}")
    print(f"recommended: {rec.get('opportunities')}")
    for t in r.get("trace", []):
        print("  ", t)


def cmd_status(a):
    meta = cases.load_case(a.case_id)
    ok, why = case_runner.confirmation_ok(a.case_id)
    print(f"{meta['id']}: stage={meta['stage']}  analysis allowed={ok}" + (f" ({why})" if why else ""))
    print(f"documents on file: {len(cases.list_document_files(a.case_id))}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("case_folder"); c.add_argument("--site", default="file")
    c.add_argument("--risk", type=float, default=0.4); c.add_argument("--linkedin", default=None); c.set_defaults(fn=cmd_create)
    d = sub.add_parser("discover"); d.add_argument("case_id"); d.set_defaults(fn=cmd_discover)
    f = sub.add_parser("confirm"); f.add_argument("case_id"); f.add_argument("--industry"); f.add_argument("--name")
    f.add_argument("--note"); f.set_defaults(fn=cmd_confirm)
    r = sub.add_parser("reject"); r.add_argument("case_id"); r.add_argument("--reason"); r.set_defaults(fn=cmd_reject)
    s = sub.add_parser("share"); s.add_argument("case_id"); s.add_argument("case_folder"); s.add_argument("--only")
    s.set_defaults(fn=cmd_share)
    z = sub.add_parser("analyze"); z.add_argument("case_id"); z.set_defaults(fn=cmd_analyze)
    t = sub.add_parser("status"); t.add_argument("case_id"); t.set_defaults(fn=cmd_status)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
