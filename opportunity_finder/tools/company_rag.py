"""Company RAG: one ChromaDB store per customer, built from that customer's authorized material.

The store lives in cases/<id>/index/ (git-ignored) next to the material it was built from, so
deleting a case deletes its index, and a search for one company can only open that company's
folder: there is no shared collection, so no filter can be forgotten. Passages are the citable
chunks from cases.document_chunks (ids like "doc:interviews/08_quoting_interview.md#3"), with
their source_type kept as metadata so a search can ask for interviews only.

Ranking is the same hybrid as the industry store: nomic vectors from LM Studio plus BM25, merged
by reciprocal rank fusion; BM25 alone when vectors are unavailable. Embeddings are built when an
analysis starts (or with `scripts/synthetic_case.py index <case>`) and reused until a file, the set
of authorized folders or the embedding model changes. COMPANY_RETRIEVAL=off turns all of this off
and brings back the old fixed bundle (each file's first 700 characters), for comparison runs.
"""
import json
import os
from datetime import datetime
from pathlib import Path

from . import kb, vectorstore

COLLECTION = "company_docs"
INFO_FILE = "index_info.json"
# What the Process Mapper searches for when a company has no process documents to anchor on.
COMMON_PROCESSES = ["order intake and quoting", "scheduling and production planning",
                    "purchasing, receiving and inventory", "invoicing, billing and month-end close",
                    "payroll, time cards and onboarding", "customer service, status questions and warranty",
                    "marketing and sales follow-up"]


def enabled() -> bool:
    vectorstore._load_env()
    return os.getenv("COMPANY_RETRIEVAL", "on").strip().lower() not in ("off", "0", "false", "no")


def _passages(chunks: list) -> list:
    return [{"id": c["id"], "text": c["text"], "source_type": c["source_type"], "name": c["name"],
             "heading": c.get("heading") or ""} for c in chunks]


def build_index(index_dir, chunks: list, embedder=None) -> dict:
    """Open (or build, or rebuild) the company store. Returns info: {mode, reason, passages,
    embed_model, index_rebuilt, fingerprint, built}. Never raises: without vectors the mode is
    "keyword" and searches use BM25 over the same passages."""
    index_dir = Path(index_dir)
    info = {"mode": "keyword", "reason": "", "passages": len(chunks), "embed_model": "",
            "index_rebuilt": False, "fingerprint": "", "embedding_calls": []}
    emb = embedder
    try:
        emb = emb or vectorstore.Embedder()
        info["embed_model"] = emb.model
        info["fingerprint"] = vectorstore.fingerprint(_passages(chunks), emb.model)
        _, info["index_rebuilt"] = vectorstore.open_store(index_dir, COLLECTION, _passages(chunks), emb)
        info["mode"] = "hybrid"
    except vectorstore.VectorsUnavailable as exc:
        info["reason"] = str(exc)
    info["embedding_calls"] = list(getattr(emb, "calls", []) or [])
    if info["mode"] == "hybrid":
        saved = {k: v for k, v in info.items() if k != "embedding_calls"}
        saved["built" if info["index_rebuilt"] else "checked"] = datetime.now().isoformat(timespec="seconds")
        old = read_info(index_dir)
        if not info["index_rebuilt"] and old.get("built"):
            saved["built"] = old["built"]
        (index_dir / INFO_FILE).write_text(json.dumps(saved, indent=2), encoding="utf-8")
    return info


def read_info(index_dir) -> dict:
    try:
        return json.loads((Path(index_dir) / INFO_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def index_status(index_dir, chunks: list) -> dict:
    """For the UI and `status`: is there an index, and does it match the current material?
    (Up to date means same passages and same embedding model; checked without calling a model.)"""
    info = read_info(index_dir)
    if not info:
        return {"exists": False, "up_to_date": False, "passages": 0, "embed_model": "", "built": ""}
    current = vectorstore.fingerprint(_passages(chunks), info.get("embed_model", ""))
    return {"exists": True, "up_to_date": current == info.get("fingerprint"), "passages": info.get("passages", 0),
            "embed_model": info.get("embed_model", ""), "built": info.get("built", "")}


class Searcher:
    """Searches one company's passages. Built once per analysis; the Process Mapper calls search()
    once per process. Vector search when the store is available, BM25 otherwise."""

    def __init__(self, index_dir, chunks: list, mode: str = "hybrid", embedder=None):
        self.chunks = chunks
        self.by_id = {c["id"]: c for c in chunks}
        self.mode, self.reason, self.col, self.emb = "keyword", "", None, None
        if mode == "hybrid":
            try:
                self.emb = embedder or vectorstore.Embedder()
                self.col, _ = vectorstore.open_store(Path(index_dir), COLLECTION, _passages(chunks), self.emb)
                self.mode = "hybrid"
            except vectorstore.VectorsUnavailable as exc:
                self.reason = str(exc)

    @property
    def embedding_calls(self) -> list:
        return list(getattr(self.emb, "calls", []) or [])

    def search(self, query: str, k: int = 4, source_types=None, exclude=()) -> list:
        """Top-k chunks for `query`, restricted to `source_types` (None = all), skipping ids in
        `exclude`. Returns chunk dicts, best first."""
        pool = [c for c in self.chunks if (source_types is None or c["source_type"] in source_types)
                and c["id"] not in exclude]
        if not pool or k <= 0:
            return []
        scores = kb._bm25(kb._tokens(query), pool)
        bm = [pool[i]["id"] for s, i in sorted(zip(scores, range(len(pool))), key=lambda t: (-t[0], t[1])) if s > 0]
        order = bm
        if self.mode == "hybrid":
            try:
                where = {"source_type": {"$in": list(source_types)}} if source_types else None
                n = min(len(self.chunks), max(4 * k, 20))
                res = self.col.query(query_embeddings=[self.emb.query(query)], n_results=n,
                                     **({"where": where} if where else {}))
                allowed = {c["id"] for c in pool}
                vec = [i for i in res["ids"][0] if i in allowed]
                order = vectorstore.rrf(vec, bm)
            except vectorstore.VectorsUnavailable as exc:
                self.mode, self.reason = "keyword", str(exc)
        return [self.by_id[i] for i in order[:k]]
