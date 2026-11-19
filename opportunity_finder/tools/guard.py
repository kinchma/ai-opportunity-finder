"""Simple prompt-injection scan for text we did not write (web pages, pasted text, documents).

This is a cheap first line of defense, not a guarantee: a fixed list of patterns that catches
the obvious "ignore your instructions" style of attack. Matches are cut out of the text before
a model sees it, and every match is reported as a flag so the owner and the run log show it.
The prompts still tell the model that page text is data, not instructions (rule 6).
"""
import re

REMOVED = "[removed: looked like an instruction to the AI]"
_PATTERNS = [
    r"(ignore|disregard|forget|override)\s+(all\s+|any\s+|the\s+|your\s+)?(previous|prior|above|earlier|preceding|system)\s+(instructions?|prompts?|rules|messages?|context)",
    r"(ignore|disregard|forget)\s+(everything|anything|all)\s+(above|before|you\s+were\s+told)",
    r"you\s+are\s+now\s+(a|an|the|in)\b[^.\n]{0,60}",
    r"(new|updated|additional)\s+(system\s+)?instructions?\s*:",
    r"(reveal|print|show|repeat|output)\s+(me\s+)?(your|the)\s+(system\s+)?(prompt|instructions)",
    r"do\s+not\s+(tell|inform|alert|mention\s+(this\s+)?to)\s+the\s+(user|owner|human|reviewer)",
    r"</?\s*(system|assistant|instructions?)\s*>",
    r"\[/?INST\]|<\|im_(start|end)\|>",
    r"(attention|note\s+to|message\s+for)\s+(ai|llm|language\s+model|assistant|chatbot)s?\b[^.\n]{0,80}",
    r"(rate|score|rank|give)\s+(this|our|the)\s+(company|business|site|website|page)\s+(a\s+|as\s+)?(10|ten|perfect|the\s+highest|top)",
    r"respond\s+only\s+with\b[^.\n]{0,60}",
]
_RX = [re.compile(p, re.I) for p in _PATTERNS]


def scan(text: str) -> list:
    """Every suspicious match in the text: [{"match": the matched words}]."""
    hits = []
    for rx in _RX:
        hits.extend({"match": m.group(0)[:120]} for m in rx.finditer(text or ""))
    return hits


def scrub(text: str, where: str) -> tuple[str, list]:
    """Cut suspicious matches out of the text. Returns (clean text, flags for the run state)."""
    hits = scan(text)
    clean = text or ""
    for rx in _RX:
        clean = rx.sub(REMOVED, clean)
    return clean, [{"type": "injection", "where": where, "detail": h["match"]} for h in hits]
