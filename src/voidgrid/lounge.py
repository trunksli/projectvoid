"""The owner's lounge (spec §3.15): arrive, listen, join in, personalise, leave, and truthful catch-up."""

from __future__ import annotations

from sqlalchemy import select

from .app import App, Ctx
from .characters import HOST, MODES, PIP, REGULARS, THEMES
from .common import (
    LoungeError,
    clean_text,
    get_or_create_lounge,
    get_or_create_user,
    line_dicts,
    narrate,
    open_presence,
    owner_presence,
    take_notices,
    theme_info,
    touch,
    wall,
    when,
)
from .content import ContentService
from .events import EventType, emit
from .gallery import ExchangePlan, _seed
from .memory import extract_facts
from .models import (
    AgentMemory,
    Decoration,
    Discovery,
    Event,
    Exchange,
    Knock,
    Lounge,
    Note,
    Notice,
    Presence,
    SeenDiscovery,
    User,
    UserFact,
    Utterance,
    VipRelationship,
)

REACTIONS = ("loved", "liked", "meh")


def _and_join(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def build_catchup(c: Ctx, user: User, lounge: Lounge, since) -> list[dict]:
    """Only real, recorded events since the person was last here (spec §3.15: truthful catch-up)."""
    if since is None:
        return []
    now = c.now()
    items: list[dict] = []
    evs = c.s.scalars(
        select(Event).where(Event.lounge_id == lounge.id, Event.created_at > since, Event.actor_type == "human_vip").order_by(Event.created_at, Event.id)
    ).all()
    left_rel_after: dict[int, list] = {}
    for e in evs:
        if e.type == EventType.VIP_LEFT:
            left_rel_after.setdefault((e.payload or {}).get("rel_id"), []).append(e.created_at)
    here_rel_ids = {pr.vip_relationship_id for pr in open_presence(c, lounge) if pr.role == "vip"}
    for e in evs:
        p = e.payload or {}
        who = f"{p.get('name')} (your {p.get('label')})"
        at = when(e.created_at, now)
        if e.type == EventType.VIP_LEFT:
            text = f"{who} stopped by {at}"
            if p.get("shared") and p.get("chatted_with"):
                text += f" and chatted with {_and_join(p['chatted_with'])}"
                if p.get("topic"):
                    text += f" about “{p['topic']}”"
            text += f" — they said: “{p['highlight']}”" if (p.get("shared") and p.get("highlight")) else "."
            items.append({"type": "vip_visit", "text": text, "at": e.created_at.isoformat(), "who": p.get("name")})
        elif e.type == EventType.VIP_JOINED:
            # A visit that ended without a goodbye (they wandered off) still counts as a visit.
            ended = any(t >= e.created_at for t in left_rel_after.get(p.get("rel_id"), []))
            if not ended and p.get("rel_id") not in here_rel_ids:
                items.append({"type": "vip_visit", "text": f"{who} stopped by {at}.", "at": e.created_at.isoformat(), "who": p.get("name")})
        elif e.type == EventType.VIP_NOTE:
            items.append({"type": "vip_note", "text": f"{who} left you a note {at}: “{p.get('text')}”", "at": e.created_at.isoformat(), "who": p.get("name")})
        elif e.type == EventType.VIP_PINNED:
            items.append({"type": "vip_pin", "text": f"{who} pinned “{p.get('item')}” to {p.get('spot')} {at}.", "at": e.created_at.isoformat(), "who": p.get("name")})
        elif e.type == EventType.VIP_KNOCKED:
            k = c.s.get(Knock, p.get("knock_id"))
            tail = " They're still waiting — you can let them in." if k and k.status == "pending" else ""
            items.append({"type": "vip_knock", "text": f"{who} knocked {at}.{tail}", "at": e.created_at.isoformat(), "knock_id": p.get("knock_id"), "who": p.get("name")})
        elif e.type == EventType.VIP_DENIED:
            items.append({"type": "vip_denied", "text": f"{who} tried to drop by {at}, but your lounge was set to private.", "at": e.created_at.isoformat(), "who": p.get("name")})
    # VIPs who are here right now
    for pr in open_presence(c, lounge):
        if pr.role == "vip":
            rel = c.s.get(VipRelationship, pr.vip_relationship_id)
            items.append({"type": "vip_here", "text": f"{pr.display_name} (your {rel.label if rel else 'guest'}) is here right now.", "at": pr.joined_at.isoformat(), "who": pr.display_name})
    new_finds = c.s.scalars(
        select(Event).where(Event.type == EventType.DISCOVERY_INGESTED, Event.created_at > since)
    ).all()
    if new_finds:
        n = len(new_finds)
        items.append({"type": "new_finds", "text": f"{n} new find{'s' if n != 1 else ''} came in.", "at": new_finds[-1].created_at.isoformat()})
    return items


VERBS = {"vip_visit": "stopped by", "vip_note": "left you a note", "vip_pin": "pinned something to your wall",
         "vip_knock": "knocked", "vip_denied": "tried to drop by", "vip_here": "is here now"}


def catchup_summary(items: list[dict]) -> list[str]:
    """One short sentence per person for the host to say; the full list is shown separately."""
    by_person: dict[str, list[str]] = {}
    out: list[str] = []
    for i in items:
        if i.get("who") and i["type"] in VERBS:
            verbs = by_person.setdefault(i["who"], [])
            if VERBS[i["type"]] not in verbs:
                verbs.append(VERBS[i["type"]])
        elif i["type"] == "new_finds":
            out.append(i["text"])
    people = [f"{who} {_and_join(v)}." for who, v in by_person.items()]
    return people + out


class LoungeService:
    def __init__(self, app: App):
        self.app = app

    # ------------------------------------------------------------------ helpers
    def _commentator_turns(self, lounge: Lounge) -> int:
        s = self.app.settings
        return s.quiet_gallery_turns if lounge.mode == "quiet" else max(1, s.max_gallery_turns - 1)

    def _place(self, c: Ctx, lounge: Lounge) -> dict:
        t = theme_info(lounge)
        return {
            "theme": lounge.theme,
            "setting": t["name"],
            "description": t["description"],
            "mode": lounge.mode,
            "favorite_seat": lounge.favorite_seat,
            "seat_ideas": t["seats"],
            "wall_spots": t["spots"],
            "wall": wall(c, lounge),
            "join_policy": lounge.join_policy,
        }

    def _here(self, c: Ctx, lounge: Lounge) -> list[dict]:
        here = [{"name": ch.name, "type": "bot", "label": f"{ch.name} (AI regular, {ch.role})"} for ch in REGULARS.values()]
        for p in open_presence(c, lounge):
            if p.role == "vip":
                rel = c.s.get(VipRelationship, p.vip_relationship_id)
                here.append({"name": p.display_name, "type": "human_vip", "label": f"{p.display_name} (human, your {rel.label if rel else 'guest'})"})
        return here

    def _scene(self, c: Ctx, lounge: Lounge) -> str:
        place = self._place(c, lounge)
        lines = [f"[{place['setting']} — {place['description']}]"]
        if place["favorite_seat"]:
            lines.append(f"You're in your spot: {place['favorite_seat']}.")
        if place["wall"]:
            pinned = "; ".join(f"“{w['label']}” {w['spot']} (from {w['placed_by']})" for w in place["wall"])
            lines.append(f"On the wall: {pinned}.")
        lines.append("Here now: " + ", ".join(h["label"] for h in self._here(c, lounge)) + ".")
        return "\n".join(lines)

    def _start(self, c: Ctx, handle: str) -> tuple[User, Lounge]:
        user = get_or_create_user(c, handle)
        lounge = get_or_create_lounge(c, user)
        return user, lounge

    def _require_present(self, c: Ctx, user: User, lounge: Lounge) -> Presence:
        p = owner_presence(c, lounge)
        if p is None:
            raise LoungeError("You're not in the lounge right now. Use enter_lounge first.")
        touch(c, p)
        user.last_seen_at = c.now()
        return p

    def _plan(self, c: Ctx, user: User, lounge: Lounge, kind: str, discovery: Discovery | None, **kw) -> ExchangePlan:
        vip_here = any(p.role == "vip" for p in open_presence(c, lounge))
        return ExchangePlan(kind=kind, lounge=lounge, owner=user, discovery=discovery, vip_present=vip_here, **kw)

    def _speaker_name(self, c: Ctx, user: User) -> str:
        name, _hedged = c.memory.greeting_name(user)
        return name or user.handle

    # ------------------------------------------------------------------ arrive
    def enter(self, handle: str) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            now = c.now()
            returning = user.last_seen_at is not None
            catchup = build_catchup(c, user, lounge, user.last_seen_at)
            for n in c.s.scalars(select(Note).where(Note.lounge_id == lounge.id, Note.read_at.is_(None))):
                n.read_at = now
            if user.last_visit_ended_at:  # live notices from a past visit are covered by the catch-up instead
                for n in c.s.scalars(select(Notice).where(
                        Notice.user_id == user.id, Notice.delivered_at.is_(None), Notice.created_at <= user.last_visit_ended_at)):
                    n.delivered_at = now
            old = owner_presence(c, lounge)
            if old:
                old.left_at = now
            c.s.add(Presence(lounge_id=lounge.id, user_id=user.id, role="owner", display_name=user.handle, joined_at=now, last_active_at=now))
            emit(c.s, EventType.VISIT_STARTED, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, at=now)

            discovery, promise_tag = c.content.pick_fresh(user, seed=_seed(user.id, now.isoformat()), last_kind=self._last_kind(c, lounge))
            promise_agent = None
            if promise_tag:
                for p in c.memory.open_promises(user):
                    if p.content == promise_tag:
                        p.fulfilled_at = now
                        promise_agent = p.agent_key
                        break
            if discovery:
                c.content.mark_seen(user, discovery)
                c.ensure_briefing(discovery)
                lounge.current_discovery_id = discovery.id
                emit(c.s, EventType.DISCOVERY_SHOWN, actor_type="system", actor_id="curator", lounge_id=lounge.id, payload={"discovery_id": discovery.id}, at=now)
            else:
                lounge.current_discovery_id = None

            name, hedged = c.memory.greeting_name(user)
            host_facts = {
                "user_name": name,
                "hedged_name": hedged,
                "seat": lounge.favorite_seat,
                "returning": returning,
                "catchup_lines": catchup_summary(catchup),
                "empty_bar": discovery is None,
            }
            plan = self._plan(
                c, user, lounge, "arrival" if discovery else "empty_bar", discovery,
                host_facts=host_facts, promise_tag=promise_tag if promise_agent else None, promise_agent=promise_agent,
                max_commentator_turns=self._commentator_turns(lounge),
            )
            lines = c.gallery.run(plan)
            user.last_seen_at = now
            user.last_visit_started_at = now
            return self._result(c, user, lounge, lines, discovery=discovery, catchup=catchup, include_scene=True)

    def _result(self, c: Ctx, user: User, lounge: Lounge, lines: list[Utterance], *, discovery=None, catchup=None, include_scene=False, extra: dict | None = None) -> dict:
        parts: list[str] = []
        if include_scene:
            parts.append(self._scene(c, lounge))
        if catchup:
            parts.append("While you were away:\n" + "\n".join(f"- {i['text']}" for i in catchup))
        if discovery is not None:
            v = ContentService.public_view(discovery)
            tag = " · sample content" if v["is_fixture"] else ""
            parts.append(
                f"Tonight's find ({v['label']}{tag}): {v['title']}\n{v['summary']}\nSource: {v['url']} — {v['source']['license']}. "
                f"What we accessed: {v['what_we_accessed'].replace('_', ' ')}."
            )
        if lines:
            parts.append(narrate(lines))
        notices = take_notices(c, user)
        if notices:
            parts.append("Just now:\n" + "\n".join(f"- {n}" for n in notices))
        parts.append("(No need to reply. You can listen for more, say something, react, pin it to your wall, or just leave.)")
        out = {
            "narration": "\n\n".join(parts),
            "conversation": line_dicts(lines),
            "discovery": ContentService.public_view(discovery) if discovery is not None else None,
            "catch_up": catchup or [],
            "here_now": self._here(c, lounge),
            "place": self._place(c, lounge),
            "notices": notices,
        }
        if extra:
            out.update(extra)
        return out

    # ------------------------------------------------------------------ in the room
    def listen(self, handle: str) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            self._require_present(c, user, lounge)
            d = c.s.get(Discovery, lounge.current_discovery_id) if lounge.current_discovery_id else None
            recent = list(reversed(c.s.scalars(
                select(Utterance).where(Utterance.lounge_id == lounge.id).order_by(Utterance.id.desc()).limit(4)).all()))
            c.ensure_briefing(d)
            plan = self._plan(c, user, lounge, "listen" if d else "listen_empty", d, context=recent,
                              max_commentator_turns=2 if lounge.mode == "quiet" else 3, beats_done=self._beats_done(c, lounge, d))
            lines = c.gallery.run(plan)
            return self._result(c, user, lounge, lines)

    @staticmethod
    def _last_kind(c: Ctx, lounge: Lounge) -> str | None:
        d = c.s.get(Discovery, lounge.current_discovery_id) if lounge.current_discovery_id else None
        return d.kind if d else None

    @staticmethod
    def _beats_done(c: Ctx, lounge: Lounge, d: Discovery | None) -> set[str]:
        if d is None:
            return set()
        rows = c.s.scalars(
            select(Utterance).join(Exchange, Exchange.id == Utterance.exchange_id)
            .where(Utterance.lounge_id == lounge.id, Exchange.discovery_id == d.id, Utterance.meta.is_not(None))
        )
        return {u.speaker_key for u in rows if (u.meta or {}).get("beat")}

    def next_find(self, handle: str) -> dict:
        """Put a different find on the table; the regulars react to it (no greeting, you're already here)."""
        return self.play(handle, None)

    def lineup(self, handle: str, exclude: set[int] | None = None, n: int = 5) -> dict:
        """Five options to choose from, each with a mini preview. Logged (slot, exploratory, odds) for the forecaster."""
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            now = c.now()
            ex = set(exclude or ()) | ({lounge.current_discovery_id} if lounge.current_discovery_id else set())
            opts = c.content.lineup(user, n, seed=_seed(user.id, "lineup", now.isoformat(), sorted(ex)), exclude=ex,
                                    last_kind=self._last_kind(c, lounge))
            ev = emit(c.s, EventType.LINEUP_SHOWN, actor_type="system", actor_id="curator", lounge_id=lounge.id, at=now, payload={
                "options": [{"discovery_id": o["discovery"].id, "slot": i, "kind": o["discovery"].kind, "rank_score": o["score"],
                             "exploratory": o["exploratory"], "propensity": o["propensity"]} for i, o in enumerate(opts)],
            })
            return {
                "lineup_id": ev.id if ev else None,
                "options": [dict(ContentService.public_view(o["discovery"]), slot=i, exploratory=o["exploratory"]) for i, o in enumerate(opts)],
            }

    def play(self, handle: str, discovery_id: int | None, *, slot: int | None = None, lineup_id: int | None = None) -> dict:
        """Put a find on (the one you picked, or the best next one); the regulars react to what's playing."""
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            self._require_present(c, user, lounge)
            now = c.now()
            promise_tag = None
            if discovery_id is None:
                d, promise_tag = c.content.pick_fresh(user, seed=_seed(user.id, "next", now.isoformat()), last_kind=self._last_kind(c, lounge))
            else:
                d = c.s.get(Discovery, discovery_id)
                if d is None or not (d.rights.read_metadata and d.rights.link):
                    raise LoungeError("That one isn't available.")
                tags = set(d.tags or [])
                promise_tag = next((p.content for p in c.memory.open_promises(user) if p.content in tags), None)
            if d is None:
                lounge.current_discovery_id = None
                return self._result(c, user, lounge, [], extra={"narration_note": "That's everything for now. The scout will turn up more."})
            promise_agent = None
            if promise_tag:
                for p in c.memory.open_promises(user):
                    if p.content == promise_tag:
                        p.fulfilled_at = now
                        promise_agent = p.agent_key
                        break
            c.content.mark_seen(user, d)
            c.ensure_briefing(d)
            lounge.current_discovery_id = d.id
            emit(c.s, EventType.DISCOVERY_SHOWN, actor_type="system", actor_id="curator", lounge_id=lounge.id, payload={"discovery_id": d.id}, at=now)
            if discovery_id is not None:
                emit(c.s, EventType.DISCOVERY_PLAYED, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, at=now,
                     payload={"discovery_id": d.id, "slot": slot, "lineup_id": lineup_id, "kind": d.kind})
            plan = self._plan(c, user, lounge, "next", d, promise_tag=promise_tag if promise_agent else None, promise_agent=promise_agent,
                              max_commentator_turns=self._commentator_turns(lounge))
            lines = c.gallery.run(plan)
            return self._result(c, user, lounge, lines, discovery=d)

    def current(self, handle: str) -> dict:
        """The find on the table and the recent conversation, without anyone speaking (for the web UI)."""
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            d = c.s.get(Discovery, lounge.current_discovery_id) if lounge.current_discovery_id else None
            recent = list(reversed(c.s.scalars(
                select(Utterance).where(Utterance.lounge_id == lounge.id).order_by(Utterance.id.desc()).limit(30)).all()))
            return {
                "discovery": ContentService.public_view(d) if d else None,
                "conversation": line_dicts(recent),
                "place": self._place(c, lounge),
                "here_now": self._here(c, lounge),
                "you_are_here": owner_presence(c, lounge) is not None,
            }

    def say(self, handle: str, text: str) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            self._require_present(c, user, lounge)
            text = clean_text(text, 1000)
            now = c.now()
            d = c.s.get(Discovery, lounge.current_discovery_id) if lounge.current_discovery_id else None
            u = Utterance(
                exchange_id=None, lounge_id=lounge.id, speaker_type="human_owner", speaker_key=user.handle,
                speaker_name=self._speaker_name(c, user), text=text, created_at=now,
            )
            # Store what they told us first, so the regulars can use it in their reply.
            stored = [
                c.memory.store_fact(user, kind, content, conf, f"you told us on {now:%Y-%m-%d}", lounge_id=lounge.id)
                for kind, content, conf in extract_facts(text)
            ]
            u.speaker_name = self._speaker_name(c, user)
            plan =self._plan(c, user, lounge, "reply", d, human_line=u, max_commentator_turns=2)
            lines = c.gallery.run(plan)
            for f in stored:
                f.source_utterance_id = f.source_utterance_id or u.id
            learned = [{"id": f.id, "kind": f.kind, "content": f.content} for f in stored]
            emit(c.s, EventType.HUMAN_SPOKE, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, payload={"utterance_id": u.id}, at=now)
            return self._result(c, user, lounge, lines, extra={"remembered": learned})

    def react(self, handle: str, reaction: str) -> dict:
        reaction = (reaction or "").strip().lower()
        if reaction not in REACTIONS:
            raise LoungeError(f"Reaction must be one of: {', '.join(REACTIONS)}.")
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            self._require_present(c, user, lounge)
            if not lounge.current_discovery_id:
                raise LoungeError("There's no discovery on the table right now.")
            d = c.s.get(Discovery, lounge.current_discovery_id)
            seen = c.s.get(SeenDiscovery, (user.id, d.id))
            seen.reaction = reaction
            now = c.now()
            emit(c.s, EventType.DISCOVERY_REACTED, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, payload={"discovery_id": d.id, "reaction": reaction}, at=now)
            tag = (d.tags or ["oddities"])[0]
            lines: list[Utterance] = []
            if reaction in ("loved", "liked"):
                c.memory.store_fact(user, "likes", tag, 0.75 if reaction == "loved" else 0.65, f"you {reaction} “{d.title}”", lounge_id=lounge.id)
            else:
                c.memory.store_fact(user, "dislikes", tag, 0.5, f"you were lukewarm on “{d.title}”", lounge_id=lounge.id)
            if reaction == "loved" and not any(p.content == tag for p in c.memory.open_promises(user)):
                c.memory.store_fact(user, "promise", tag, 1.0, f"Pip promised after you loved “{d.title}”", agent_key=PIP.key, lounge_id=lounge.id)
                plan = self._plan(c, user, lounge, "aside", d)
                u = c.gallery.single_line(
                    plan, PIP, "promise",
                    f"They loved it. Promise to keep an eye out for more {tag} finds for them.",
                    {"tag": tag, "user_name": c.memory.greeting_name(user)[0]},
                )
                if u:
                    lines.append(u)
            return self._result(c, user, lounge, lines, extra={"reaction": reaction})

    # ------------------------------------------------------------------ make it yours (free, no quests)
    def customize(self, handle: str, theme: str | None = None, mode: str | None = None, seat: str | None = None) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            now = c.now()
            changed = []
            if theme is not None:
                if theme not in THEMES:
                    raise LoungeError(f"Theme must be one of: {', '.join(THEMES)}.")
                lounge.theme = theme
                emit(c.s, EventType.LOUNGE_THEME, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, payload={"theme": theme}, at=now)
                changed.append(f"setting → {THEMES[theme]['name']}")
            if mode is not None:
                if mode not in MODES:
                    raise LoungeError(f"Mode must be one of: {', '.join(MODES)}.")
                lounge.mode = mode
                emit(c.s, EventType.LOUNGE_MODE, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, payload={"mode": mode}, at=now)
                changed.append(f"mode → {mode}")
            if seat is not None:
                lounge.favorite_seat = clean_text(seat, 120)
                emit(c.s, EventType.SEAT_CHOSEN, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, payload={"seat": lounge.favorite_seat}, at=now)
                changed.append(f"your spot → {lounge.favorite_seat}")
            touch(c, owner_presence(c, lounge))
            return {"changed": changed, "place": self._place(c, lounge), "notices": take_notices(c, user),
                    "narration": ("Done: " + "; ".join(changed) + ".") if changed else "Nothing changed."}

    def pin_to_wall(self, handle: str, discovery_id: int | None = None, label: str | None = None, spot: str | None = None) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            now = c.now()
            t = theme_info(lounge)
            spot = clean_text(spot, 120) if spot else t["spots"][0]
            d = None
            if discovery_id is None and label is None:
                if not lounge.current_discovery_id:
                    raise LoungeError("Nothing on the table to pin. Give a discovery id or a label for a keepsake.")
                discovery_id = lounge.current_discovery_id
            if discovery_id is not None:
                if c.s.get(SeenDiscovery, (user.id, discovery_id)) is None:
                    raise LoungeError("You can only pin discoveries you've seen here.")
                d = c.s.get(Discovery, discovery_id)
            dec = Decoration(
                lounge_id=lounge.id,
                label=clean_text(label, 200) if label else d.title,
                spot=spot,
                kind="discovery_pin" if d else "keepsake",
                discovery_id=d.id if d else None,
                placed_by_user_id=user.id,
                created_at=now,
            )
            c.s.add(dec)
            c.s.flush()
            emit(c.s, EventType.DECORATED, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, payload={"decoration_id": dec.id}, at=now)
            touch(c, owner_presence(c, lounge))
            return {"pinned": {"id": dec.id, "label": dec.label, "spot": dec.spot}, "place": self._place(c, lounge),
                    "notices": take_notices(c, user), "narration": f"Pinned “{dec.label}” {dec.spot}. It'll be there next time."}

    def take_down(self, handle: str, decoration_id: int | None = None) -> dict:
        """Undo: remove one wall item (default: the last thing you put up). Owners may remove guests' pins too."""
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            q = select(Decoration).where(Decoration.lounge_id == lounge.id, Decoration.removed_at.is_(None))
            if decoration_id is not None:
                dec = c.s.scalar(q.where(Decoration.id == decoration_id))
            else:
                dec = c.s.scalar(q.where(Decoration.placed_by_user_id == user.id).order_by(Decoration.created_at.desc(), Decoration.id.desc()))
            if dec is None:
                raise LoungeError("Nothing to take down.")
            dec.removed_at = c.now()
            emit(c.s, EventType.DECORATION_UNDONE, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, payload={"decoration_id": dec.id}, at=c.now())
            return {"removed": dec.label, "place": self._place(c, lounge), "narration": f"Took down “{dec.label}”."}

    # ------------------------------------------------------------------ state & leaving
    def state(self, handle: str) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            vips = c.s.scalars(select(VipRelationship).where(VipRelationship.owner_id == user.id)).all()
            knocks = c.s.scalars(select(Knock).where(Knock.lounge_id == lounge.id, Knock.status == "pending")).all()
            return {
                "narration": self._scene(c, lounge),
                "place": self._place(c, lounge),
                "here_now": self._here(c, lounge),
                "you_are_here": owner_presence(c, lounge) is not None,
                "vips": [{"label": v.label, "name": v.display_name, "status": v.status} for v in vips],
                "pending_knocks": [{"knock_id": k.id, "from": c.s.get(VipRelationship, k.vip_relationship_id).display_name} for k in knocks],
                "notices": take_notices(c, user),
            }

    def catchup(self, handle: str) -> dict:
        """Peek at what happened since you were last here, without entering."""
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            items = build_catchup(c, user, lounge, user.last_seen_at)
            text = "\n".join(f"- {i['text']}" for i in items) if items else "Nothing new since you were last here. Quiet's allowed."
            return {"catch_up": items, "narration": text}

    def leave(self, handle: str) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            now = c.now()
            p = owner_presence(c, lounge)
            lines: list[Utterance] = []
            if p is not None:
                plan = self._plan(c, user, lounge, "aside", None)
                u = c.gallery.single_line(plan, HOST, "farewell", "They're heading off. Say a brief, warm goodbye.", {"user_name": c.memory.greeting_name(user)[0]})
                if u:
                    lines.append(u)
                p.left_at = now
            user.last_visit_ended_at = now
            user.last_seen_at = now
            emit(c.s, EventType.VISIT_ENDED, actor_type="human_owner", actor_id=user.handle, lounge_id=lounge.id, at=now)
            c.memory.consolidate(lounge)
            return {"narration": narrate(lines) if lines else "See you next time.", "conversation": line_dicts(lines)}

    # ------------------------------------------------------------------ memory controls (§3.16)
    def remember(self, handle: str) -> dict:
        with self.app.ctx() as c:
            user, lounge = self._start(c, handle)
            thr = self.app.settings.fact_hedge_threshold
            facts = [
                {
                    "id": f.id,
                    "kind": f.kind,
                    "content": f.content,
                    "confidence": round(f.confidence, 2),
                    "unsure": f.confidence < thr,
                    "source": f.source,
                    **({"by": REGULARS[f.agent_key].name, "fulfilled": f.fulfilled_at is not None} if f.kind == "promise" and f.agent_key in REGULARS else {}),
                }
                for f in c.memory.active_facts(user)
            ]
            rels = c.s.scalars(
                select(AgentMemory).where(AgentMemory.lounge_id == lounge.id, AgentMemory.about_user_id == user.id, AgentMemory.retired_at.is_(None))
            ).all()
            by_regular: dict[str, list[str]] = {}
            for m in rels:
                by_regular.setdefault(REGULARS[m.agent_key].name, []).append(m.content)
            lines = [f"- [{f['id']}] {f['kind']}: {f['content']}{' (unsure)' if f['unsure'] else ''} — {f['source']}" for f in facts]
            return {
                "facts": facts,
                "regulars_memories_of_you": by_regular,
                "narration": ("Here's what the regulars remember about you (ask to forget any by id):\n" + "\n".join(lines)) if lines else "The regulars don't know anything about you yet.",
            }

    def forget(self, handle: str, fact_id: int) -> dict:
        with self.app.ctx() as c:
            user, _lounge = self._start(c, handle)
            f = c.memory.forget(user, fact_id)
            if f is None:
                raise LoungeError("No such memory about you.")
            return {"forgotten": {"id": f.id, "kind": f.kind, "content": f.content}, "narration": f"Forgotten: {f.content}. It won't come up again."}

    def facts_raw(self, handle: str) -> list[UserFact]:  # test helper
        with self.app.ctx() as c:
            user, _ = self._start(c, handle)
            return c.memory.active_facts(user)
