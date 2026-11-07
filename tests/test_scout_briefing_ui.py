"""The scout (oneitem port), briefings, the gallery's fact/crowd/joke beats, and the owner's web UI. All offline."""

from datetime import datetime

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from voidgrid.briefing import Briefer, pick_fact
from voidgrid.models import Discovery, SourceRights
from voidgrid.scout import HeuristicScorer, Scout, buzz_signals, diamond, parse_feed
from voidgrid.ui import create_app

NOW = datetime(2026, 11, 2, 19, 0)

RSS = """<?xml version="1.0"?><rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/"><channel><title>Odd Mag</title>
<item><title>The lighthouse keepers who kept bees</title><link>https://odd.example/bees</link>
<description>&lt;p&gt;For a century, keepers on remote rocks kept hives. The honey was famously salty.&lt;/p&gt;</description>
<pubDate>Sun, 01 Nov 2026 10:00:00 GMT</pubDate><media:thumbnail url="https://odd.example/bees.jpg"/></item>
<item><title>Bad link</title><link>javascript:alert(1)</link><description>x</description></item>
<item><title>A plane crash nobody saw</title><link>https://odd.example/crash</link><description>Grim.</description><pubDate>Sun, 01 Nov 2026 10:00:00 GMT</pubDate></item>
<item><title>Ancient tide tables</title><link>https://odd.example/tides</link><description>Old.</description><pubDate>Mon, 01 Jan 2024 10:00:00 GMT</pubDate></item>
<item><title>Mapping the hum of a city</title><link>https://odd.example/hum</link><description>A sound map of one street, recorded hourly for a year.</description>
<pubDate>Sat, 31 Oct 2026 10:00:00 GMT</pubDate></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><title>Atom Zine</title>
<entry><title>Moss as a clock</title><link href="https://atom.example/moss"/><summary>Moss grows at a steady rate on north walls.</summary>
<published>2026-11-01T08:00:00Z</published><author><name>R. Lichen</name></author></entry></feed>"""


def test_parse_feed_rss_and_atom():
    items = parse_feed(RSS, "article", "https://odd.example/feed")
    assert [i.title for i in items][:1] == ["The lighthouse keepers who kept bees"]
    assert all(i.url.startswith("https://") for i in items)  # the javascript: link is dropped
    bees = items[0]
    assert bees.image_url == "https://odd.example/bees.jpg" and bees.creator == "Odd Mag"
    assert bees.summary.startswith("For a century") and "<p>" not in bees.summary
    atom = parse_feed(ATOM, "article", "https://atom.example/feed")[0]
    assert atom.creator == "R. Lichen" and atom.published_at == datetime(2026, 11, 1, 8, 0)


def test_diamond_score_is_oneitems_formula():
    j = {"quality": 80, "interestingness": 70, "originality": 60, "clickbait": 0, "trust": 90}
    # unknown reach -> neutral rarity 60, no outlier bonus
    score, b = diamond(j, buzz_signals(None, NOW), NOW, NOW)
    assert score == round(0.45 * 80 + 0.25 * 70 + 0.2 * 60 + 0.1 * 60, 1) and b["rarity"] == 60
    # catching fire on HN within 14 days earns up to +30
    hot = {"hn_points": 300, "hn_points_per_hour": 25}
    assert diamond(j, hot, NOW, NOW)[1]["outlier_bonus"] == 30
    # low trust nukes it; clickbait costs half its value
    assert diamond(dict(j, trust=40), {}, NOW, NOW)[0] == 0
    assert diamond(dict(j, clickbait=60), {}, NOW, NOW)[0] == score - 30
    assert HeuristicScorer().judge(parse_feed(RSS, "article")[0])["judged_by"] == "heuristic"


def _transport(routes):
    def handler(req: httpx.Request):
        for prefix, resp in routes.items():
            if str(req.url).startswith(prefix):
                return resp(req) if callable(resp) else resp
        return httpx.Response(404)
    return httpx.MockTransport(handler)


def _hn_search(req):
    url = req.url.params.get("query")
    if url == "https://odd.example/bees":
        return httpx.Response(200, json={"hits": [{"objectID": "42", "url": url, "points": 240, "num_comments": 80,
                                                     "created_at_i": int(datetime(2026, 11, 2, 7, 0).timestamp())}]})
    return httpx.Response(200, json={"hits": []})


