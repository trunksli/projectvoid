"""Discovery ingestion, rights checks, and the freshness floor (spec §3.2, §3.15 v5)."""

from __future__ import annotations

import json
import logging
import random
import re
from collections.abc import Callable
from datetime import date, datetime
from importlib import resources

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import Settings
from .events import EventType, emit
from .memory import MemoryService, tags_for_text
from .models import Discovery, SeenDiscovery, SourceRights, User

log = logging.getLogger(__name__)

# The lounge is a cozy place: skip items about death, violence and disaster from general feeds.
# A keyword list is a blunt first pass, not a content classifier (see README, known limitations).
GRIM = re.compile(
    r"\b(kill(ed|ing|s)?|dies|died|death|dead|murder\w*|assassinat\w*|massacre\w*|genocide|terror\w*|bomb\w*|"
    r"shoot\w*|crash(ed|es)?|war|wars|attack\w*|execut(ed|ion)|suicide|disaster|famine|earthquake|tsunami|abuse\w*)\b",
    re.I,
)

RIGHT_FIELDS = (
    "link",
    "read_metadata",
    "index_metadata",
    "download_or_store_media",
    "analyze_audio_video",
    "use_captions_or_transcripts",
    "embed_or_play",
    "redistribute_or_clip",
    "translate_or_create_derivatives",
    "share_generated_commentary",
)


def upsert_rights(session: Session, spec: dict) -> SourceRights:
    rights = session.scalar(select(SourceRights).where(SourceRights.source_key == spec["source_key"]))
    if rights is None:
        rights = SourceRights(source_key=spec["source_key"], rights_holder="", license="")
        session.add(rights)
    rights.rights_holder = spec.get("rights_holder", "")
    rights.license = spec.get("license", "")
    rights.attribution = spec.get("attribution", "")
    rights.verification_status = spec.get("verification_status", "unverified")
    for f in RIGHT_FIELDS:  # default deny: anything not explicitly granted is False
        setattr(rights, f, bool(spec.get(f, False)))
    session.flush()
    return rights


def ingest(session: Session, source_key: str, items: list[dict], now: datetime, *, is_fixture: bool = False) -> int:
    """Insert new items (idempotent per source/external_id). Returns how many were new."""
    rights = session.scalar(select(SourceRights).where(SourceRights.source_key == source_key))
    if rights is None or not rights.index_metadata:
        raise PermissionError(f"source {source_key!r} has no rights record allowing metadata indexing")
    new = 0
    for it in items:
        exists = session.scalar(
            select(Discovery).where(Discovery.source_key == source_key, Discovery.external_id == it["external_id"])
        )
        if exists:
            continue
        d = Discovery(
            source_key=source_key,
            external_id=it["external_id"],
            title=it["title"][:300],
            summary=it.get("summary", "")[:2000],
            canonical_url=it["canonical_url"],
            kind=it.get("kind", "article"),
            tags=list(it.get("tags") or sorted(tags_for_text(it["title"] + " " + it.get("summary", ""))) or ["oddities"]),
            analysis_depth=it.get("analysis_depth", "metadata_only"),
            label=it.get("label", "factual"),
            is_fixture=is_fixture,
            ingested_at=now,
        )
        session.add(d)
        session.flush()
        emit(
            session,
            EventType.DISCOVERY_INGESTED,
            actor_type="system",
            actor_id=f"scout:{source_key}",
            payload={"discovery_id": d.id, "title": d.title},
            idempotency_key=f"ingest:{source_key}:{d.external_id}",
            at=now,
        )
        new += 1
    return new


def load_fixtures(session: Session, now: datetime) -> int:
    data = json.loads(resources.files("voidgrid.data").joinpath("fixtures.json").read_text(encoding="utf-8"))
    upsert_rights(session, data["source"])
    return ingest(session, data["source"]["source_key"], data["items"], now, is_fixture=True)


# ---------------------------------------------------------------------------
# A real, rights-cleared source: Wikipedia's featured feed (CC BY-SA 4.0 text)
# ---------------------------------------------------------------------------

WIKIPEDIA_RIGHTS = {
    "source_key": "wikipedia_featured",
    "rights_holder": "Wikipedia contributors",
    "license": "CC BY-SA 4.0 (text)",
    "attribution": "From Wikipedia, the free encyclopedia, CC BY-SA 4.0. Follow the link for the full article and authors.",
    "verification_status": "license_reviewed_by_developer",  # not a legal review
    "link": True,
    "read_metadata": True,
    "index_metadata": True,
    "share_generated_commentary": True,
}


