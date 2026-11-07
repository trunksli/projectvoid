"""Things you can actually watch, read or hear in the lounge, from places that make them publicly available.

Sources (all free, no keys, all rights-checked):

- **Internet Archive**: public-domain films, classic TV episodes, cartoons and Prelinger short films. Only
  items whose uploader marked them public domain (``licenseurl`` contains "publicdomain"). Played with the
  Archive's own embed player.
- **Project Gutenberg** (via Gutendex): public-domain books. We show an opening excerpt and link the full text.
- **PoetryDB**: public-domain poems, shown whole (short ones only).
- Feeds already in the scout: Vimeo staff picks play in Vimeo's do-not-track player; podcasts play
  from the publisher's own audio host.

A ``media`` dict says how to play a find. The browser never gets a raw third-party URL for an iframe:
embeds are rebuilt here from validated ids (``player()``).
"""

from __future__ import annotations

import random
import re
from datetime import datetime
from urllib.parse import quote

import httpx

PUBLIC_DOMAIN_RIGHTS = {
    "link": True,
    "read_metadata": True,
    "index_metadata": True,
    "embed_or_play": True,
    "share_generated_commentary": True,
}

# Not grim, but not the lounge either: exploitation-era titles that dominate "most downloaded".
NOT_COZY = re.compile(r"\b(sex\w*|nud\w+|naked|adult|grindhouse|xxx|erotic\w*|exploitation|reefer|marihuana|marijuana|madness|cocaine|drug addict\w*|strip\w*|lust)\b", re.I)

_ARCHIVE_ID = re.compile(r"^[A-Za-z0-9._-]{1,100}$")
_VIMEO = re.compile(r"vimeo\.com/(?:video/)?(\d{4,12})")
_TAGS = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


def _plain(text) -> str:
    if isinstance(text, list):
        text = " ".join(map(str, text))
    return _WS.sub(" ", _TAGS.sub(" ", str(text or ""))).strip()


def _sentences(text: str, n: int = 2, limit: int = 320) -> str:
    out = " ".join(re.split(r"(?<=[.!?])\s+", text.strip())[:n])
    return out if len(out) <= limit else out[: limit - 1].rsplit(" ", 1)[0] + "…"


def _https(url: str | None) -> str | None:
    return url if url and url.startswith("https://") else None


def media_for_link(url: str, audio_url: str | None = None) -> dict | None:
    """Media for an item from a feed: a Vimeo film, or a podcast episode's audio."""
    if m := _VIMEO.search(url):
        return {"type": "embed", "provider": "vimeo", "id": m.group(1)}
    if audio := _https(audio_url):
        return {"type": "audio", "src": audio}
    return None


def player(media: dict | None) -> dict | None:
    """What the browser gets: a validated, rebuilt player description. Never a raw URL from a source."""
    if not media:
        return None
    t = media.get("type")
    if t == "embed" and media.get("provider") == "archive" and _ARCHIVE_ID.match(str(media.get("id", ""))):
        return {"type": "iframe", "src": f"https://archive.org/embed/{media['id']}", "label": "Internet Archive player"}
    if t == "embed" and media.get("provider") == "vimeo" and str(media.get("id", "")).isdigit():
        return {"type": "iframe", "src": f"https://player.vimeo.com/video/{media['id']}?dnt=1", "label": "Vimeo player"}
    if t == "audio" and _https(media.get("src")):
        return {"type": "audio", "src": media["src"]}
    if t == "text" and media.get("text"):
        return {"type": "text", "form": media.get("form", "prose"), "text": str(media["text"])[:6000],
                "by": media.get("by"), "more_url": _https(media.get("more_url"))}
    return None


def teaser(kind: str, summary: str, media: dict | None) -> str:
    """The mini preview: a taste, not the summary. Opening lines for words, a line of description otherwise."""
    if media and media.get("type") == "text":
        lines = [ln.strip() for ln in str(media.get("text", "")).splitlines() if ln.strip()]
        if media.get("form") == "poem":
            return " / ".join(lines[:2])[:160]
        return _sentences(" ".join(lines), 1, 160)
    return _sentences(summary, 1, 140)


# ---------------------------------------------------------------------------
# Sources. Each is a callable (client, now) -> list[FeedItem], at most a few items per run.
# ---------------------------------------------------------------------------


def _feed_item(**kw):
    from .scout import FeedItem  # local import: scout imports this module

    return FeedItem(**kw)


ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"

