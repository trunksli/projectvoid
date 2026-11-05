"""Typed event contracts (spec §3.1). Event names are versioned by convention: add new names, never repurpose old ones."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Event, utcnow


class EventType:
    VISIT_STARTED = "lounge.visit_started"
    VISIT_ENDED = "lounge.visit_ended"
    DISCOVERY_INGESTED = "discovery.ingested"
    DISCOVERY_SHOWN = "discovery.shown"
    DISCOVERY_REACTED = "discovery.reacted"
    EXCHANGE = "bot.discussion_started"
    HUMAN_SPOKE = "human.spoke"
    LOUNGE_THEME = "lounge.theme_changed"
    LOUNGE_MODE = "lounge.mode_changed"
    SEAT_CHOSEN = "lounge.seat_chosen"
    DECORATED = "home.decorated"
    DECORATION_UNDONE = "home.decoration_undone"
    FACT_STORED = "memory.fact_stored"
    FACT_DELETED = "memory.fact_deleted"
    MEMORY_CONSOLIDATED = "bot.memory_consolidated"
    VIP_INVITED = "vip.invited"
    VIP_ACCEPTED = "vip.accepted"
    VIP_JOINED = "vip.joined"
    VIP_LEFT = "vip.left"
    VIP_KNOCKED = "vip.knocked"
    VIP_KNOCK_ANSWERED = "vip.knock_answered"
    VIP_DENIED = "vip.denied"
    VIP_NOTE = "vip.note_left"
    VIP_PINNED = "vip.pinned"
    VIP_SPOKE = "vip.spoke"
    VIP_REVOKED = "vip.access_revoked"
    JOIN_POLICY = "room.join_policy_changed"


def emit(
    session: Session,
    type_: str,
    *,
    actor_type: str,
    actor_id: str,
    lounge_id: int | None = None,
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    at=None,
) -> Event:
    """Append an event. Re-emitting with the same idempotency key returns the original row."""
    if idempotency_key:
        existing = session.scalar(select(Event).where(Event.idempotency_key == idempotency_key))
        if existing:
            return existing
    ev = Event(
        type=type_,
        lounge_id=lounge_id,
        actor_type=actor_type,
        actor_id=actor_id,
        payload=payload or {},
        idempotency_key=idempotency_key,
        created_at=at or utcnow(),
    )
    session.add(ev)
    session.flush()
    return ev
