"""Durable state. The backend is authoritative: LLM text never mutates these rows directly (spec §3.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Naive UTC timestamps keep SQLite and PostgreSQL behaviour identical."""
    return datetime.now(UTC).replace(tzinfo=None)


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON, list[str]: JSON, list[int]: JSON}


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    handle: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_visit_started_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_visit_ended_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)  # catch-ups cover events after this

    lounge: Mapped[Lounge | None] = relationship(back_populates="owner", uselist=False)


class Lounge(Base):
    __tablename__ = "lounges"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    theme: Mapped[str] = mapped_column(String(40), default="neighborhood_bar")
    mode: Mapped[str] = mapped_column(String(20), default="chatty")  # quiet | chatty | explore
    favorite_seat: Mapped[str | None] = mapped_column(String(120))
    join_policy: Mapped[str] = mapped_column(String(20), default="private")  # open | knock | private
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    current_discovery_id: Mapped[int | None] = mapped_column(ForeignKey("discoveries.id"))

    owner: Mapped[User] = relationship(back_populates="lounge")


class SourceRights(Base):
    """Per-source rights policy (spec §3.2). Anything not explicitly granted is denied."""

    __tablename__ = "source_rights"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(String(64), unique=True)
    rights_holder: Mapped[str] = mapped_column(String(200))
    license: Mapped[str] = mapped_column(String(200))
    attribution: Mapped[str] = mapped_column(Text, default="")
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified")
    review_date: Mapped[datetime | None] = mapped_column(DateTime)
    link: Mapped[bool] = mapped_column(Boolean, default=False)
    read_metadata: Mapped[bool] = mapped_column(Boolean, default=False)
    index_metadata: Mapped[bool] = mapped_column(Boolean, default=False)
    download_or_store_media: Mapped[bool] = mapped_column(Boolean, default=False)
    analyze_audio_video: Mapped[bool] = mapped_column(Boolean, default=False)
    use_captions_or_transcripts: Mapped[bool] = mapped_column(Boolean, default=False)
    embed_or_play: Mapped[bool] = mapped_column(Boolean, default=False)
    redistribute_or_clip: Mapped[bool] = mapped_column(Boolean, default=False)
    translate_or_create_derivatives: Mapped[bool] = mapped_column(Boolean, default=False)
    share_generated_commentary: Mapped[bool] = mapped_column(Boolean, default=False)


