"""Case folders: one isolated folder per customer, so work can stop and resume weeks later.

    cases/<case-id>/
        case.json            id, name, stage, status, dates, company_input, authorized folders, latest run
        website/             a synthetic site (test cases only; real companies give a URL)
        documents/           process documents, company profile, policies (subfolders allowed:
                             documents/processes/ marks a file as a process document)
        interviews/          SME interview transcripts
        data/                CSV samples
        research/            outside material: context, not company facts
        owner/               profile.json (as confirmed), decisions.json (every owner decision)
        index/               the company's retrieval index (generated, safe to delete)
        results/
            discovery.json   latest Discovery output (profile guess, site text, website check)
            run-001/         result.json, process_map.json, the run's call log, evaluation.json
            run-002/ ...

The agents read only the material folders (documents, interviews, data, research), and only those
the owner has authorized (case.json "materials_authorized"), plus the website. They never read
owner/, results/ or anything outside the case. Answer keys for synthetic cases live outside cases/
(evaluation/answer_keys/), so no path from a case reaches them.

Nothing important lives only in memory: each stage loads what it needs from the folder and saves
what it produced. Standard library only.
"""
import json
import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path

STAGES = ["new", "discovered", "confirmed", "analyzed"]
STATUS_TEXT = {
    "new": "Case created. Next: run Discovery.",
    "discovered": "Discovery done. Waiting for the owner to confirm the profile.",
    "rejected": "The owner rejected the discovered profile. Nothing proceeds until the owner confirms a corrected profile.",
    "confirmed": "Profile confirmed. Waiting for company material (optional), then run the analysis.",
    "analyzed": "Recommendation ready.",
}
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json"}
MATERIAL_FOLDERS = ("documents", "interviews", "data", "research")
PROFILE, DECISIONS, DISCOVERY = "owner/profile.json", "owner/decisions.json", "results/discovery.json"
# Folders or files that must never be imported into a case, whatever the owner selects:
# evaluation answer keys and generation prompts of a synthetic test case are not company records.
DENY_PATTERNS = ("evaluator", "do_not_share", "do-not-share", "answer_key", "answer-key",
                 "expectations", "case_manifest", "creation_prompt", "desktop_prompt", "grading")
# Where an imported subfolder lands inside the case (first path part of the source).
IMPORT_TARGETS = {"interviews": "interviews", "interview": "interviews", "personas": "interviews/personas",
                  "data": "data", "research": "research", "documents": "documents"}


def base_dir(base=None) -> Path:
    return Path(base or os.getenv("CASES_DIR") or "cases")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def case_dir(case_id: str, base=None) -> Path:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,80}", case_id):
        raise ValueError(f"bad case id: {case_id!r}")
    return base_dir(base) / case_id


