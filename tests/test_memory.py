"""Pillar 2: the regulars remember you (spec §3.7 + §3.16)."""

from sqlalchemy import select

from voidgrid.memory import extract_facts
from voidgrid.models import AgentMemory, User, UserFact


def test_extract_facts():
    facts = extract_facts("Hi! My name is sam. I love octopuses, but I don't like jazz.")
    assert ("name", "Sam", 0.95) in facts
    assert any(k == "likes" and c == "octopuses" for k, c, _ in facts)
    assert any(k == "dislikes" and c == "jazz" for k, c, _ in facts)
    assert not any(k == "likes" and c == "jazz" for k, c, _ in facts)


def test_returning_user_greeted_by_name_after_restart(make_app, clock):
    app1 = make_app()
    app1.lounge().enter("sam")
    app1.lounge().say("sam", "Call me Sam. I love space stuff.")
    app1.lounge().leave("sam")
    app1.dispose()
    clock.advance(days=3)
    r = make_app().lounge().enter("sam")
    assert r["conversation"][0]["text"].startswith("Evening, Sam.")


def test_low_confidence_name_is_hedged_not_asserted(app):
    L = app.lounge()
    L.enter("sam")
    with app.ctx() as c:
        sam = c.s.scalar(select(User).where(User.handle == "sam"))
        c.memory.store_fact(sam, "name", "Samwise", 0.4, "overheard, not confirmed")
    greet = L.enter("sam")["conversation"][0]["text"]
    assert "Evening, Samwise." not in greet
    assert "isn't it?" in greet and "Samwise" in greet


def test_forgotten_fact_never_resurfaces(app, provider, clock):
    L = app.lounge()
    L.enter("sam")
    r = L.say("sam", "My name is Sam and I love octopuses")
    octo = next(f for f in r["remembered"] if f["content"] == "octopuses")
    L.forget("sam", octo["id"])
    assert all(f["content"] != "octopuses" for f in L.remember("sam")["facts"])
    provider.requests.clear()
    L.leave("sam")
    clock.advance(days=1)
    L.enter("sam")
    for req in provider.requests:
        assert "octopuses" not in req.system_prompt.split("<your_private_memories>")[1].split("</your_private_memories>")[0]


def test_user_facts_bypass_episodic_budget(app):
    L = app.lounge()
    L.enter("sam")
    for i in range(5):
        L.say("sam", f"I love topic{i} things")
    facts = [f for f in L.remember("sam")["facts"] if f["kind"] == "likes"]
    assert len(facts) == 5  # every stated taste kept, regardless of the 20% budget


def test_episodic_retention_is_selective(app):
    L = app.lounge()
    L.enter("sam")
    with app.ctx() as c:
        from voidgrid.models import Utterance

        n_lines = len(c.s.scalars(select(Utterance).where(Utterance.speaker_type == "bot", Utterance.speaker_key != "wren")).all())
        distinct = {m.source_utterance_ids[0] for m in c.s.scalars(select(AgentMemory).where(AgentMemory.layer == "episodic"))}
    assert 1 <= len(distinct) <= max(1, -(-n_lines // 5))  # ~20%, at least one


def test_each_regular_gets_only_its_own_memories(app, provider):
    L = app.lounge()
    L.enter("sam")
    L.listen("sam")
    with app.ctx() as c:
        mems = c.s.scalars(select(AgentMemory).where(AgentMemory.layer == "episodic")).all()
        by_agent = {}
        for m in mems:
            by_agent.setdefault(m.agent_key, []).append(m.content)
    assert len(by_agent) >= 2
    provider.requests.clear()
    L.listen("sam")
    for req in provider.requests:
        private = req.system_prompt.split("<your_private_memories>")[1].split("</your_private_memories>")[0]
        for other, contents in by_agent.items():
            if other == req.character.key:
                continue
            for content in contents:
                if content not in by_agent.get(req.character.key, []):
                    assert content not in private


def test_promise_is_made_and_kept(app, clock):
    L = app.lounge()
    first = L.enter("sam")
    tag = first["discovery"]["tags"][0]
    r = L.react("sam", "loved")
    assert r["conversation"] and r["conversation"][0]["speaker"] == "Pip"
    assert "promise" in r["conversation"][0]["text"].lower()
    L.leave("sam")
    clock.advance(days=1)
    nxt = L.enter("sam")
    assert tag in nxt["discovery"]["tags"]
    assert nxt["conversation"][1]["speaker"] == "Pip"
    assert "keep an eye out" in nxt["conversation"][1]["text"]
    with app.ctx() as c:
        p = c.s.scalar(select(UserFact).where(UserFact.kind == "promise"))
        assert p.fulfilled_at is not None


def test_relationships_evolve(app):
    L = app.lounge()
    for _ in range(3):
        L.enter("sam")
        L.listen("sam")
    with app.ctx() as c:
        rels = c.s.scalars(select(AgentMemory).where(AgentMemory.layer == "relationship", AgentMemory.about_agent_key.is_not(None))).all()
    assert rels
    assert max(r.stats["exchanges"] for r in rels) >= 2


def test_consolidation_caps_episodes(make_app):
    app = make_app(episodic_cap_per_agent=2)
    L = app.lounge()
    for i in range(6):
        L.enter(f"u{i}")
    L.leave("u0")
    with app.ctx() as c:
        for agent in ("theo", "jules", "pip"):
            live = c.s.scalars(select(AgentMemory).where(
                AgentMemory.agent_key == agent, AgentMemory.layer == "episodic", AgentMemory.retired_at.is_(None))).all()
            assert len(live) <= 2 * 6  # per lounge cap of 2, across 6 lounges
            per_lounge = {}
            for m in live:
                per_lounge[m.lounge_id] = per_lounge.get(m.lounge_id, 0) + 1
            owner_lounge = c.s.scalar(select(User).where(User.handle == "u0")).lounge.id
            assert per_lounge.get(owner_lounge, 0) <= 2
