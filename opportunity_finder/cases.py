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
    "confirmed": "Profile confirmed. Waiting for process documents (optional), then run the analysis.",
    "analyzed": "Recommendation ready.",
}
TEXT_SUFFIXES = {".txt", ".md", ".csv", ".json"}


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


def load_documents(case_id: str, base=None, max_chars: int = 6000) -> list:
    """Readable documents as [{name, text}], with the total text capped for a small model."""
    folder = case_dir(case_id, base) / "documents"
    docs, used = [], 0
    for p in sorted(folder.glob("*")) if folder.exists() else []:
        if p.suffix.lower() not in TEXT_SUFFIXES or used >= max_chars:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")[: max_chars - used]
        used += len(text)
        docs.append({"name": p.name, "text": text})
    return docs


def list_document_files(case_id: str, base=None) -> list:
    folder = case_dir(case_id, base) / "documents"
    return [p.name for p in sorted(folder.glob("*"))] if folder.exists() else []


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