class WikipediaFeaturedSource:
    """Reads https://api.wikimedia.org/feed/v1/wikipedia/en/featured/YYYY/MM/DD (no key needed)."""

    URL = "https://api.wikimedia.org/feed/v1/wikipedia/en/featured/{y:04d}/{m:02d}/{d:02d}"

    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.client = client or httpx.Client(
            timeout=10.0, headers={"User-Agent": f"{settings.brand_name}/0.1 (+{settings.contact_url})"}
        )

    def fetch(self, day: date) -> list[dict]:
        resp = self.client.get(self.URL.format(y=day.year, m=day.month, d=day.day))
        resp.raise_for_status()
        return self.parse(resp.json(), day)

    @staticmethod
    def parse(feed: dict, day: date) -> list[dict]:
        items: list[dict] = []
        tfa = feed.get("tfa")
        if isinstance(tfa, dict) and tfa.get("extract"):
            page = ((tfa.get("content_urls") or {}).get("desktop") or {}).get("page")
            title = (tfa.get("titles") or {}).get("normalized") or tfa.get("title")
            if page and title:
                items.append({"external_id": f"tfa-{day.isoformat()}", "title": title, "summary": tfa["extract"], "canonical_url": page})
        for ev in (feed.get("onthisday") or [])[:5]:
            pages = ev.get("pages") or []
            if not pages or not ev.get("text"):
                continue
            page = ((pages[0].get("content_urls") or {}).get("desktop") or {}).get("page")
            if not page:
                continue
            year = ev.get("year")
            items.append(
                {
                    "external_id": f"otd-{day.isoformat()}-{pages[0].get('pageid', len(items))}",
                    "title": f"On this day in {year}: {ev['text'][:120]}" if year else ev["text"][:140],
                    "summary": pages[0].get("extract") or ev["text"],
                    "canonical_url": page,
                }
            )
        items = [it for it in items if not GRIM.search(it["title"] + " " + it["summary"])]
        for it in items:
            tags = sorted(tags_for_text(it["title"] + " " + it["summary"]))
            it["tags"] = tags or ["history"]
        return items


def refresh_wikipedia(session: Session, settings: Settings, now: datetime) -> int:
    upsert_rights(session, WIKIPEDIA_RIGHTS)
    try:
        items = WikipediaFeaturedSource(settings).fetch(now.date())
    except (httpx.HTTPError, ValueError) as e:
        log.warning("wikipedia featured feed unavailable: %s", e)
        return 0
    return ingest(session, WIKIPEDIA_RIGHTS["source_key"], items, now)


# ---------------------------------------------------------------------------
# Picking a fresh discovery for a person
# ---------------------------------------------------------------------------


class ContentService:
    def __init__(self, session: Session, memory: MemoryService, now: Callable[[], datetime]):
        self.s = session
        self.memory = memory
        self.now = now

    def pick_fresh(self, user: User, seed: int = 0) -> tuple[Discovery | None, str | None]:
        """Return (discovery, fulfilled_promise_tag). Never repeats a discovery for the same person."""
        seen = select(SeenDiscovery.discovery_id).where(SeenDiscovery.user_id == user.id)
        candidates = list(
            self.s.scalars(
                select(Discovery)
                .join(SourceRights, SourceRights.source_key == Discovery.source_key)
                .where(SourceRights.read_metadata.is_(True), SourceRights.link.is_(True), Discovery.id.not_in(seen))
            )
        )
        if not candidates:
            return None, None
        likes, dislikes = self.memory.taste_tags(user)
        promises = {p.content: p for p in self.memory.open_promises(user)}
        rng = random.Random(seed)

        def score(d: Discovery) -> tuple[float, str | None]:
            sc = rng.uniform(0, 0.5)  # controlled serendipity
            tags = set(d.tags or [])
            sc += sum(likes.get(t, 0) for t in tags)
            sc -= 1.5 * sum(dislikes.get(t, 0) for t in tags)
            hit = next((t for t in promises if t in tags), None)
            if hit:
                sc += 2.0
            if not d.is_fixture:
                sc += 0.3  # prefer real, current content when we have it
            return sc, hit

        scored = [(score(d), d) for d in candidates]
        (best_score, promise_tag), best = max(scored, key=lambda x: x[0][0])
        return best, promise_tag

    def mark_seen(self, user: User, d: Discovery) -> None:
        if self.s.get(SeenDiscovery, (user.id, d.id)) is None:
            self.s.add(SeenDiscovery(user_id=user.id, discovery_id=d.id, seen_at=self.now()))
            self.s.flush()

    @staticmethod
    def public_view(d: Discovery) -> dict:
        r = d.rights
        return {
            "id": d.id,
            "title": d.title,
            "summary": d.summary,
            "url": d.canonical_url,
            "kind": d.kind,
            "tags": d.tags,
            "label": d.label,
            "what_we_accessed": d.analysis_depth,
            "is_fixture": d.is_fixture,
            "source": {"key": d.source_key, "license": r.license, "attribution": r.attribution},
        }
