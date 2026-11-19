"""Deterministic checks on a page's raw HTML (standard library only).

These are facts read from the page source, not opinions. The website rating uses them
together with the LLM's content sub-ratings, and the chatbot check uses them on their own.
A text-only fetch cannot see visual design, and a chat widget that loads only after a user
action or on other pages can be missed, so every result is worded as "found / not found on
the pages read".
"""
import re

# vendor name -> substrings that appear in the page source when its chat widget is installed
CHAT_WIDGETS = {
    "Intercom": ["widget.intercom.io", "intercomsettings"],
    "Drift": ["js.driftt.com", "drift-frame"],
    "Tidio": ["code.tidio.co", "tidiochatcode"],
    "LiveChat": ["cdn.livechatinc.com", "__lc.license"],
    "HubSpot chat": ["js.hs-scripts.com", "hubspotconversations", "js.usemessages.com"],
    "Zendesk chat": ["static.zdassets.com", "zopim", "zendesk.com/embeddable"],
    "Crisp": ["client.crisp.chat", "$crisp"],
    "Tawk.to": ["embed.tawk.to"],
    "Freshchat": ["wchat.freshchat.com"],
    "Olark": ["static.olark.com", "olark.identify"],
    "Smartsupp": ["smartsuppchat", "smartsupp.com"],
    "Podium": ["connect.podium.com", "podium-webchat"],
    "Ada": ["static.ada.support", "adaembed"],
    "Botpress": ["cdn.botpress.cloud"],
    "Chatbase": ["chatbase.co"],
    "Voiceflow": ["cdn.voiceflow.com"],
    "Qualified": ["js.qualified.com"],
    "Gorgias": ["gorgias.chat"],
    "Facebook Messenger": ["xfbml.customerchat"],
}
CHAT_TEXT = re.compile(r"\b(live chat|chat with us|chat now|ask our (ai )?assistant|virtual assistant|chatbot)\b", re.I)
CTA_WORDS = re.compile(r"\b(get a quote|request a quote|contact us|book (a|an|your)|schedule|call us|get started|free estimate|request a (call|demo)|sign up|buy now|order now)\b", re.I)


SOCIAL_HOSTS = {"linkedin": ("linkedin.com",), "facebook": ("facebook.com", "fb.com"),
                "instagram": ("instagram.com",), "tiktok": ("tiktok.com",),
                "youtube": ("youtube.com", "youtu.be"), "x_twitter": ("twitter.com", "x.com")}


def social_links(html: str) -> dict:
    """{platform: [links found on this page]} for every platform in SOCIAL_HOSTS. A platform with an
    empty list was NOT FOUND ON THE PAGE READ; that is all it means (rule 3: never "does not exist")."""
    hrefs = re.findall(r"""href\s*=\s*["']([^"']+)["']""", html, flags=re.I)
    found = {name: [] for name in SOCIAL_HOSTS}
    for h in hrefs:
        host = re.sub(r"^https?://(www\.)?", "", h.strip().lower()).split("/")[0]
        for name, hosts in SOCIAL_HOSTS.items():
            if any(host == d or host.endswith("." + d) for d in hosts) and h not in found[name]:
                found[name].append(h)
    return found


def analyze_html(html: str, url: str = "") -> dict:
    """Return a dict of simple facts about the page source."""
    low = html.lower()
    vendors = sorted(v for v, needles in CHAT_WIDGETS.items() if any(n in low for n in needles))
    imgs = re.findall(r"<img\b[^>]*>", html, flags=re.I)
    missing_alt = sum(1 for tag in imgs if not re.search(r"\balt\s*=\s*[\"'][^\"']+[\"']", tag, flags=re.I))
    visible = re.sub(r"<(script|style)\b.*?</\1>", " ", html, flags=re.I | re.S)
    visible = re.sub(r"<[^>]+>", " ", visible)
    return {
        "https": url.lower().startswith("https://"),
        "chat_widgets": vendors,
        "chat_text_hint": bool(CHAT_TEXT.search(visible)),
        "mobile_viewport": bool(re.search(r"<meta[^>]+name=[\"']viewport[\"']", html, flags=re.I)),
        "phone_link": "tel:" in low,
        "email_link": "mailto:" in low,
        "form_count": len(re.findall(r"<form\b", low)),
        "h1_count": len(re.findall(r"<h1\b", low)),
        "images": len(imgs),
        "images_missing_alt": missing_alt,
        "cta_hits": len(CTA_WORDS.findall(visible)),
        "has_title": bool(re.search(r"<title[^>]*>\s*\S", html, flags=re.I)),
        "has_meta_description": bool(re.search(r"<meta[^>]+name=[\"']description[\"']", html, flags=re.I)),
        "social_links": social_links(html),
    }