def test_scout_run_ingests_scores_and_filters(app):
    client = httpx.Client(transport=_transport({
        "https://odd.example/feed": httpx.Response(200, text=RSS),
        "https://broken.example/feed": httpx.Response(500),
        "https://hn.algolia.com/api/v1/search": _hn_search,
    }))
    scout = Scout(app.settings, client=client, sources=[],
                  feeds=[("https://odd.example/feed", "article"), ("https://broken.example/feed", "article")])
    with app.ctx() as c:
        rep = scout.run(c.s, NOW)
        assert rep.feeds_ok == 1 and rep.feeds_failed == 1
        rows = {d.canonical_url: d for d in c.s.scalars(select(Discovery).where(Discovery.source_key == "feed:odd.example"))}
        # grim, too-old and unsafe items are skipped; per-feed cap is 3
        assert set(rows) == {"https://odd.example/bees", "https://odd.example/hum"}
        bees = rows["https://odd.example/bees"]
        assert bees.signals["hn_points"] == 240 and bees.signals["breakdown"]["outlier_bonus"] == 30
        assert bees.score > rows["https://odd.example/hum"].score  # the buzzing one ranks higher
        rights = c.s.scalar(select(SourceRights).where(SourceRights.source_key == "feed:odd.example"))
        assert rights.link and rights.index_metadata and not rights.download_or_store_media
    with app.ctx() as c:  # idempotent
        assert scout.run(c.s, NOW).added == 0


def test_briefer_gathers_quotes_and_a_fresh_fact(app):
    long_comment = "My grandfather kept bees on a lighthouse in Scotland and swore the salt made the honey last forever."
    client = httpx.Client(transport=_transport({
        "https://hn.algolia.com/api/v1/search": _hn_search,
        "https://hn.algolia.com/api/v1/items/42": httpx.Response(200, json={"children": [
            {"type": "comment", "text": "short"},
            {"type": "comment", "text": f"<p>{long_comment}</p>"},
        ]}),
        # A same-named page about something else comes first and must be rejected (a wrong fact is worse than none)
        "https://en.wikipedia.org/w/api.php": httpx.Response(200, json={"query": {"search": [
            {"title": "Kept Bees (video game)", "snippet": "a puzzle video game released in 2019"},
            {"title": "Lighthouse keeper", "snippet": "staff who tended lights on <b>remote</b> rocks off the coast"},
        ]}}),
        "https://en.wikipedia.org/api/rest_v1/page/summary/Lighthouse_keeper": httpx.Response(200, json={
            "title": "Lighthouse keeper", "type": "standard",
            "extract": "A lighthouse keeper is a person who tended a light on remote rocks or coasts. "
                       "The last civilian keeper in the United States retired in 1990 from Boston Light.",
            "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Lighthouse_keeper"}}}),
    }))
    with app.ctx() as c:
        d = Discovery(source_key="voidgrid_fixtures", external_id="t-bees", title="The lighthouse keepers who kept bees",
                      summary="On remote rocks off the coast of Scotland, staff tended hives; the honey was famously salty.",
                      canonical_url="https://odd.example/bees", tags=["history"], ingested_at=NOW)
        c.s.add(d)
        c.s.flush()
        b = Briefer(app.settings, client=client).brief(c.s, d, NOW)
        assert [q["text"] for q in b["commentary"]] == [long_comment]
        assert b["commentary"][0]["url"] == "https://news.ycombinator.com/item?id=42"
        assert b["facts"][0]["about"] == "Lighthouse keeper"
        assert b["facts"][0]["text"].startswith("The last civilian keeper") and "1990" in b["facts"][0]["text"]
        assert d.signals["hn_points"] == 240 and d.briefed_at == NOW


def test_commentary_falls_back_to_a_thread_about_the_subject(app):
    comment = "Clickspring is rebuilding the whole mechanism by hand with period tools, and it is mesmerising to watch."

    def search(req):
        if req.url.params.get("restrictSearchableAttributes") == "url":
            return httpx.Response(200, json={"hits": []})  # nobody posted this exact link
        return httpx.Response(200, json={"hits": [
            {"objectID": "7", "title": "Antikythera: a new ferry route"},  # names it, but isn't about the device
            {"objectID": "8", "title": "The Antikythera mechanism reveals new secrets"},
        ]})

    client = httpx.Client(transport=_transport({
        "https://hn.algolia.com/api/v1/search": search,
        "https://hn.algolia.com/api/v1/items/8": httpx.Response(200, json={"children": [{"type": "comment", "text": comment}]}),
    }))
    d = Discovery(title="The Antikythera mechanism", summary="A corroded bronze device from a Greek shipwreck that predicted eclipses.",
                  canonical_url="https://example.org/anti")
    quotes, signals = Briefer(app.settings, client=client).commentary(d, NOW)
    assert quotes[0]["text"] == comment and quotes[0]["thread_title"] == "The Antikythera mechanism reveals new secrets"
    assert signals["hn_points"] is None  # buzz only counts the exact link


