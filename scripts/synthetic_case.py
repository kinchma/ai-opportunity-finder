"""Run a case through the case workspace, stage by stage, from the command line.

Each command is one owner action in app_cases.py, so the same gate (owner confirmation before
any material is read or any analysis runs) applies here. Works for synthetic test cases such as
cases/laurel-run, whose own website/ folder holds the fixture site.

    python scripts/synthetic_case.py create    "<company name>" [--site local|<url>] [--risk 0.4] [--linkedin file.txt]
    python scripts/synthetic_case.py discover  <case_id>
    python scripts/synthetic_case.py confirm   <case_id> [--industry "..."] [--name "..."] [--note "..."]
    python scripts/synthetic_case.py reject    <case_id> [--reason "..."]
    python scripts/synthetic_case.py authorize <case_id> --folders documents,interviews,data[,research]
    python scripts/synthetic_case.py share     <case_id> <folder elsewhere> [--only processes,interviews]
    python scripts/synthetic_case.py index     <case_id>   (build or refresh the company's RAG store now)
    python scripts/synthetic_case.py analyze   <case_id>
    python scripts/synthetic_case.py status    <case_id>

Evaluation against an answer key is a separate step with separate code:
    python evaluation/evaluate_case.py <case_id> evaluation/answer_keys/<case>.json [--run run-NNN]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opportunity_finder import case_runner, cases  # noqa: E402
from opportunity_finder.tools import company_rag  # noqa: E402


def cmd_create(a):
    company = {"website": a.site, "risk_tolerance": a.risk}
    if a.linkedin:  # a pasted LinkedIn text fixture, if this company has one
        company["linkedin_text"] = Path(a.linkedin).read_text(encoding="utf-8")
    cid = cases.create_case(a.name, company)
    print(f"created case {cid} in {cases.case_dir(cid)}")
    if a.site == "local":
        print("  website: local (put the synthetic site in the case's website/ folder)")
    print(f"  next: discover {cid}")


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


def cmd_authorize(a):
    folders = [x.strip() for x in a.folders.split(",") if x.strip()]
    try:
        now = case_runner.authorize(a.case_id, folders)
    except (case_runner.ConfirmationRequired, ValueError) as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
    print(f"authorized: {', '.join(now)}  ({len(cases.list_document_files(a.case_id))} readable file(s))")


def cmd_share(a):
    include = [x.strip() for x in a.only.split(",") if x.strip()] if a.only else None
    try:
        out = case_runner.share(a.case_id, Path(a.folder).expanduser(), include)
    except (case_runner.ConfirmationRequired, FileNotFoundError, ValueError) as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
    print(f"imported {len(out['copied'])} file(s) from {out['source_root']}")
    for r in out["refused"]:
        print(f"  refused {r['path']}: {r['reason']}")


def cmd_index(a):
    info = case_runner.refresh_index(a.case_id)
    print(f"company index: mode {info['mode']}" + (f" ({info['reason']})" if info.get("reason") else ""))
    if info["mode"] != "off":
        print(f"  {info.get('passages', 0)} passage(s), embedding model {info.get('embed_model') or '-'}, "
              f"built this time: {info.get('index_rebuilt')}")


def cmd_analyze(a):
    try:
        r = case_runner.analyze(a.case_id)
    except case_runner.ConfirmationRequired as exc:
        print(f"REFUSED: {exc}")
        sys.exit(2)
    rec = (r.get("final_recommendation") or {}).get("roadmap") or {}
    print(f"saved as results/{cases.latest_run(a.case_id)}")
    print(f"status: {r.get('status')}  verified: {r.get('verified')}  model calls: {r.get('model_calls')}")
    print(f"recommended: {rec.get('opportunities')}")
    for t in r.get("trace", []):
        print("  ", t)


def cmd_status(a):
    meta = cases.load_case(a.case_id)
    ok, why = case_runner.confirmation_ok(a.case_id)
    print(f"{meta['id']}: stage={meta['stage']}  analysis allowed={ok}" + (f" ({why})" if why else ""))
    for row in cases.material_summary(a.case_id):
        print(f"  {row['folder']}: {row['files']} file(s), {'authorized' if row['authorized'] else 'NOT authorized'}")
    st = company_rag.index_status(cases.case_dir(a.case_id) / "index", cases.document_chunks(a.case_id))
    print("company index: " + (f"{st['passages']} passage(s), {st['embed_model']}, built {st['built']}, "
                               f"{'up to date' if st['up_to_date'] else 'OUT OF DATE (rebuilt at the next analysis or index)'}"
                               if st["exists"] else "not built yet"))
    print(f"runs: {', '.join(cases.runs(a.case_id)) or 'none'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create"); c.add_argument("name"); c.add_argument("--site", default="local")
    c.add_argument("--risk", type=float, default=0.4); c.add_argument("--linkedin", default=None); c.set_defaults(fn=cmd_create)
    d = sub.add_parser("discover"); d.add_argument("case_id"); d.set_defaults(fn=cmd_discover)
    f = sub.add_parser("confirm"); f.add_argument("case_id"); f.add_argument("--industry"); f.add_argument("--name")
    f.add_argument("--note"); f.set_defaults(fn=cmd_confirm)
    r = sub.add_parser("reject"); r.add_argument("case_id"); r.add_argument("--reason"); r.set_defaults(fn=cmd_reject)
    u = sub.add_parser("authorize"); u.add_argument("case_id"); u.add_argument("--folders", required=True)
    u.set_defaults(fn=cmd_authorize)
    s = sub.add_parser("share"); s.add_argument("case_id"); s.add_argument("folder"); s.add_argument("--only")
    s.set_defaults(fn=cmd_share)
    i = sub.add_parser("index"); i.add_argument("case_id"); i.set_defaults(fn=cmd_index)
    z = sub.add_parser("analyze"); z.add_argument("case_id"); z.set_defaults(fn=cmd_analyze)
    t = sub.add_parser("status"); t.add_argument("case_id"); t.set_defaults(fn=cmd_status)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