def write_json(path: Path, data) -> None:
    """Write atomically so a crash never leaves half a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    replace_with_retry(tmp, path)


def replace_with_retry(tmp: Path, path: Path, attempts: int = 10, wait: float = 0.05) -> None:
    """os.replace, retried briefly. On Windows the swap is refused (PermissionError) while another
    program, typically antivirus or the search indexer, still has the just-written file open."""
    for i in range(attempts):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            if i == attempts - 1:
                raise
            time.sleep(wait * (i + 1))


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "case"


def create_case(name: str, company_input: dict, base=None) -> str:
    """One folder per company, named after it (laurel-run-trailer-works-inc); a second case with
    the same name gets -2, -3 ..."""
    case_id, n = slug(name), 2
    while case_dir(case_id, base).exists():
        case_id, n = f"{slug(name)}-{n}", n + 1
    write_json(case_dir(case_id, base) / "case.json", {
        "id": case_id, "name": name, "stage": "new", "status": STATUS_TEXT["new"],
        "created": _now(), "updated": _now(), "company_input": company_input,
        "materials_authorized": []})
    return case_id


def load_case(case_id: str, base=None) -> dict:
    meta = read_json(case_dir(case_id, base) / "case.json")
    if meta is None:
        raise FileNotFoundError(f"no case {case_id}")
    return meta


def update_case(case_id: str, base=None, **changes) -> dict:
    meta = load_case(case_id, base)
    meta.update(changes)
    meta["updated"] = _now()
    write_json(case_dir(case_id, base) / "case.json", meta)
    return meta


def set_stage(case_id: str, stage: str, base=None) -> dict:
    return update_case(case_id, base, stage=stage, status=STATUS_TEXT[stage])


def tracker_index(stage: str) -> int:
    """Position on the stage tracker; a rejected case sits at the confirmation step."""
    return STAGES.index("discovered") if stage == "rejected" else STAGES.index(stage)


def list_cases(base=None) -> list:
    root = base_dir(base)
    cases = [m for p in sorted(root.glob("*/case.json")) if (m := read_json(p))] if root.exists() else []
    return sorted(cases, key=lambda m: m.get("updated", ""), reverse=True)


def save(case_id: str, relpath: str, data, base=None) -> None:
    write_json(case_dir(case_id, base) / relpath, data)


def load(case_id: str, relpath: str, default=None, base=None):
    return read_json(case_dir(case_id, base) / relpath, default)


def add_decision(case_id: str, kind: str, detail, base=None) -> None:
    items = load(case_id, DECISIONS, [], base)
    items.append({"when": _now(), "kind": kind, "detail": detail})
    save(case_id, DECISIONS, items, base)


def website_for(case_id: str, company_input: dict, base=None) -> str:
    """The website Discovery should read. "local" (or no website at all, when the case has its own
    website/ folder) means the case's synthetic site, resolved on this machine at run time, so a
    case folder works on any computer."""
    site = case_dir(case_id, base) / "website"
    url = (company_input or {}).get("website", "")
    if url == "local" or (not url and (site / "index.html").exists()):
        return site.resolve().as_uri()
    return url


# ------------------------------------------------------------------ company material
def authorized_folders(case_id: str, base=None) -> list:
    got = load_case(case_id, base).get("materials_authorized") or []
    if got is True:                      # cases saved before Nov 17 stored a yes/no
        return list(MATERIAL_FOLDERS)
    return [f for f in MATERIAL_FOLDERS if f in got]


def authorize_materials(case_id: str, folders, base=None) -> list:
    """The owner allows the analysis to read these material folders. Logged as a decision."""
    bad = [f for f in folders if f not in MATERIAL_FOLDERS]
    if bad:
        raise ValueError(f"not a material folder: {', '.join(bad)} (allowed: {', '.join(MATERIAL_FOLDERS)})")
    now = sorted(set(authorized_folders(case_id, base)) | set(folders), key=MATERIAL_FOLDERS.index)
    update_case(case_id, base, materials_authorized=now)
    add_decision(case_id, "materials_authorized", {"folders": list(folders), "now_authorized": now}, base)
    return now


def add_document(case_id: str, filename: str, data: bytes, base=None, folder: str = "documents") -> dict:
    """Store a file the owner uploads into one material folder; uploading is the owner's authorization
    for that folder. Only plain-text types are read by the pipeline for now."""
    if folder not in MATERIAL_FOLDERS:
        raise ValueError(f"not a material folder: {folder}")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name) or "document"
    target = case_dir(case_id, base) / folder
    target.mkdir(parents=True, exist_ok=True)
    (target / safe).write_bytes(data)
    readable = Path(safe).suffix.lower() in TEXT_SUFFIXES
    if folder not in authorized_folders(case_id, base):
        update_case(case_id, base, materials_authorized=sorted(
            set(authorized_folders(case_id, base)) | {folder}, key=MATERIAL_FOLDERS.index))
    add_decision(case_id, "document_added", {"file": f"{folder}/{safe}", "readable": readable}, base)
    return {"file": f"{folder}/{safe}", "readable": readable}


def _material_paths(case_id: str, base=None, folders=None) -> list:
    """Files in the given material folders (default: the authorized ones), sorted; symlinks and
    hidden files skipped, and nothing whose real path leaves the case folder."""
    root = case_dir(case_id, base)
    root_real = root.resolve()
    out = []
    for name in (authorized_folders(case_id, base) if folders is None else folders):
        folder = root / name
        if not folder.is_dir() or folder.is_symlink():
            continue
        for p in sorted(folder.rglob("*")):
            rel = p.relative_to(root)
            if (not p.is_file() or p.is_symlink() or any(part.startswith(".") for part in rel.parts)
                    or root_real not in p.resolve().parents):
                continue
            out.append(p)
    return out


def source_type_of(relpath: str) -> str:
    """What kind of record a file is, from where it sits in the case folder."""
    parts = [x.lower() for x in Path(relpath).parts[:-1]]
    if not parts:
        return "owner_document"
    top = parts[0]
    if top == "interviews":
        return "sme_interview"
    if top == "data":
        return "data_sample"
    if top == "research":
        return "external_research"
    if any(x in ("processes", "process") for x in parts[1:]):
        return "process_document"
    return "owner_document"


def load_documents(case_id: str, base=None, max_chars: int = 6000, per_file: int | None = None) -> list:
    """Readable documents as [{name, text, source_type}], total text capped for a small model.
    `per_file` caps each file so one long document cannot crowd out the others."""
    root = case_dir(case_id, base)
    docs, used = [], 0
    for p in _material_paths(case_id, base):
        if p.suffix.lower() not in TEXT_SUFFIXES or used >= max_chars:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        text = text[: min(max_chars - used, per_file or max_chars)]
        used += len(text)
        rel = p.relative_to(root).as_posix()
        docs.append({"name": rel, "text": text, "source_type": source_type_of(rel)})
    return docs


def document_chunks(case_id: str, base=None, max_chars: int = 900) -> list:
    """Readable documents split into citable chunks: {id, name, source_type, heading, text}.
    Markdown is split at headings, then paragraphs are grouped up to ~max_chars (a paragraph is
    never split). CSV files become one chunk of header plus the first rows. Ids look like
    "doc:documents/processes/08_quoting.md#3" so a citation says exactly which file and section."""
    root = case_dir(case_id, base)
    chunks = []
    for p in _material_paths(case_id, base):
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = p.relative_to(root).as_posix()
        text = p.read_text(encoding="utf-8", errors="replace")
        stype = source_type_of(rel)
        if p.suffix.lower() == ".csv":
            lines = text.splitlines()
            body = "\n".join(lines[:12]) + (f"\n... ({len(lines) - 12} more rows)" if len(lines) > 12 else "")
            chunks.append({"id": f"doc:{rel}#1", "name": rel, "source_type": stype, "heading": "", "text": body[:max_chars]})
            continue
        heading, pieces, cur = "", [], ""
        for para in re.split(r"\n\s*\n", text):
            para = para.strip()
            if not para:
                continue
            if re.match(r"^#{1,6}\s", para):
                if cur:
                    pieces.append((heading, cur))
                    cur = ""
                heading = re.sub(r"^#{1,6}\s*", "", para.splitlines()[0]).strip()
                rest = "\n".join(para.splitlines()[1:]).strip()
                if rest:
                    cur = rest
                continue
            if cur and len(cur) + len(para) > max_chars:
                pieces.append((heading, cur))
                cur = para
            else:
                cur = f"{cur}\n\n{para}" if cur else para
        if cur:
            pieces.append((heading, cur))
        for i, (h, t) in enumerate(pieces, 1):
            chunks.append({"id": f"doc:{rel}#{i}", "name": rel, "source_type": stype, "heading": h, "text": t})
    return chunks


def list_document_files(case_id: str, base=None, authorized_only: bool = True) -> list:
    """Material files relative to the case folder (documents/..., interviews/...)."""
    root = case_dir(case_id, base)
    folders = None if authorized_only else list(MATERIAL_FOLDERS)
    return [p.relative_to(root).as_posix() for p in _material_paths(case_id, base, folders)]


def material_summary(case_id: str, base=None) -> list:
    """[{folder, files, authorized}] for every material folder that has files, for the UI."""
    auth = set(authorized_folders(case_id, base))
    rows = []
    for f in MATERIAL_FOLDERS:
        n = len(_material_paths(case_id, base, [f]))
        if n:
            rows.append({"folder": f, "files": n, "authorized": f in auth})
    return rows


def _denied(relpath: Path) -> bool:
    low = "/".join(relpath.parts).lower()
    return any(pat in low for pat in DENY_PATTERNS) or any(part.startswith(".") for part in relpath.parts)


def _import_target(rel: Path) -> Path:
    """interviews/x.md -> interviews/x.md; personas/x.md -> interviews/personas/x.md;
    processes/x.md -> documents/processes/x.md; README.md -> documents/README.md."""
    first = rel.parts[0].lower() if len(rel.parts) > 1 else ""
    if first in IMPORT_TARGETS:
        return Path(IMPORT_TARGETS[first], *rel.parts[1:])
    return Path("documents", *rel.parts)


def share_materials(case_id: str, source_root, include=None, base=None) -> dict:
    """Import owner-authorized files from a folder elsewhere on this computer into the case's
    material folders (interviews/ -> interviews/, data/ -> data/, research/ -> research/,
    personas/ -> interviews/personas/, anything else -> documents/), and authorize those folders.

    The copy enforces a boundary rather than trusting folder names: the real path of every file
    must stay inside `source_root`, symlinks are refused, hidden files are refused, and anything
    whose path matches DENY_PATTERNS (evaluator material, answer keys, generation prompts) is
    refused even if listed. `include` is a list of relative paths or folders inside source_root;
    None means the whole root. Returns {copied: [...], refused: [{path, reason}], source_root}.
    Everything is logged in owner/decisions.json as the owner's sharing decision."""
    root = Path(source_root).expanduser()
    try:
        root_real = root.resolve(strict=True)
    except OSError:
        raise FileNotFoundError(f"materials folder not found: {source_root}")
    if root.is_symlink() or not root_real.is_dir():
        raise ValueError("materials folder must be a real directory, not a symbolic link")
    low_root = root_real.as_posix().lower()          # the whole path, so evaluation/answer_keys/x is refused too
    if any(pat in low_root for pat in DENY_PATTERNS) or root_real.name.startswith("."):
        raise ValueError(f"refusing to share '{root_real.name}': it is evaluation or generation material, not company records")
    dest = case_dir(case_id, base)
    wanted = [root / i for i in (include or ["."])]
    copied, refused, seen, folders = [], [], set(), set()
    for item in wanted:
        if not item.exists():
            refused.append({"path": str(item.relative_to(root) if item.is_relative_to(root) else item), "reason": "not found"})
            continue
        files = [item] if item.is_file() else sorted(q for q in item.rglob("*") if q.is_file() or q.is_symlink())
        for q in files:
            try:
                rel = q.relative_to(root)
            except ValueError:
                refused.append({"path": str(q), "reason": "outside the shared folder"})
                continue
            key = rel.as_posix()
            if key in seen:
                continue
            seen.add(key)
            if q.is_symlink() or any(part.is_symlink() for part in [q, *q.parents] if part != root):
                refused.append({"path": key, "reason": "symbolic link"})
                continue
            real = q.resolve()
            if root_real not in real.parents:
                refused.append({"path": key, "reason": "resolves outside the shared folder"})
                continue
            if _denied(rel):
                refused.append({"path": key, "reason": "evaluation, hidden or generation material"})
                continue
            target = _import_target(rel)
            (dest / target).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(real, dest / target)
            copied.append(target.as_posix())
            folders.add(target.parts[0])
    add_decision(case_id, "materials_shared", {"source_root": str(root_real), "copied": copied,
                                               "refused": refused}, base)
    if folders:
        authorize_materials(case_id, sorted(folders, key=MATERIAL_FOLDERS.index), base)
    return {"copied": copied, "refused": refused, "source_root": str(root_real)}


