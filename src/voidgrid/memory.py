"""Memory (spec §3.7 four layers + §3.16 user recognition).

Layers:
- core_identity: lives in characters.py (edited deliberately, not learned).
- working_context: the room transcript of the current exchange (never persisted here).
- episodic: a small, salience-selected share (~20%) of moments, stored per regular with its own interpretation.
- relationship: per regular, evolving stats/notes about other regulars and the user.

User facts (name, tastes, promises, moments) bypass the episodic budget and live in `user_facts`.
"""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from .characters import REGULARS
from .config import Settings
from .events import EventType, emit
from .models import AgentMemory, Lounge, User, UserFact, Utterance

# A small vocabulary keeps taste matching inspectable. Real ranking can replace this later.
TAG_SYNONYMS: dict[str, tuple[str, ...]] = {
    "animals": ("animal", "octopus", "octopuses", "bird", "birds", "cat", "cats", "dog", "dogs", "whale", "whales", "insect", "fish"),
    "space": ("space", "astronomy", "planet", "planets", "star", "stars", "moon", "rocket", "rockets", "nasa"),
    "science": ("science", "physics", "chemistry", "biology", "experiment", "experiments"),
    "history": ("history", "historical", "ancient", "medieval", "war", "empire"),
    "engineering": ("engineering", "machine", "machines", "invention", "inventions", "bridge", "bridges", "robot", "robots"),
    "nature": ("nature", "plant", "plants", "tree", "trees", "ocean", "oceans", "forest", "deep sea", "deep-sea"),
    "art": ("art", "painting", "paintings", "sculpture", "design"),
    "music": ("music", "song", "songs", "band", "instrument"),
    "food": ("food", "cooking", "recipe", "recipes", "bread", "cheese", "coffee"),
    "culture": ("culture", "language", "languages", "tradition", "traditions", "film", "films", "book", "books"),
    "oddities": ("odd", "weird", "strange", "oddities", "bizarre", "unusual"),
    "mystery": ("mystery", "mysteries", "unsolved", "puzzle", "puzzles"),
}

_NAME_RE = re.compile(r"\b(?:my name is|call me|i go by)\s+([A-Za-z][A-Za-z'\-]{1,30})", re.I)
_LIKE_RE = re.compile(r"\bi\s+(?:really\s+|absolutely\s+)?(?:love|like|enjoy|adore)\s+([^.!?,;]{2,60})", re.I)
_DISLIKE_RE = re.compile(
    r"\bi\s+(?:(?:really\s+)?(?:don't|do not|dont)\s+(?:like|enjoy|care for)|hate|can't stand|cannot stand)\s+([^.!?,;]{2,60})",
    re.I,
)
_DISAGREE_MARKERS = ("push back", "no,", "disagree", "missing the point", "respectfully", "not convinced", "but ")

INTERPRETATION = {
    "theo": "worth checking properly later",
    "jules": "comedy gold, frankly",
    "pip": "that made my night",
    "wren": "good night in the room",
}


def tags_for_text(text: str) -> set[str]:
    low = text.lower()
    found = set()
    for tag, words in TAG_SYNONYMS.items():
        if any(re.search(rf"\b{re.escape(w)}\b", low) for w in (tag, *words)):
            found.add(tag)
    return found


def extract_facts(text: str) -> list[tuple[str, str, float]]:
    """Rule-based extraction of durable facts the user stated explicitly about themselves."""
    out: list[tuple[str, str, float]] = []
    if m := _NAME_RE.search(text):
        out.append(("name", m.group(1).strip().capitalize(), 0.95))
    for m in _DISLIKE_RE.finditer(text):
        out.append(("dislikes", m.group(1).strip().rstrip(" ."), 0.85))
    for m in _LIKE_RE.finditer(text):
        span_start = m.start()
        # don't double-count "don't like X" as "like X"
        if any(d.start() <= span_start < d.end() for d in _DISLIKE_RE.finditer(text)):
            continue
        out.append(("likes", m.group(1).strip().rstrip(" ."), 0.85))
    return out


