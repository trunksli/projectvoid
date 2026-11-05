"""Shared helpers: identities, presence, notices, wall, and readable narration for text-only clients."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .app import Ctx
from .characters import REGULARS, THEMES
from .models import Decoration, Discovery, Lounge, Notice, Presence, User, Utterance, VipRelationship

PRESENCE_TIMEOUT = timedelta(hours=2)
_HANDLE_RE = re.compile(r"^[a-z0-9][a-z0-9_\-]{0,63}$")


class LoungeError(Exception):
    """A user-facing refusal (permissions, bad input). The message is safe to show."""


class LinkInactive(LoungeError):
    """A VIP link that was revoked or never existed."""


def clean_handle(handle: str) -> str:
    h = (handle or "").strip().lower()
    if not _HANDLE_RE.match(h):
        raise LoungeError("Handles are 1-64 characters: lowercase letters, digits, '-' or '_'.")
    return h


def clean_text(text: str, limit: int = 1000) -> str:
    t = (text or "").strip()
    if not t:
        raise LoungeError("That was empty.")
    return t[:limit]


def get_or_create_user(c: Ctx, handle: str) -> User:
    handle = clean_handle(handle)
    u = c.s.scalar(select(User).where(User.handle == handle))
    if u is None:
        try:
            with c.s.begin_nested():  # tolerate a concurrent create of the same handle
                u = User(handle=handle, created_at=c.now())
                c.s.add(u)
        except IntegrityError:
            u = c.s.scalar(select(User).where(User.handle == handle))
    return u


def find_user(c: Ctx, handle: str) -> User | None:
    return c.s.scalar(select(User).where(User.handle == clean_handle(handle)))


def get_or_create_lounge(c: Ctx, user: User) -> Lounge:
    lg = c.s.scalar(select(Lounge).where(Lounge.owner_id == user.id))
    if lg is None:
        lg = Lounge(owner_id=user.id, created_at=c.now())
        c.s.add(lg)
        c.s.flush()
    return lg


def open_presence(c: Ctx, lounge: Lounge) -> list[Presence]:
    """Who is in the room right now (open visits active within the timeout)."""
    cutoff = c.now() - PRESENCE_TIMEOUT
    rows = c.s.scalars(select(Presence).where(Presence.lounge_id == lounge.id, Presence.left_at.is_(None))).all()
    live = []
    for p in rows:
        if p.last_active_at < cutoff:
            p.left_at = p.last_active_at  # stale: they wandered off without saying goodbye
        else:
            live.append(p)
    return live


def owner_presence(c: Ctx, lounge: Lounge) -> Presence | None:
    return next((p for p in open_presence(c, lounge) if p.role == "owner"), None)


def vip_presence(c: Ctx, lounge: Lounge, rel: VipRelationship) -> Presence | None:
    return next((p for p in open_presence(c, lounge) if p.vip_relationship_id == rel.id), None)


def touch(c: Ctx, p: Presence | None) -> None:
    if p is not None:
        p.last_active_at = c.now()


def notify(c: Ctx, user_id: int | None, text: str) -> None:
    if user_id is not None:
        c.s.add(Notice(user_id=user_id, text=text, created_at=c.now()))


def take_notices(c: Ctx, user: User) -> list[str]:
    rows = c.s.scalars(
        select(Notice).where(Notice.user_id == user.id, Notice.delivered_at.is_(None)).order_by(Notice.created_at, Notice.id)
    ).all()
    for n in rows:
        n.delivered_at = c.now()
    return [n.text for n in rows]


def wall(c: Ctx, lounge: Lounge) -> list[dict]:
    rows = c.s.scalars(
        select(Decoration).where(Decoration.lounge_id == lounge.id, Decoration.removed_at.is_(None)).order_by(Decoration.created_at, Decoration.id)
    ).all()
    out = []
    for d in rows:
        if d.placed_by_vip_id:
            rel = c.s.get(VipRelationship, d.placed_by_vip_id)
            by = f"{rel.display_name} (your {rel.label})" if rel else "a guest"
        else:
            by = "you"
        item = {"id": d.id, "label": d.label, "spot": d.spot, "kind": d.kind, "placed_by": by}
        if d.discovery_id:
            disc = c.s.get(Discovery, d.discovery_id)
            item["url"] = disc.canonical_url if disc else None
        out.append(item)
    return out


def theme_info(lounge: Lounge) -> dict:
    return THEMES.get(lounge.theme, THEMES["neighborhood_bar"])


def when(dt: datetime, now: datetime) -> str:
    days = (now.date() - dt.date()).days
    if days <= 0:
        return "earlier today"
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"on {dt:%A}"
    return f"on {dt:%d %b}".replace(" 0", " ")


def speaker_label(u: Utterance, *, viewer: str = "owner") -> str:
    if u.speaker_type == "bot":
        role = REGULARS[u.speaker_key].role if u.speaker_key in REGULARS else "regular"
        return f"{u.speaker_name} (AI regular, {role})"
    if u.speaker_type == "human_owner":
        return "You" if viewer == "owner" else f"{u.speaker_name} (human, lounge owner)"
    return f"{u.speaker_name} (human, VIP guest)" if viewer == "owner" else "You"


def narrate(lines: list[Utterance], *, viewer: str = "owner") -> str:
    return "\n".join(f"{speaker_label(u, viewer=viewer)}: {u.text}" for u in lines)


def line_dicts(lines: list[Utterance], *, viewer: str = "owner") -> list[dict]:
    return [
        {"speaker": u.speaker_name, "speaker_type": u.speaker_type, "label": speaker_label(u, viewer=viewer), "text": u.text}
        for u in lines
    ]
