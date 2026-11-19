"""Unpack a synthetic company produced by evaluation/synthetic/SYNTHETIC_CASE_PROMPT.md.

    python scripts/unpack_case_bundle.py <bundle.txt | bundle.zip> [--dry-run] [--force]

A text bundle has one `=== FILE: <path> ===` line before each file. Paths must start with
cases/ or evaluation/ and stay inside the repository; anything else is refused. Existing files are
not overwritten unless --force. Afterwards it checks the case: case.json, the website, material
folders, file sizes the Process Mapper depends on, and that nothing about the answer key leaked
into the case folder."""
import argparse
import io
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ("cases/", "evaluation/")
LEAK = re.compile(r"answer key|answer_key|planted issue|do not share|evaluator-only", re.I)


def files_from(src: Path) -> dict:
    if src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as z:
            out = {}
            for n in z.namelist():
                if n.endswith("/"):
                    continue
                rel = n.split("/", 1)[1] if not n.startswith(ALLOWED) and "/" in n and n.split("/", 1)[1].startswith(ALLOWED) else n
                out[rel] = z.read(n)
            return out
    text = src.read_text(encoding="utf-8")
    parts = re.split(r"^=== FILE: (.+?) ===\s*$", text, flags=re.M)
    return {parts[i].strip(): parts[i + 1].lstrip("\n").encode("utf-8") for i in range(1, len(parts) - 1, 2)}


def safe(rel: str) -> Path | None:
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts or not rel.startswith(ALLOWED) or any(x.startswith(".") for x in p.parts):
        return None
    return ROOT / p


def check_case(case: Path) -> list:
    issues = []
    meta = json.loads((case / "case.json").read_text()) if (case / "case.json").exists() else None
    if not meta:
        return ["case.json missing or not JSON"]
    if meta.get("id") != case.name:
        issues.append(f"case.json id {meta.get('id')!r} does not match the folder {case.name!r}")
    if meta.get("company_input", {}).get("website") != "local":
        issues.append('company_input.website should be "local"')
    if not (case / "website" / "index.html").exists():
        issues.append("website/index.html missing")
    procs = sorted((case / "documents" / "processes").glob("*.md"))
    if not procs:
        issues.append("no process documents in documents/processes/")
    total = 0
    for p in procs:
        n = len(p.read_text(encoding="utf-8"))
        total += n
        if n > 4500:
            issues.append(f"{p.name}: {n} characters (max 4,500)")
        if not list((case / "interviews").glob(p.name[:2] + "_*interview*.md")):
            issues.append(f"{p.name}: no matching interview (interviews/{p.name[:2]}_..._interview.md)")
    if total > 45000:
        issues.append(f"process documents total {total} characters (max 45,000)")
    for d in ("owner", "results", "index"):
        if (case / d).exists():
            issues.append(f"{d}/ should not be in the package (the app creates it)")
    for p in case.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".md", ".csv", ".json", ".txt", ".html") and p.name != "case.json":
            if LEAK.search(p.read_text(encoding="utf-8", errors="replace")):
                issues.append(f"{p.relative_to(case)} mentions the answer key, planted issues or the evaluation")
    for p in case.rglob("*.md"):
        for para in re.split(r"\n\s*\n", p.read_text(encoding="utf-8")):
            if len(para) > 1200:
                issues.append(f"{p.relative_to(case)}: a paragraph of {len(para)} characters (keep under 800)")
                break
    return issues


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    files = files_from(Path(a.bundle))
    written, refused, cases = [], [], set()
    for rel, data in files.items():
        dest = safe(rel)
        if dest is None:
            refused.append(f"{rel}: outside cases/ or evaluation/")
            continue
        if dest.exists() and not a.force:
            refused.append(f"{rel}: exists (use --force to overwrite)")
            continue
        if rel.startswith("cases/"):
            cases.add(rel.split("/")[1])
        if not a.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        written.append(rel)
    print(f"{'would write' if a.dry_run else 'wrote'} {len(written)} file(s); refused {len(refused)}")
    for r in refused:
        print("  refused", r)
    for c in sorted(cases):
        if a.dry_run:
            continue
        problems = check_case(ROOT / "cases" / c)
        print(f"\ncase {c}: " + ("looks ready" if not problems else f"{len(problems)} problem(s)"))
        for p in problems:
            print("  -", p)
        key = ROOT / "evaluation" / "answer_keys" / f"{c}.json"
        print(f"  answer key: {'found' if key.exists() else 'MISSING'} ({key.relative_to(ROOT)})")
        print(f"  next: python scripts/synthetic_case.py discover {c}")


if __name__ == "__main__":
    main()
