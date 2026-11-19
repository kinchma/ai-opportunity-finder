"""Case folders: one isolated folder per customer, so work can stop and resume weeks later.

    cases/<case-id>/
        case.json            id, name, stage, status, dates, company_input
        discovery.json       Discovery output (profile, site text, website check, call log)
        profile.json         profile as confirmed by the owner
        decisions.json       every owner correction or decision, with a date
        documents/           files the owner provided (text files are read by the Process Mapper)
        process_map.json     latest process map; process_map.v1.json, v2.json ... keep every version
        result.json          full pipeline result (recommendation, ranking, roadmaps, logs)
        runs/                one call-log file per run

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
    "confirmed": "Profile confirmed. Waiting for process documents (optional), then run the analysis.",
    "analyzed": "Recommendation ready.",
}
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json"}
# Folders or files that must never be copied into a case's documents/, whatever the owner selects:
# evaluation answer keys and generation prompts of a synthetic test case are not company records.
DENY_PATTERNS = ("evaluator", "do_not_share", "do-not-share", "answer_key", "answer-key",
                 "expectations", "case_manifest", "creation_prompt", "desktop_prompt", "grading")
# Subfolder names (under documents/) that tell the pipeline what kind of record a file is.
SOURCE_TYPES = {"interviews": "sme_interview", "interview": "sme_interview", "personas": "sme_interview",
                "processes": "process_document", "process": "process_document",
                "data": "data_sample", "research": "external_research"}


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


def create_case(name: str, company_input: dict, base=None) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "case"
    case_id = f"{slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    write_json(case_dir(case_id, base) / "case.json", {
        "id": case_id, "name": name, "stage": "new", "status": STATUS_TEXT["new"],
        "created": _now(), "updated": _now(), "company_input": company_input})
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
    items = load(case_id, "decisions.json", [], base)
    items.append({"when": _now(), "kind": kind, "detail": detail})
    save(case_id, "decisions.json", items, base)


def add_document(case_id: str, filename: str, data: bytes, base=None) -> dict:
    """Store an owner document. Only plain-text types are read by the pipeline for now."""
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(filename).name) or "document"
    folder = case_dir(case_id, base) / "documents"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / safe).write_bytes(data)
    readable = Path(safe).suffix.lower() in TEXT_SUFFIXES
    add_decision(case_id, "document_added", {"file": safe, "readable": readable}, base)
    return {"file": safe, "readable": readable}


def _document_paths(case_id: str, base=None) -> list:
    """Every file under documents/ (subfolders included), sorted, symlinks skipped."""
    folder = case_dir(case_id, base) / "documents"
    if not folder.exists():
        return []
    return sorted(p for p in folder.rglob("*") if p.is_file() and not p.is_symlink())


def source_type_of(relpath: str) -> str:
    """owner_document unless the file sits in a subfolder that names a record type."""
    parts = Path(relpath).parts[:-1]
    for part in parts:
        if part.lower() in SOURCE_TYPES:
            return SOURCE_TYPES[part.lower()]
    return "owner_document"


def load_documents(case_id: str, base=None, max_chars: int = 6000, per_file: int | None = None) -> list:
    """Readable documents as [{name, text, source_type}], total text capped for a small model.
    `per_file` caps each file so one long document cannot crowd out the others."""
    folder = case_dir(case_id, base) / "documents"
    docs, used = [], 0
    for p in _document_paths(case_id, base):
        if p.suffix.lower() not in TEXT_SUFFIXES or used >= max_chars:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        text = text[: min(max_chars - used, per_file or max_chars)]
        used += len(text)
        rel = p.relative_to(folder).as_posix()
        docs.append({"name": rel, "text": text, "source_type": source_type_of(rel)})
    return docs


def document_chunks(case_id: str, base=None, max_chars: int = 900) -> list:
    """Readable documents split into citable chunks: {id, name, source_type, heading, text}.
    Markdown is split at headings, then paragraphs are grouped up to ~max_chars (a paragraph is
    never split). CSV files become one chunk of header plus the first rows. Ids look like
    "doc:processes/08_quoting.md#3" so a citation says exactly which file and section it means."""
    folder = case_dir(case_id, base) / "documents"
    chunks = []
    for p in _document_paths(case_id, base):
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = p.relative_to(folder).as_posix()
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


def list_document_files(case_id: str, base=None) -> list:
    folder = case_dir(case_id, base) / "documents"
    return [p.relative_to(folder).as_posix() for p in _document_paths(case_id, base)]


def _denied(relpath: Path) -> bool:
    low = "/".join(relpath.parts).lower()
    return any(pat in low for pat in DENY_PATTERNS) or any(part.startswith(".") for part in relpath.parts)


def share_materials(case_id: str, source_root, include=None, base=None) -> dict:
    """Copy owner-authorized files into cases/<id>/documents/, keeping their subfolders.

    This is the pipeline's only route to company material: agents read documents/ and nothing
    else, so what is not copied here cannot be seen. The copy enforces a boundary rather than
    trusting folder names: the real path of every file must stay inside `source_root`, symlinks
    are refused, hidden files are refused, and anything whose path matches DENY_PATTERNS
    (evaluator material, answer keys, generation prompts) is refused even if listed. `include`
    is a list of relative paths or folders inside source_root; None means the whole root.
    Returns {copied: [...], refused: [{path, reason}], source_root}. Everything is logged in
    decisions.json as the owner's sharing decision."""
    root = Path(source_root).expanduser()
    try:
        root_real = root.resolve(strict=True)
    except OSError:
        raise FileNotFoundError(f"materials folder not found: {source_root}")
    if root.is_symlink() or not root_real.is_dir():
        raise ValueError("materials folder must be a real directory, not a symbolic link")
    if _denied(Path(root_real.name)):
        raise ValueError(f"refusing to share '{root_real.name}': it is evaluation or generation material, not company records")
    dest = case_dir(case_id, base) / "documents"
    wanted = [root / i for i in (include or ["."])]
    copied, refused, seen = [], [], set()
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
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(real, target)
            copied.append(key)
    add_decision(case_id, "materials_shared", {"source_root": str(root_real), "copied": copied,
                                               "refused": refused}, base)
    update_case(case_id, base, materials_authorized=bool(copied) or load_case(case_id, base).get("materials_authorized", False))
    return {"copied": copied, "refused": refused, "source_root": str(root_real)}


def save_process_map(case_id: str, pmap: dict, note: str, base=None) -> int:
    """Keep every version: process_map.vN.json, plus process_map.json as the latest."""
    folder = case_dir(case_id, base)
    n = len(list(folder.glob("process_map.v*.json"))) + 1
    entry = {**pmap, "version": n, "saved": _now(), "version_note": note}
    write_json(folder / f"process_map.v{n}.json", entry)
    write_json(folder / "process_map.json", entry)
    return n


def reset_case(case_id: str, base=None) -> None:
    """Delete a case folder (used for demo cases)."""
    shutil.rmtree(case_dir(case_id, base), ignore_errors=True)
