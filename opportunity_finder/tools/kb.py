"""Retriever over the curated knowledge base (default kb_sources/, sourced public-domain notes).

Layout: <kb>/<industry-folder>/<note>.md, each starting with `source:`, `url:` and
`industries:` header lines, then `---`, then text. `industries: *` marks general guidance.
Passages are paragraph-sized chunks with ids like "nist-mep-lean-methods#2".

Ranking is hybrid (Nov 17): vector similarity from ChromaDB with local nomic embeddings
(tools/vectorstore.py) plus BM25 keyword scores, merged by reciprocal rank fusion. When vectors
are not available (no LLM_EMBED_MODEL, Chroma missing, or the embedding server down) it falls
back to BM25 alone and says so in the retrieval info. KB_DIR=kb selects the old author-written
placeholder notes (the tests use them).
"""
import math
import os
import re
from pathlib import Path

from . import vectorstore

DEFAULT_KB_DIR = Path(__file__).resolve().parents[2] / "kb_sources"
_STOP = {"the", "and", "of", "for", "a", "an", "in", "to", "with", "inc", "llc", "co", "company",
         "companies", "business", "businesses", "industry", "service", "services", "regional", "small"}


def _tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in _STOP:
            continue
        out.append(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return out


def _read_doc(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8")
    if "\n---" not in raw:
        return None
    header, body = raw.split("\n---", 1)
    meta = {}
    for line in header.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    tags = [t.strip() for t in meta.get("industries", "").split(",") if t.strip()]
    return {"file": path.stem, "source": meta.get("source") or path.stem, "url": meta.get("url", ""),
            "general": tags == ["*"], "tag_tokens": set(_tokens(" ".join(tags))), "body": body.strip("- \n")}


def _chunks(doc: dict, max_chars: int = 900) -> list[dict]:
    """Group paragraphs into chunks of up to ~max_chars (a paragraph is never split)."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", doc["body"]) if p.strip()]
    merged, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) > max_chars:
            merged.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        merged.append(cur)
    return [{"id": f"{doc['file']}#{i + 1}", "text": t, "source": doc["source"], "url": doc["url"],
             "general": doc["general"], "tag_tokens": doc["tag_tokens"]} for i, t in enumerate(merged)]


def load_kb(kb_dir: str | Path | None = None) -> list[dict]:
    root = kb_root(kb_dir)
    chunks = []
    for path in sorted(root.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        doc = _read_doc(path)
        if doc:
            chunks.extend(_chunks(doc))
    return chunks


def _bm25(query: list[str], chunks: list[dict], k1: float = 1.5, b: float = 0.75) -> list[float]:
    docs = [_tokens(c["text"]) for c in chunks]
    if not docs:
        return []
    avg = sum(len(d) for d in docs) / len(docs) or 1
    n = len(docs)
    scores = []
    for d in docs:
        s = 0.0
        for term in set(query):
            tf = d.count(term)
            if not tf:
                continue
            df = sum(1 for x in docs if term in x)
            idf = math.log(1 + (n - df + 0.5) / (df + 0.5))
            s += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(d) / avg))
        scores.append(s)
    return scores


def kb_root(kb_dir: str | Path | None = None) -> Path:
    vectorstore._load_env()
    return Path(kb_dir or os.getenv("KB_DIR") or DEFAULT_KB_DIR)


def retrieve_with_info(industry: str, k_industry: int = 4, k_general: int = 2,
                       kb_dir: str | Path | None = None, query_text: str = "",
                       embedder=None) -> tuple[list[dict], str, dict]:
    """Return (chunks, note, info). Industry-specific chunks come first, then general guidance.
    `note` is non-empty when the KB has nothing specific for this industry. `info` says how the
    ranking was done: {"mode": "hybrid"|"keyword", "reason", "embed_model", "index_rebuilt",
    "query", "embedding_calls"}."""
    root = kb_root(kb_dir)
    chunks = load_kb(root)
    want = set(_tokens(industry))
    specific = [c for c in chunks if not c["general"] and c["tag_tokens"] & want]
    general = [c for c in chunks if c["general"]]
    query = f"{industry} AI automation best practices process efficiency {query_text}".strip()
    qtok = _tokens(query)
    info = {"mode": "keyword", "reason": "", "embed_model": "", "index_rebuilt": False,
            "query": query[:300], "embedding_calls": []}

    vec_rank: list[str] | None = None
    emb = embedder
    if chunks:
        try:
            emb = emb or vectorstore.Embedder()
            info["embed_model"] = emb.model
            col, info["index_rebuilt"] = vectorstore.open_store(
                root / ".chroma", "industry_kb",
                [{"id": c["id"], "text": c["text"], "source": c["source"], "general": c["general"]} for c in chunks], emb)
            vec_rank = vectorstore.vector_ranking(col, emb.query(query), len(chunks))
            info["mode"] = "hybrid"
            info["embedding_calls"] = list(emb.calls)
        except vectorstore.VectorsUnavailable as exc:
            info["reason"] = str(exc)
            info["embedding_calls"] = list(getattr(emb, "calls", []) or [])

    def top(pool, k):
        scores = _bm25(qtok, pool)
        bm = [pool[i]["id"] for _, i in sorted(zip(scores, range(len(pool))), key=lambda t: (-t[0], t[1]))]
        if vec_rank is None:
            order = bm
        else:
            ids = {c["id"] for c in pool}
            order = vectorstore.rrf([i for i in vec_rank if i in ids], bm)
        by_id = {c["id"]: c for c in pool}
        return [by_id[i] for i in order[:k]]

    hits = top(specific, k_industry) + top(general, k_general)
    note = "" if specific else f"no curated sources for '{industry}'; using general guidance only"
    return hits, note, info


def retrieve(industry: str, k_industry: int = 4, k_general: int = 2,
             kb_dir: str | Path | None = None, query_text: str = "", embedder=None) -> tuple[list[dict], str]:
    """Return (chunks, note); see retrieve_with_info for the ranking details."""
    hits, note, _ = retrieve_with_info(industry, k_industry, k_general, kb_dir, query_text, embedder)
    return hits, note


def get_passages(ids, kb_dir: str | Path | None = None) -> dict:
    """{passage id: {text, source, url}} for the ids that exist. The Verifier uses this to check
    a claim against the passage it cites (looked up by id, so it works with or without vectors)."""
    want = set(ids)
    return {c["id"]: {"text": c["text"], "source": c["source"], "url": c["url"]}
            for c in load_kb(kb_dir) if c["id"] in want}
