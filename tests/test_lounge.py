"""Pillar 1 (something interesting when you arrive) and the free personalisation."""

import pytest
from sqlalchemy import select

from voidgrid.common import LoungeError
from voidgrid.models import Discovery, User


def test_first_visit_is_complete_without_replying(app):
    r = app.lounge().enter("sam")
    convo = r["conversation"]
    assert convo[0]["speaker"] == "Wren"  # only the host greets
    assert sum(1 for line in convo if line["speaker"] == "Wren") == 1
    assert all(line["speaker_type"] == "bot" for line in convo)
    assert all("AI regular" in line["label"] for line in convo)
    commentators = {line["speaker"] for line in convo[1:]}
    assert len(commentators) >= 2  # a real exchange, not a monologue
    assert r["discovery"]["url"].startswith("https://")
    assert "No need to reply" in r["narration"]
    # leaving immediately is fine
    assert "Night" in app.lounge().leave("sam")["narration"]


def test_regulars_reply_to_each_other_not_round_robin(app, clock):
    L = app.lounge()
    orders = set()
    for i in range(6):
        r = L.enter(f"user{i}")
        speakers = tuple(line["speaker"] for line in r["conversation"][1:])
        orders.add(speakers)
        # consecutive lines are never the same regular
        assert all(a != b for a, b in zip(speakers, speakers[1:]))
        replies = [line for line in r["conversation"][2:]]
        assert any(prev["speaker"] in line["text"] for prev, line in zip(r["conversation"][1:], replies))
    assert len(orders) > 1


def test_discoveries_never_repeat_then_empty_bar(app, clock):
    L = app.lounge()
    with app.ctx() as c:
        total = len(c.s.scalars(select(Discovery)).all())
    seen = []
    for _ in range(total):
        r = L.enter("sam")
        seen.append(r["discovery"]["id"])
        L.leave("sam")
        clock.advance(hours=3)
    assert len(seen) == len(set(seen)) == total
    r = L.enter("sam")
    assert r["discovery"] is None
    assert "quiet" in r["conversation"][0]["text"].lower()
    for line in r["conversation"][1:]:  # callbacks or labelled fiction, never invented news
        assert line["text"].startswith("Remember") or "update nobody asked for" in line["text"]


def test_seat_theme_and_wall_persist_across_restart(make_app, clock):
    app1 = make_app()
    L = app1.lounge()
    L.customize("sam", theme="library", seat="the window seat", mode="quiet")
    L.enter("sam")
    pinned = L.pin_to_wall("sam", spot="the map wall")["pinned"]
    L.pin_to_wall("sam", label="a pressed flower")
    L.leave("sam")
    app1.dispose()

    app2 = make_app()  # simulated restart, same database
    clock.advance(days=1)
    st = app2.lounge().state("sam")
    assert st["place"]["theme"] == "library"
    assert st["place"]["mode"] == "quiet"
    assert st["place"]["favorite_seat"] == "the window seat"
    labels = [w["label"] for w in st["place"]["wall"]]
    assert pinned["label"] in labels and "a pressed flower" in labels
    # undo is free too
    app2.lounge().take_down("sam")
    labels = [w["label"] for w in app2.lounge().state("sam")["place"]["wall"]]
    assert "a pressed flower" not in labels


def test_quiet_mode_is_shorter(app):
    L = app.lounge()
    L.customize("quiet", mode="quiet")
    quiet = L.enter("quiet")["conversation"]
    chatty = L.enter("chatty")["conversation"]
    assert len(quiet) <= 3 < len(chatty) + 1


def test_catchup_is_truthful_when_nothing_happened(app, clock):
    L = app.lounge()
    L.enter("sam")
    L.leave("sam")
    clock.advance(days=2)
    assert L.catchup("sam")["catch_up"] == []
    r = L.enter("sam")
    assert r["catch_up"] == []
    assert "while you were out" not in r["conversation"][0]["text"].lower()


def test_cannot_pin_unseen_discovery(app):
    L = app.lounge()
    L.enter("sam")
    with app.ctx() as c:
        sam = c.s.scalar(select(User).where(User.handle == "sam"))
        from voidgrid.models import SeenDiscovery

        seen = {s.discovery_id for s in c.s.scalars(select(SeenDiscovery).where(SeenDiscovery.user_id == sam.id))}
        unseen = c.s.scalar(select(Discovery).where(Discovery.id.not_in(seen)))
    with pytest.raises(LoungeError):
        L.pin_to_wall("sam", discovery_id=unseen.id)


def test_must_be_present_to_listen(app):
    with pytest.raises(LoungeError):
        app.lounge().listen("nobody")


def test_listen_continues_the_conversation(app):
    L = app.lounge()
    L.enter("sam")
    more = L.listen("sam")["conversation"]
    assert more and all(line["speaker"] != "Wren" for line in more)
    assert not any(line["text"].startswith("Wait, wait") for line in more)  # replies, not fresh reactions


def test_daily_turn_budget_is_enforced(make_app):
    app = make_app(daily_turn_budget_per_lounge=3)
    r = app.lounge().enter("sam")
    assert len(r["conversation"]) <= 3