class MemoryService:
    def __init__(self, session: Session, settings: Settings, now: Callable[[], datetime]):
        self.s = session
        self.settings = settings
        self.now = now

    # ------------------------------------------------------------------ user facts (§3.16)
    def store_fact(
        self,
        user: User,
        kind: str,
        content: str,
        confidence: float,
        source: str,
        *,
        utterance_id: int | None = None,
        agent_key: str | None = None,
        lounge_id: int | None = None,
    ) -> UserFact:
        content = content.strip()[:300]
        existing = self.s.scalars(
            select(UserFact).where(UserFact.user_id == user.id, UserFact.kind == kind, UserFact.deleted_at.is_(None))
        ).all()
        for f in existing:
            if f.content.lower() == content.lower() and (kind != "promise" or f.fulfilled_at is None):
                f.confidence = max(f.confidence, confidence)
                return f
        fact = UserFact(
            user_id=user.id,
            kind=kind,
            content=content,
            confidence=confidence,
            source=source,
            source_utterance_id=utterance_id,
            agent_key=agent_key,
            created_at=self.now(),
        )
        self.s.add(fact)
        self.s.flush()
        emit(
            self.s,
            EventType.FACT_STORED,
            actor_type="system",
            actor_id="memory",
            lounge_id=lounge_id,
            payload={"fact_id": fact.id, "kind": kind},
            at=self.now(),
        )
        return fact

    def active_facts(self, user: User) -> list[UserFact]:
        return list(
            self.s.scalars(
                select(UserFact)
                .where(UserFact.user_id == user.id, UserFact.deleted_at.is_(None))
                .order_by(UserFact.created_at, UserFact.id)
            )
        )

    def name(self, user: User) -> tuple[str | None, float]:
        names = [f for f in self.active_facts(user) if f.kind == "name"]
        if not names:
            return None, 0.0
        latest = names[-1]
        return latest.content, latest.confidence

    def greeting_name(self, user: User) -> tuple[str | None, str | None]:
        """(confident_name, hedged_name). A wrong memory is worse than none: below threshold we only hedge."""
        name, conf = self.name(user)
        if not name:
            return None, None
        if conf >= self.settings.fact_hedge_threshold:
            return name, None
        return None, name

    def taste_tags(self, user: User) -> tuple[dict[str, float], dict[str, float]]:
        likes: dict[str, float] = {}
        dislikes: dict[str, float] = {}
        for f in self.active_facts(user):
            if f.kind not in ("likes", "dislikes"):
                continue
            target = likes if f.kind == "likes" else dislikes
            for t in tags_for_text(f.content):
                target[t] = max(target.get(t, 0.0), f.confidence)
        return likes, dislikes

    def open_promises(self, user: User) -> list[UserFact]:
        return [f for f in self.active_facts(user) if f.kind == "promise" and f.fulfilled_at is None]

    def forget(self, user: User, fact_id: int) -> UserFact | None:
        fact = self.s.get(UserFact, fact_id)
        if not fact or fact.user_id != user.id or fact.deleted_at:
            return None
        fact.deleted_at = self.now()
        # Quotes ("moments") and episodes built from the same utterance must not resurface it either.
        if fact.source_utterance_id:
            for m in self.s.scalars(select(UserFact).where(
                    UserFact.user_id == user.id, UserFact.kind == "moment", UserFact.deleted_at.is_(None),
                    UserFact.source_utterance_id == fact.source_utterance_id)):
                m.deleted_at = self.now()
            for m in self.s.scalars(select(AgentMemory).where(AgentMemory.retired_at.is_(None))):
                if fact.source_utterance_id in (m.source_utterance_ids or []):
                    m.retired_at = self.now()
        emit(self.s, EventType.FACT_DELETED, actor_type="human_owner", actor_id=user.handle, payload={"fact_id": fact_id}, at=self.now())
        return fact

    # ------------------------------------------------------------------ per-agent context (independent memories)
    def agent_context(self, agent_key: str, lounge: Lounge, user: User | None, *, guest: bool = False) -> str:
        """Only this regular's own episodes and relationships, plus the shared durable fact store.

        guest=True (a VIP is the audience): no facts, no episodes, no notes about the owner. Episodes can quote
        the owner's own words, so they are withheld entirely rather than filtered.
        """
        lines: list[str] = []
        if user is not None:
            facts = self.active_facts(user)
            if facts:
                lines.append("What you know about the person whose spot this is (durable facts):")
                thr = self.settings.fact_hedge_threshold
                for f in facts:
                    if f.kind == "promise":
                        if f.agent_key != agent_key or f.fulfilled_at:
                            continue
                        lines.append(f"- You promised them: {f.content}")
                        continue
                    unsure = " (UNSURE: hedge or ask, never assert)" if f.confidence < thr else ""
                    lines.append(f"- {f.kind}: {f.content}{unsure}  [source: {f.source}]")
        rels = self.s.scalars(
            select(AgentMemory).where(
                AgentMemory.agent_key == agent_key,
                AgentMemory.lounge_id == lounge.id,
                AgentMemory.layer == "relationship",
                AgentMemory.retired_at.is_(None),
            )
        ).all()
        if guest:
            rels = [r for r in rels if r.about_agent_key is not None]
        if rels:
            lines.append("Your relationships:")
            lines += [f"- {r.content}" for r in rels]
        eps = [] if guest else self.recent_episodes(agent_key, lounge, limit=5)
        if eps:
            lines.append("Moments you remember (your own take):")
            lines += [f"- {e.content}" for e in eps]
        return "\n".join(lines) if lines else "You have no memories of this place yet."

    def recent_episodes(self, agent_key: str, lounge: Lounge, limit: int = 5) -> list[AgentMemory]:
        return list(
            self.s.scalars(
                select(AgentMemory)
                .where(
                    AgentMemory.agent_key == agent_key,
                    AgentMemory.lounge_id == lounge.id,
                    AgentMemory.layer == "episodic",
                    AgentMemory.retired_at.is_(None),
                )
                .order_by(AgentMemory.salience.desc(), AgentMemory.created_at.desc())
                .limit(limit)
            )
        )

    def callback_topic(self, agent_key: str, lounge: Lounge, exclude_topic: str | None) -> str | None:
        for e in self.recent_episodes(agent_key, lounge, limit=10):
            topic = (e.stats or {}).get("topic")
            if topic and topic != exclude_topic:
                return topic
        return None

    # ------------------------------------------------------------------ after each exchange
    def record_exchange(
        self,
        lounge: Lounge,
        owner: User | None,
        utterances: list[Utterance],
        topic: str | None,
        *,
        vip_present: bool = False,
        stances: dict[int, str] | None = None,
    ) -> list[Utterance]:
        """Select ~20% of moments by salience and store each participant's own interpretation."""
        stances = stances or {}
        now = self.now()
        candidates = [u for u in utterances if u.speaker_key != "wren"]
        if not candidates:
            return []
        participants = {u.speaker_key for u in candidates if u.speaker_type == "bot"}

        def salience(u: Utterance) -> float:
            sc = 0.1
            low = u.text.lower()
            if u.speaker_type != "bot":
                sc += 0.6
            if stances.get(u.id) == "disagree" or any(m in low for m in _DISAGREE_MARKERS):
                sc += 0.3
            if u.speaker_key == "jules":
                sc += 0.15
            if vip_present:
                sc += 0.3
            if topic and self._already_remembered(lounge, topic):
                sc -= 0.2  # novelty: we already hold a moment about this
            return sc

        scores = {u.id: salience(u) for u in candidates}  # score before storing anything new
        ranked = sorted(candidates, key=lambda u: scores[u.id], reverse=True)
        k = max(1, math.ceil(self.settings.episodic_retention_ratio * len(candidates)))
        kept = ranked[:k]
        for u in kept:
            sal = scores[u.id]
            for agent in participants:
                who = "I" if agent == u.speaker_key else u.speaker_name
                quote = u.text if len(u.text) <= 160 else u.text[:157] + "…"
                content = f"{who} on “{topic or 'a quiet night'}”: “{quote}” — {INTERPRETATION.get(agent, 'memorable')}"
                self.s.add(
                    AgentMemory(
                        agent_key=agent,
                        lounge_id=lounge.id,
                        layer="episodic",
                        about_user_id=owner.id if (owner and u.speaker_type == "human_owner") else None,
                        content=content,
                        stats={"topic": topic},
                        salience=sal,
                        source_utterance_ids=[u.id],
                        created_at=now,
                        updated_at=now,
                    )
                )
        # The owner's own words are durable "moments" (bypass the budget, §3.16).
        if owner is not None:
            for u in candidates:
                if u.speaker_type == "human_owner":
                    self.store_fact(
                        owner,
                        "moment",
                        f"You said “{u.text[:120]}” about “{topic or 'a quiet night'}”",
                        0.9,
                        f"your own words on {now:%Y-%m-%d}",
                        utterance_id=u.id,
                        lounge_id=lounge.id,
                    )
        self._update_relationships(lounge, owner, utterances, topic, stances)
        self.s.flush()
        return kept

    def _already_remembered(self, lounge: Lounge, topic: str) -> bool:
        for m in self.s.scalars(
            select(AgentMemory).where(AgentMemory.lounge_id == lounge.id, AgentMemory.layer == "episodic", AgentMemory.retired_at.is_(None))
        ):
            if (m.stats or {}).get("topic") == topic:
                return True
        return False

    def _relationship(self, agent: str, lounge: Lounge, *, other_agent: str | None = None, user: User | None = None) -> AgentMemory:
        q = select(AgentMemory).where(
            AgentMemory.agent_key == agent,
            AgentMemory.lounge_id == lounge.id,
            AgentMemory.layer == "relationship",
            AgentMemory.retired_at.is_(None),
        )
        q = q.where(AgentMemory.about_agent_key == other_agent) if other_agent else q.where(AgentMemory.about_user_id == user.id)
        rel = self.s.scalar(q)
        if rel is None:
            rel = AgentMemory(
                agent_key=agent,
                lounge_id=lounge.id,
                layer="relationship",
                about_agent_key=other_agent,
                about_user_id=user.id if user else None,
                content="",
                stats={"exchanges": 0, "disagreements": 0},
                created_at=self.now(),
                updated_at=self.now(),
            )
            self.s.add(rel)
            self.s.flush()
        return rel

    def _update_relationships(self, lounge, owner, utterances, topic, stances) -> None:
        prev: Utterance | None = None
        for u in utterances:
            if prev is not None and u.speaker_type == "bot" and u.speaker_key != "wren" and prev.speaker_key != u.speaker_key:
                if prev.speaker_type == "bot" and prev.speaker_key != "wren":
                    rel = self._relationship(u.speaker_key, lounge, other_agent=prev.speaker_key)
                    other = REGULARS[prev.speaker_key].name
                elif prev.speaker_type == "human_owner" and owner is not None:
                    rel = self._relationship(u.speaker_key, lounge, user=owner)
                    other = "the person whose spot this is"
                else:
                    prev = u
                    continue
                st = dict(rel.stats or {})
                st["exchanges"] = st.get("exchanges", 0) + 1
                if stances.get(u.id) == "disagree":
                    st["disagreements"] = st.get("disagreements", 0) + 1
                st["last_topic"] = topic
                rel.stats = st
                rel.content = (
                    f"{other}: talked {st['exchanges']} time(s), you pushed back {st.get('disagreements', 0)} time(s); "
                    f"last about “{topic or 'nothing much'}”."
                )
                rel.updated_at = self.now()
            prev = u

    # ------------------------------------------------------------------ consolidation
    def consolidate(self, lounge: Lounge) -> int:
        """Merge duplicate episodes and retire the lowest-value ones beyond the per-agent cap."""
        retired = 0
        now = self.now()
        for agent in REGULARS:
            eps = list(
                self.s.scalars(
                    select(AgentMemory)
                    .where(
                        AgentMemory.agent_key == agent,
                        AgentMemory.lounge_id == lounge.id,
                        AgentMemory.layer == "episodic",
                        AgentMemory.retired_at.is_(None),
                    )
                    .order_by(AgentMemory.salience.desc(), AgentMemory.created_at.desc())
                )
            )
            seen: dict[str, AgentMemory] = {}
            for e in eps:
                if e.content in seen:
                    keep = seen[e.content]
                    keep.source_utterance_ids = list({*keep.source_utterance_ids, *e.source_utterance_ids})
                    e.retired_at = now
                    retired += 1
                else:
                    seen[e.content] = e
            for e in list(seen.values())[self.settings.episodic_cap_per_agent :]:
                e.retired_at = now
                retired += 1
        emit(self.s, EventType.MEMORY_CONSOLIDATED, actor_type="system", actor_id="memory", lounge_id=lounge.id, payload={"retired": retired}, at=now)
        return retired