class Discovery(Base):
    __tablename__ = "discoveries"
    __table_args__ = (UniqueConstraint("source_key", "external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_key: Mapped[str] = mapped_column(ForeignKey("source_rights.source_key"))
    external_id: Mapped[str] = mapped_column(String(200))
    title: Mapped[str] = mapped_column(String(300))
    summary: Mapped[str] = mapped_column(Text)
    canonical_url: Mapped[str] = mapped_column(String(500))
    kind: Mapped[str] = mapped_column(String(20), default="article")  # article | video | fact
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    # What the system actually accessed (spec §3.2): metadata_only | transcript | sampled_frames | full_video | human_review
    analysis_depth: Mapped[str] = mapped_column(String(30), default="metadata_only")
    label: Mapped[str] = mapped_column(String(20), default="factual")  # factual | hypothetical | fictional
    is_fixture: Mapped[bool] = mapped_column(Boolean, default=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    rights: Mapped[SourceRights] = relationship()


class SeenDiscovery(Base):
    __tablename__ = "seen_discoveries"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    discovery_id: Mapped[int] = mapped_column(ForeignKey("discoveries.id"), primary_key=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    reaction: Mapped[str | None] = mapped_column(String(20))  # loved | liked | meh


class Decoration(Base):
    __tablename__ = "decorations"

    id: Mapped[int] = mapped_column(primary_key=True)
    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), index=True)
    label: Mapped[str] = mapped_column(String(200))
    spot: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(30), default="keepsake")  # discovery_pin | keepsake | note_card
    discovery_id: Mapped[int | None] = mapped_column(ForeignKey("discoveries.id"))
    placed_by_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    placed_by_vip_id: Mapped[int | None] = mapped_column(ForeignKey("vip_relationships.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    removed_at: Mapped[datetime | None] = mapped_column(DateTime)


class Event(Base):
    """Typed, append-only event log. Catch-ups are built only from these rows."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[str] = mapped_column(String(60), index=True)
    lounge_id: Mapped[int | None] = mapped_column(ForeignKey("lounges.id"), index=True)
    actor_type: Mapped[str] = mapped_column(String(30))  # human_owner | human_vip | bot | system
    actor_id: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Exchange(Base):
    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(primary_key=True)
    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), index=True)
    discovery_id: Mapped[int | None] = mapped_column(ForeignKey("discoveries.id"))
    kind: Mapped[str] = mapped_column(String(30))  # arrival | listen | reply | vip_greeting | empty_bar
    vip_relationship_id: Mapped[int | None] = mapped_column(ForeignKey("vip_relationships.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Utterance(Base):
    """The room-visible timeline. Every line carries an explicit human/bot speaker type."""

    __tablename__ = "utterances"

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange_id: Mapped[int] = mapped_column(ForeignKey("exchanges.id"), index=True)
    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), index=True)
    speaker_type: Mapped[str] = mapped_column(String(30))  # bot | human_owner | human_vip
    speaker_key: Mapped[str] = mapped_column(String(64))
    speaker_name: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class UserFact(Base):
    """Durable facts about a user (spec §3.16). Bypass the episodic budget; carry confidence + provenance."""

    __tablename__ = "user_facts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))  # name | likes | dislikes | promise | moment
    content: Mapped[str] = mapped_column(String(300))
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    source: Mapped[str] = mapped_column(String(200))  # human-readable provenance
    source_utterance_id: Mapped[int | None] = mapped_column(ForeignKey("utterances.id"))
    agent_key: Mapped[str | None] = mapped_column(String(32))  # who made a promise / who noticed it
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime)


class AgentMemory(Base):
    """A regular's private memory (spec §3.7). Each agent keeps its own interpretation."""

    __tablename__ = "agent_memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    agent_key: Mapped[str] = mapped_column(String(32), index=True)
    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), index=True)
    layer: Mapped[str] = mapped_column(String(20))  # episodic | relationship
    about_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    about_agent_key: Mapped[str | None] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    stats: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    salience: Mapped[float] = mapped_column(Float, default=0.0)
    source_utterance_ids: Mapped[list[int]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    retired_at: Mapped[datetime | None] = mapped_column(DateTime)


class VipRelationship(Base):
    __tablename__ = "vip_relationships"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vip_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    label: Mapped[str] = mapped_column(String(60))  # how the owner refers to them, e.g. "sister"
    display_name: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(20), default="invited")  # invited | active | revoked
    invite_code: Mapped[str] = mapped_column(String(40), unique=True)
    link_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    can_drop_in: Mapped[bool] = mapped_column(Boolean, default=True)
    can_leave_note: Mapped[bool] = mapped_column(Boolean, default=True)
    can_pin_to_wall: Mapped[bool] = mapped_column(Boolean, default=True)
    share_visit_with_owner: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)


class Presence(Base):
    """One row per visit. Open rows (left_at is NULL) are who is in the room right now."""

    __tablename__ = "presence"

    id: Mapped[int] = mapped_column(primary_key=True)
    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    vip_relationship_id: Mapped[int | None] = mapped_column(ForeignKey("vip_relationships.id"))
    role: Mapped[str] = mapped_column(String(20))  # owner | vip
    display_name: Mapped[str] = mapped_column(String(60))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    left_at: Mapped[datetime | None] = mapped_column(DateTime)


class Knock(Base):
    __tablename__ = "knocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), index=True)
    vip_relationship_id: Mapped[int] = mapped_column(ForeignKey("vip_relationships.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | admitted | declined
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), index=True)
    vip_relationship_id: Mapped[int] = mapped_column(ForeignKey("vip_relationships.id"))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)


class Notice(Base):
    """Things to tell a person on their next tool call (MCP clients usually can't receive pushes)."""

    __tablename__ = "notices"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime)


class TurnBudget(Base):
    __tablename__ = "turn_budgets"

    lounge_id: Mapped[int] = mapped_column(ForeignKey("lounges.id"), primary_key=True)
    day: Mapped[str] = mapped_column(String(10), primary_key=True)
    turns_used: Mapped[int] = mapped_column(Integer, default=0)


class VipLinkUse(Base):
    __tablename__ = "vip_link_uses"

    id: Mapped[int] = mapped_column(primary_key=True)
    vip_relationship_id: Mapped[int] = mapped_column(ForeignKey("vip_relationships.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