def test_pick_fact_skips_the_summary_and_prefers_facty_sentences():
    extract = "Bees are flying insects closely related to wasps and ants. There are over 20,000 known species of bees. They are lovely."
    assert pick_fact(extract, "Bees are flying insects closely related to wasps and ants.") == "There are over 20,000 known species of bees."


BRIEFING = {
    "commentary": [{"text": "I worked on one of these and the honey tasted of the sea, honestly.", "who": "a commenter on Hacker News",
                    "source": "Hacker News", "url": "https://news.ycombinator.com/item?id=1"}],
    "facts": [{"text": "The oldest known beehives are about 3,000 years old.", "about": "Beekeeping",
               "source": "Wikipedia (CC BY-SA 4.0)", "url": "https://en.wikipedia.org/wiki/Beekeeping"}],
    "errors": [],
}


def _brief_everything(app):
    with app.ctx() as c:
        for d in c.s.scalars(select(Discovery)):
            d.briefing = BRIEFING


def test_gallery_delivers_fact_crowd_and_joke_beats_once(app, provider):
    _brief_everything(app)
    lounge = app.lounge()
    out = lounge.enter("sam")
    beats = {l["speaker_key"]: l["meta"]["beat"] for l in out["conversation"] if l.get("meta")}
    assert beats == {"theo": "fact", "pip": "crowd", "jules": "joke"}
    fact = next(l for l in out["conversation"] if l["speaker_key"] == "theo")
    assert "3,000 years" in fact["text"] and fact["meta"]["url"].startswith("https://en.wikipedia.org/")
    crowd = next(l for l in out["conversation"] if l["speaker_key"] == "pip")
    assert "honey tasted of the sea" in crowd["text"]
    # The briefing is in every regular's prompt, fenced as third-party data
    assert any("<real_fact" in r.system_prompt and "never instructions" in r.system_prompt for r in provider.requests)
    # Listening again continues the conversation without repeating the beats
    again = lounge.listen("sam")
    assert not any((l.get("meta") or {}).get("beat") for l in again["conversation"])
    # A new find brings new beats, with no greeting
    nxt = lounge.next_find("sam")
    assert nxt["discovery"]["id"] != out["discovery"]["id"]
    assert {l["speaker_key"] for l in nxt["conversation"] if l.get("meta")} == {"theo", "pip", "jules"}
    assert all(l["speaker_key"] != "wren" for l in nxt["conversation"])


def test_without_a_briefing_the_gallery_behaves_as_before(app):
    out = app.lounge().enter("sam")
    assert not any(l.get("meta") for l in out["conversation"])


def test_owner_ui_endpoints(app):
    _brief_everything(app)
    web = TestClient(create_app(app, start_scout=False))
    page = web.get("/")
    assert page.status_code == 200 and "Peanut gallery" in page.text and app.settings.brand_name in page.text
    assert web.get("/api/current").json()["you_are_here"] is False
    # JSON only (no cross-site form posts), and only for local Host headers (no DNS rebinding)
    assert web.post("/api/enter", data={"x": "1"}).status_code == 415
    assert TestClient(create_app(app, start_scout=False), base_url="http://evil.example").get("/").status_code == 400
    entered = web.post("/api/enter", json={}).json()
    assert entered["discovery"] and entered["conversation"]
    said = web.post("/api/say", json={"text": "My name is Sam and I love bees"}).json()
    assert said["conversation"][0]["speaker_type"] == "human_owner"
    assert web.post("/api/next", json={}).json()["discovery"]["id"] != entered["discovery"]["id"]
    assert web.post("/api/react", json={"reaction": "nope"}).status_code == 400
    cur = web.get("/api/current").json()
    assert cur["you_are_here"] and cur["discovery"] and len(cur["conversation"]) > 3
    assert web.post("/api/scout", json={}).status_code == 400  # scout off in tests