ARCHIVE_COLLECTIONS = {
    # collection: (kind, how many to take per run)
    "feature_films": ("film", 3),
    "classic_tv": ("tv", 3),
    "classic_cartoons": ("cartoon", 2),
    "prelinger": ("short film", 2),
}


CURATED_PD = {"prelinger"}  # collections that are public domain as a whole, not by uploader say-so
LATEST_PD_YEAR = 1977  # US works after 1977 are essentially never public domain


def plausibly_public_domain(collection: str, doc: dict) -> bool:
    """Uploaders' public-domain marks are claims, not facts: a 2011 feature film marked PD is not. Need an old year."""
    if collection in CURATED_PD:
        return True
    m = re.search(r"\d{4}", str(doc.get("year") or ""))
    return bool(m) and 1880 <= int(m.group()) <= LATEST_PD_YEAR


def archive_source(collection: str, kind: str, take: int):
    def fetch(client: httpx.Client, now: datetime) -> list:
        resp = client.get(ARCHIVE_SEARCH, params={
            "q": f"collection:{collection} AND mediatype:movies AND licenseurl:*publicdomain*",
            "fl[]": ["identifier", "title", "description", "year", "downloads", "creator", "runtime"],
            "sort[]": "downloads desc", "rows": 150, "output": "json",  # then sample: not always the top few
        })
        resp.raise_for_status()
        docs = [d for d in resp.json().get("response", {}).get("docs", [])
                if _ARCHIVE_ID.match(d.get("identifier", "")) and plausibly_public_domain(collection, d)
                and not NOT_COZY.search(f"{d.get('title')} {_plain(d.get('description'))[:300]}")]
        random.shuffle(docs)
        items = []
        for d in docs[:take]:
            ident, title = d["identifier"], _plain(d.get("title"))
            year = d.get("year")
            desc = _sentences(_plain(d.get("description"))) or f"A {kind} from the Internet Archive."
            items.append(_feed_item(
                title=f"{title} ({year})" if year and str(year) not in title else title,
                url=f"https://archive.org/details/{ident}", summary=desc, kind=kind,
                creator=_plain(d.get("creator")) or "Internet Archive",
                image_url=f"https://archive.org/services/img/{ident}",
                media={"type": "embed", "provider": "archive", "id": ident, "runtime": _plain(d.get("runtime")) or None},
                reach=int(d.get("downloads") or 0) or None,
                rights=dict(PUBLIC_DOMAIN_RIGHTS, source_key=f"archive:{collection}", rights_holder="Public domain",
                            license="Public domain, as marked by the uploader on the Internet Archive",
                            attribution="Via the Internet Archive. Public domain as marked on the item page.",
                            verification_status="uploader_marked_public_domain"),
            ))
        return items

    fetch.label = f"archive:{collection}"
    return fetch


GUTENDEX = "https://gutendex.com/books/"


def gutenberg_excerpt(raw: str, limit: int = 1800) -> str | None:
    """The opening of the actual story: past the licence header and front matter, to the first chapter."""
    start = re.search(r"\*\*\* ?START OF (THE|THIS) PROJECT GUTENBERG[^\n]*\n", raw)
    body = raw[start.end():] if start else raw
    end = re.search(r"\*\*\* ?END OF (THE|THIS) PROJECT GUTENBERG", body)
    body = body[: end.start()] if end else body
    body = body.replace("\r\n", "\n")
    # "CHAPTER I" appears first in the contents, then again where the story starts: take the last one early on
    firsts = [m for m in re.finditer(r"\n\s*(CHAPTER|Chapter|BOOK|Book|PART|Part|LETTER|Letter|STAVE|Stave)\s+(I|1|ONE|One|the First)\b[^\n]*\n", body)
              if m.start() < len(body) * 0.3]
    if firsts:
        body = body[firsts[-1].end():]

    def prose(block: str) -> bool:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        flat = _WS.sub(" ", block).strip()
        if len(flat) <= 60 or flat.isupper() or "...." in flat or not re.search(r"[.!?][”’\"']?$", flat):
            return False  # too short, a heading, a contents line, or not a sentence
        if len(lines) >= 3 and sum(len(ln) < 50 for ln in lines) / len(lines) > 0.6:
            return False  # a list of short lines: contents, illustrations, a title page
        return len(re.findall(r"\b(CHAPTER|Chapter)\s+[IVXLC\d]+", flat)) < 2

    paras = [_WS.sub(" ", p).strip() for p in re.split(r"\n\s*\n", body) if prose(p)]
    out, total = [], 0
    for p in paras:
        out.append(p)
        total += len(p)
        if total >= limit:
            break
    text = "\n\n".join(out)
    return text[:limit + 600].rsplit(" ", 1)[0] + ("…" if len(text) > limit + 600 else "") if text else None


