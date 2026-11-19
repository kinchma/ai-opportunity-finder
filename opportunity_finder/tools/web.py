"""Fetch a web page and reduce it to a small block of text (standard library only).

Small local models do badly with long inputs, so we keep just the title, the meta
description and the first few thousand characters of visible text.
"""
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

from .site_signals import analyze_html

USER_AGENT = "Mozilla/5.0 (compatible; OpportunityFinder/0.1; course project)"
_SKIP = {"script", "style", "noscript", "svg", "template", "iframe"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.description = ""
        self._in_title = False
        self._skip_depth = 0
        self._chunks: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag in _SKIP:
            self._skip_depth += 1
        elif tag == "meta":
            key = (a.get("name") or a.get("property") or "").lower()
            if key in ("description", "og:description") and not self.description:
                self.description = (a.get("content") or "").strip()

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in _SKIP and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip_depth and data.strip():
            self._chunks.append(data.strip())


def extract_text(html: str, max_chars: int = 3000) -> dict:
    """Return {title, description, text} from raw HTML."""
    p = _TextExtractor()
    p.feed(html)
    text = re.sub(r"\s+", " ", " ".join(p._chunks)).strip()
    return {"title": re.sub(r"\s+", " ", p.title).strip(),
            "description": re.sub(r"\s+", " ", p.description).strip(),
            "text": text[:max_chars]}


def normalize_url(url: str) -> str:
    url = url.strip()
    return url if re.match(r"^https?://", url, re.I) else "https://" + url


def fetch_site_text(url: str, max_chars: int = 3000, timeout: float = 15) -> dict:
    """Fetch a page. Never raises: on failure returns {"error": "..."} with empty fields."""
    url = normalize_url(url)
    out = {"url": url, "title": "", "description": "", "text": "", "error": None, "signals": {}}
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ctype = resp.headers.get("Content-Type", "")
            if "html" not in ctype.lower():
                out["error"] = f"not an HTML page (Content-Type: {ctype or 'unknown'})"
                return out
            raw = resp.read(500_000)
            charset = resp.headers.get_content_charset() or "utf-8"
        html = raw.decode(charset, errors="replace")
        out.update(extract_text(html, max_chars))
        out["signals"] = analyze_html(html, url)
    except urllib.error.HTTPError as exc:
        out["error"] = f"HTTP {exc.code} from the site"
    except Exception as exc:  # DNS failure, timeout, bad SSL, ...
        out["error"] = f"could not fetch the page: {exc}"[:200]
    return out
