"""Vector search: ChromaDB holding local embeddings (nomic-embed-text served by LM Studio).

Used by tools/kb.py for hybrid retrieval (vector ranking plus BM25 keyword ranking, merged by
reciprocal rank fusion). Everything stays on this computer:
- embeddings come from the OpenAI-compatible /v1/embeddings endpoint of LM Studio; a hosted
  endpoint is refused unless "embed" is listed in LLM_ALLOW_HOSTED (same rule as the chat models);
- Chroma's anonymous telemetry is switched off, and Chroma's own default embedding model is never
  used (it would be downloaded): we always pass our own vectors.

Settings (.env): LLM_EMBED_MODEL (empty = no vectors, keyword search only), LLM_EMBED_BASE_URL
and LLM_EMBED_API_KEY (default to LLM_BASE_URL / LLM_API_KEY). nomic-embed-text expects task
prefixes, added here: "search_document: " on passages, "search_query: " on queries.

A store is one Chroma folder (PersistentClient) with one collection. It is rebuilt only when the
passages or the embedding model change (a fingerprint is kept in the collection metadata), so a
normal run embeds just the query.
"""
import hashlib
import os
import time
from pathlib import Path

from ..llm import is_local

DOC_PREFIX, QUERY_PREFIX = "search_document: ", "search_query: "
RRF_K = 60   # reciprocal rank fusion constant (the usual value from the literature)


class VectorsUnavailable(RuntimeError):
    """Vector search cannot run (not configured, Chroma missing, or the embedding server failed).
    Callers fall back to keyword search and say so."""


def _load_env():
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


def embed_settings() -> dict:
    _load_env()
    base = os.getenv("LLM_EMBED_BASE_URL") or os.getenv("LLM_BASE_URL") or "http://localhost:1234/v1"
    allow = {a.strip().lower() for a in os.getenv("LLM_ALLOW_HOSTED", "").split(",") if a.strip()}
    return {"model": os.getenv("LLM_EMBED_MODEL", "").strip(), "base_url": base,
            "api_key": os.getenv("LLM_EMBED_API_KEY") or os.getenv("LLM_API_KEY") or "lm-studio",
            "hosted_allowed": is_local(base) or "all" in allow or "embed" in allow}


class Embedder:
    """Wraps the embedding endpoint: adds the nomic prefixes and keeps a small call log."""

    def __init__(self, settings: dict | None = None, client=None):
        self.settings = settings or embed_settings()
        if not self.settings["model"]:
            raise VectorsUnavailable("no embedding model configured (LLM_EMBED_MODEL is empty)")
        if not self.settings["hosted_allowed"]:
            raise VectorsUnavailable(f"embedding server {self.settings['base_url']} is not local; "
                                     "add 'embed' to LLM_ALLOW_HOSTED to allow it")
        if client is None:
            from langchain_openai import OpenAIEmbeddings
            client = OpenAIEmbeddings(model=self.settings["model"], base_url=self.settings["base_url"],
                                      api_key=self.settings["api_key"], check_embedding_ctx_length=False,
                                      timeout=60, max_retries=1)
        self.client, self.calls = client, []

    @property
    def model(self) -> str:
        return self.settings["model"]

    def _logged(self, fn, texts):
        started = time.perf_counter()
        try:
            out = fn(texts)
        except Exception as exc:
            self.calls.append({"agent": "embedding", "model": self.model, "texts": len(texts),
                               "seconds": round(time.perf_counter() - started, 3), "error": repr(exc)[:300]})
            raise VectorsUnavailable(f"embedding call failed: {exc}"[:300]) from exc
        self.calls.append({"agent": "embedding", "model": self.model, "texts": len(texts),
                           "seconds": round(time.perf_counter() - started, 3), "error": None})
        return out

    def documents(self, texts: list[str]) -> list[list[float]]:
        return self._logged(self.client.embed_documents, [DOC_PREFIX + t for t in texts])

    def query(self, text: str) -> list[float]:
        return self._logged(lambda ts: [self.client.embed_query(ts[0])], [QUERY_PREFIX + text])[0]


def fingerprint(passages: list[dict], model: str) -> str:
    h = hashlib.sha256(model.encode())
    for p in passages:
        h.update(p["id"].encode())
        h.update(p["text"].encode())
    return h.hexdigest()[:16]


def _client(path: Path):
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError as exc:
        raise VectorsUnavailable("chromadb is not installed (pip install -r requirements.txt)") from exc
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(path), settings=Settings(anonymized_telemetry=False))


def open_store(path: Path, name: str, passages: list[dict], embedder: Embedder):
    """The Chroma collection for these passages, built (or rebuilt) if missing or out of date.
    Returns (collection, rebuilt: bool)."""
    client = _client(Path(path))
    fp = fingerprint(passages, embedder.model)
    try:
        col = client.get_collection(name, embedding_function=None)
        if (col.metadata or {}).get("fingerprint") == fp and col.count() == len(passages):
            return col, False
        client.delete_collection(name)
    except Exception:
        pass  # no collection yet
    col = client.create_collection(name, embedding_function=None, metadata={
        "hnsw:space": "cosine", "fingerprint": fp, "embed_model": embedder.model})
    if passages:
        vectors = embedder.documents([p["text"] for p in passages])
        col.add(ids=[p["id"] for p in passages], embeddings=vectors, documents=[p["text"] for p in passages],
                metadatas=[{k: v for k, v in p.items() if isinstance(v, (str, int, float, bool)) and k not in ("id", "text")}
                           or {"_": ""} for p in passages])
    return col, True


def vector_ranking(col, query_vector: list[float], n: int) -> list[str]:
    """Passage ids, nearest first."""
    if n <= 0 or col.count() == 0:
        return []
    res = col.query(query_embeddings=[query_vector], n_results=min(n, col.count()))
    return list(res["ids"][0])


def rrf(*rankings: list[str], k: int = RRF_K) -> list[str]:
    """Reciprocal rank fusion: each list adds 1 / (k + rank) for every id it ranks. Ties keep the
    order of the first ranking."""
    score: dict = {}
    first: dict = {}
    for ranking in rankings:
        for rank, pid in enumerate(ranking, 1):
            score[pid] = score.get(pid, 0.0) + 1.0 / (k + rank)
            first.setdefault(pid, len(first))
    return sorted(score, key=lambda pid: (-score[pid], first[pid]))
