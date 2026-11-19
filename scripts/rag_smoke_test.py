"""Check the industry RAG against the real embedding model (LM Studio with nomic-embed-text loaded).

    python scripts/rag_smoke_test.py ["industry"] ["what the company does"]

Prints the retrieval mode (hybrid = vectors + keywords, keyword = fallback, with the reason),
whether the Chroma index was built, and the passages found with their sources."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from opportunity_finder.tools import kb  # noqa: E402

industry = sys.argv[1] if len(sys.argv) > 1 else "trailer manufacturing"
about = sys.argv[2] if len(sys.argv) > 2 else "family-owned manufacturer selling through independent dealers"
hits, note, info = kb.retrieve_with_info(industry, query_text=about)
print(f"knowledge base: {kb.kb_root()}")
print(f"mode: {info['mode']}" + (f"  (reason: {info['reason']})" if info["reason"] else ""))
print(f"embedding model: {info['embed_model'] or '-'}   index built this time: {info['index_rebuilt']}")
for c in info["embedding_calls"]:
    print(f"  embedding call: {c['texts']} text(s), {c['seconds']} s" + (f", ERROR {c['error']}" if c["error"] else ""))
if note:
    print(f"note: {note}")
for h in hits:
    print(f"- [{h['id']}] {h['source']}\n    {h['text'][:110].replace(chr(10), ' ')}...")