def gutenberg_source(take: int = 3):
    def fetch(client: httpx.Client, now: datetime) -> list:
        # Page 1 (the 32 most popular) is cached and fast; later pages take ~15s. Already-known books are skipped
        # by the scout, so this still turns up new ones run after run.
        resp = client.get(GUTENDEX, params={"sort": "popular", "languages": "en"}, timeout=30.0)
        resp.raise_for_status()
        books = [b for b in resp.json().get("results", []) if b.get("copyright") is False and not NOT_COZY.search(b.get("title", ""))]
        random.shuffle(books)
        items = []
        for b in books[: take * 2]:
            if len(items) >= take:
                break
            txt = next((u for k, u in (b.get("formats") or {}).items() if k.startswith("text/plain") and u.startswith("https://")), None)
            if not txt:
                continue
            try:
                raw = client.get(txt, timeout=20.0)
            except httpx.HTTPError:
                continue  # one slow book shouldn't cost the others
            if raw.status_code != 200:
                continue
            excerpt = gutenberg_excerpt(raw.text)
            if not excerpt:
                continue
            author = (b.get("authors") or [{}])[0].get("name", "Unknown")
            if "," in author:  # "Austen, Jane" -> "Jane Austen"
                last, first = author.split(",", 1)
                author = f"{first.strip()} {last.strip()}"
            title = b["title"].split(";")[0].split(":")[0].strip()
            byline = "" if author.lower() in ("unknown", "anonymous", "various") else f", by {author}"
            summary = _sentences(_plain((b.get("summaries") or [""])[0]).replace("(This is an automatically generated summary.)", "")) \
                or f"A public-domain book by {author}."
            url = f"https://www.gutenberg.org/ebooks/{b['id']}"
            items.append(_feed_item(
                title=f"{title}{byline}", url=url, summary=summary, kind="book", creator=author,
                image_url=_https((b.get("formats") or {}).get("image/jpeg")),
                media={"type": "text", "form": "prose", "text": excerpt, "by": author, "more_url": url},
                reach=b.get("download_count"), depth="excerpt",
                rights=dict(PUBLIC_DOMAIN_RIGHTS, source_key="gutenberg", rights_holder="Public domain (USA)",
                            license="Public domain in the USA, via Project Gutenberg", redistribute_or_clip=True,
                            attribution="From Project Gutenberg. Read the whole book there, free.",
                            verification_status="gutenberg_copyright_false"),
            ))
        return items

    fetch.label = "gutenberg"
    return fetch


POETRYDB = "https://poetrydb.org/random/{n}"


def poetry_source(take: int = 3, max_lines: int = 32):
    def fetch(client: httpx.Client, now: datetime) -> list:
        resp = client.get(POETRYDB.format(n=12))
        resp.raise_for_status()
        from .content import GRIM

        poems = [p for p in resp.json() if isinstance(p, dict) and 4 <= int(p.get("linecount") or 0) <= max_lines
                 and not GRIM.search(p.get("title", "")) and not NOT_COZY.search(p.get("title", ""))]
        items = []
        for p in poems[:take]:
            title, author = p["title"].strip(), p["author"].strip()
            text = "\n".join(p.get("lines") or [])
            url = f"https://poetrydb.org/title/{quote(title)}/author,title,lines.json"
            first = next((ln for ln in p["lines"] if ln.strip()), "")
            items.append(_feed_item(
                title=f"{title}, by {author}", url=url, summary=f"A short poem by {author}. It begins: “{first.strip()}”",
                kind="poem", creator=author, media={"type": "text", "form": "poem", "text": text, "by": author},
                depth="excerpt",
                rights=dict(PUBLIC_DOMAIN_RIGHTS, source_key="poetrydb", rights_holder="Public domain",
                            license="Public domain poetry, via PoetryDB", redistribute_or_clip=True,
                            attribution="Via PoetryDB (public-domain poems).", verification_status="public_domain_collection"),
            ))
        return items

    fetch.label = "poetrydb"
    return fetch


MEDIA_SOURCES = [
    *(archive_source(c, kind, take) for c, (kind, take) in ARCHIVE_COLLECTIONS.items()),
    gutenberg_source(),
    poetry_source(),
]
