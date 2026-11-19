"""Tiny retriever over the curated knowledge base in kb/ (standard library only).

Layout: kb/<industry-folder>/<note>.md, each starting with `source:`, `url:` and
`industries:` header lines, then `---`, then text. `industries: *` marks general
guidance. Ranking is BM25 over paragraph-sized chunks. To upgrade later, swap `_bm25`
for embeddings (LM Studio can serve nomic-embed-text) without changing callers.
"""
import math
import os
import re
from pathlib import Path

DEFAULT_KB_DIR = Path(__file__).resolve().parents[2] / "kb"
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
    root = Path(kb_dir or os.getenv("KB_DIR") or DEFAULT_KB_DIR)
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


def retrieve(industry: str, k_industry: int = 4, k_general: int = 2,
             kb_dir: str | Path | None = None) -> tuple[list[dict], str]:
    """Return (chunks, note). Industry-specific chunks come first, then general guidance.
    `note` is non-empty when the KB has nothing specific for this industry."""
    chunks = load_kb(kb_dir)
    want = set(_tokens(industry))
    specific = [c for c in chunks if not c["general"] and c["tag_tokens"] & want]
    general = [c for c in chunks if c["general"]]
    query = _tokens(f"{industry} AI automation best practices process efficiency")

    def top(pool, k):
        scores = _bm25(query, pool)
        ranked = sorted(zip(scores, range(len(pool))), key=lambda t: (-t[0], t[1]))
        return [pool[i] for _, i in ranked[:k]]

    hits = top(specific, k_industry) + top(general, k_general)
    note = "" if specific else f"no curated sources for '{industry}'; using general guidance only"
    return hits, note


def get_passages(ids, kb_dir: str | Path | None = None) -> dict:
    """{passage id: {text, source, url}} for the ids that exist. The Verifier uses this to check
    a claim against the passage it cites. RAG seam: swap this for a vector-store lookup later."""
    want = set(ids)
    return {c["id"]: {"text": c["text"], "source": c["source"], "url": c["url"]}
            for c in load_kb(kb_dir) if c["id"] in want}
