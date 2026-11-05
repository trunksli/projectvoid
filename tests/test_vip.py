"""Pillar 3: someone you love drops by, live or asynchronously (spec §3.13 B + B2)."""

import pytest

from voidgrid.common import LinkInactive, LoungeError


def _setup(app, policy="open"):
    L, V = app.lounge(), app.vip()
    L.enter("sam")
    inv = V.invite("sam", "sister", "Ana")
    V.accept("ana", inv["invite_code"])
    V.set_join_policy("sam", policy)
    return L, V, inv


def test_default_door_is_private(app):
    L, V = app.lounge(), app.vip()
    inv = V.invite("sam", "sister", "Ana")
    V.accept("ana", inv["invite_code"])
    r = V.drop_in("ana", "sam")
    assert r["status"] == "private"


def test_live_drop_in_is_visible_to_owner(app):
    L, V, _ = _setup(app)
    r = V.drop_in("ana", "sam")
    assert r["status"] == "joined"
    assert r["conversation"][0]["speaker"] == "Wren"
    nxt = L.listen("sam")
    assert any("Ana" in n and "walked in" in n for n in nxt["notices"])
    assert any(h["type"] == "human_vip" and h["name"] == "Ana" for h in nxt["here_now"])


def test_guest_never_sees_owner_private_memory(app, provider):
    L, V, _ = _setup(app)
    L.say("sam", "My name is Sam and I love octopuses")
    provider.requests.clear()
    V.drop_in("ana", "sam")
    V.say("ana", "sam", "Hi everyone!")
    for req in provider.requests:
        private = req.system_prompt.split("<your_private_memories>")[1].split("</your_private_memories>")[0]
        assert "octopuses" not in private and "name: Sam" not in private


def test_unapproved_person_is_denied(app):
    _setup(app)
    with pytest.raises(LoungeError):
        app.vip().drop_in("stranger", "sam")
    with pytest.raises(LoungeError):  # same message for a lounge that doesn't exist: no probing
        app.vip().drop_in("stranger", "nobody")


def test_knock_first(app):
    L, V, _ = _setup(app, policy="knock")
    r = V.drop_in("ana", "sam")
    assert r["status"] == "knocked"
    st = L.state("sam")
    assert st["pending_knocks"] and st["pending_knocks"][0]["from"] == "Ana"
    adm = V.answer_knock("sam", r["knock_id"], admit=True)
    assert adm["admitted"]
    assert any(h["name"] == "Ana" for h in L.state("sam")["here_now"])


def test_async_visit_note_and_pin_relayed_truthfully(app, clock):
    L, V, inv = _setup(app)
    L.leave("sam")
    clock.advance(days=1)
    V.drop_in("ana", "sam")
    V.say("ana", "sam", "Jules, be nice to Sam.")
    V.leave("ana", "sam")
    token = inv["vip_link"].rsplit("/", 1)[1]
    V.leave_note(None, None, "Call Mum on Sunday!", link_token=token)
    V.pin(None, None, label="a postcard from Lisbon", link_token=token)
    clock.advance(days=1)
    r = L.enter("sam")
    kinds = [i["type"] for i in r["catch_up"]]
    assert kinds.count("vip_visit") == 1 and "vip_note" in kinds and "vip_pin" in kinds
    text = " ".join(i["text"] for i in r["catch_up"])
    assert "Call Mum on Sunday!" in text and "a postcard from Lisbon" in text and "be nice to Sam" in text
    assert "Ana stopped by" in r["conversation"][0]["text"]
    assert any(w["label"] == "a postcard from Lisbon" for w in r["place"]["wall"])
    # nothing new happened since: the next catch-up is empty
    L.leave("sam")
    assert L.catchup("sam")["catch_up"] == []


def test_visit_chat_hidden_when_not_shared(app, clock):
    L, V, _ = _setup(app)
    with app.ctx() as c:
        from sqlalchemy import select

        from voidgrid.models import VipRelationship

        c.s.scalar(select(VipRelationship)).share_visit_with_owner = False
    L.leave("sam")
    clock.advance(hours=2)
    V.drop_in("ana", "sam")
    V.say("ana", "sam", "secret birthday plans")
    V.leave("ana", "sam")
    r = L.enter("sam")
    text = " ".join(i["text"] for i in r["catch_up"])
    assert "Ana" in text and "secret birthday" not in text


def test_revocation_takes_effect_everywhere(app):
    L, V, inv = _setup(app)
    V.drop_in("ana", "sam")
    V.revoke("sam", "sister")
    assert not any(h.get("name") == "Ana" for h in L.state("sam")["here_now"])
    with pytest.raises(LoungeError):
        V.drop_in("ana", "sam")
    with pytest.raises(LoungeError):
        V.leave_note("ana", "sam", "hi")
    token = inv["vip_link"].rsplit("/", 1)[1]
    with pytest.raises(LinkInactive):
        V.leave_note(None, None, "hi", link_token=token)
    with pytest.raises(LoungeError):
        V.accept("ana", inv["invite_code"])


def test_permissions_are_enforced(app):
    L, V = app.lounge(), app.vip()
    L.enter("sam")
    inv = V.invite("sam", "cousin", "Bo", can_pin_to_wall=False, can_drop_in=False)
    V.accept("bo", inv["invite_code"])
    V.set_join_policy("sam", "open")
    with pytest.raises(LoungeError):
        V.drop_in("bo", "sam")
    with pytest.raises(LoungeError):
        V.pin("bo", "sam", label="graffiti")
    assert V.leave_note("bo", "sam", "hello")["note_id"]


def test_cannot_accept_own_invite(app):
    inv = app.vip().invite("sam", "me", "Me")
    with pytest.raises(LoungeError):
        app.vip().accept("sam", inv["invite_code"])


def test_guest_can_only_pin_discoveries_shown_in_owner_lounge(app):
    L, V, inv = _setup(app)
    token = inv["vip_link"].rsplit("/", 1)[1]
    view = V.link_view(token)
    assert view["shareable"]
    with pytest.raises(LoungeError):
        V.pin(None, None, discovery_id=999999, link_token=token)
    ok = V.pin(None, None, discovery_id=view["shareable"][0]["id"], link_token=token)
    assert ok["pinned"]["label"] == view["shareable"][0]["title"]


def test_link_rate_limit(make_app):
    app = make_app(vip_link_actions_per_hour=2)
    L, V, inv = _setup(app)
    token = inv["vip_link"].rsplit("/", 1)[1]
    V.leave_note(None, None, "one", link_token=token)
    V.leave_note(None, None, "two", link_token=token)
    with pytest.raises(LoungeError):
        V.leave_note(None, None, "three", link_token=token)