# ------------------------------------------------------------------ results: one folder per run
def runs(case_id: str, base=None) -> list:
    folder = case_dir(case_id, base) / "results"
    return sorted(p.name for p in folder.glob("run-[0-9][0-9][0-9]") if p.is_dir()) if folder.exists() else []


def latest_run(case_id: str, base=None) -> str | None:
    found = runs(case_id, base)
    return found[-1] if found else None


def new_run(case_id: str, base=None) -> str:
    found = runs(case_id, base)
    name = f"run-{(int(found[-1][4:]) + 1) if found else 1:03d}"
    (case_dir(case_id, base) / "results" / name).mkdir(parents=True)
    return name


def run_dir(case_id: str, run: str, base=None) -> Path:
    if not re.fullmatch(r"run-\d{3}", run or ""):
        raise ValueError(f"bad run name: {run!r}")
    return case_dir(case_id, base) / "results" / run


def load_result(case_id: str, run: str | None = None, base=None) -> dict:
    """A run's result.json (latest run when `run` is None); {} if there is none."""
    run = run or latest_run(case_id, base)
    return read_json(run_dir(case_id, run, base) / "result.json", {}) if run else {}


def save_run(case_id: str, result: dict, note: str, base=None) -> str:
    """Save a finished analysis as the next results/run-NNN: result.json and process_map.json."""
    run = new_run(case_id, base)
    folder = run_dir(case_id, run, base)
    write_json(folder / "process_map.json", {**result.get("process_map", {}), "run": run, "saved": _now(), "run_note": note})
    write_json(folder / "result.json", result)
    update_case(case_id, base, latest_run=run)
    return run


def reset_case(case_id: str, base=None) -> None:
    """Delete a case folder (used for demo cases)."""
    shutil.rmtree(case_dir(case_id, base), ignore_errors=True)
