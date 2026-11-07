"""Watchable/readable media (films, TV, books, poems), the lineup of five, and playing a pick. All offline."""

from datetime import datetime

import httpx
from fastapi.testclient import TestClient
from sqlalchemy import select

from voidgrid.events import EventType
from voidgrid.media import archive_source, gutenberg_excerpt, gutenberg_source, player, poetry_source, teaser
from voidgrid.models import Discovery, Event
from voidgrid.scout import Scout
from voidgrid.ui import create_app

NOW = datetime(2026, 11, 2, 19, 0)

GUTENBERG_TEXT = """The Project Gutenberg eBook of A Test Book
*** START OF THE PROJECT GUTENBERG EBOOK A TEST BOOK ***

CONTENTS

CHAPTER I. Beginnings ........ 1

CHAPTER I.

It was a bright cold morning in the town of Lesser Wending, and every chimney sent up its own small opinion of the weather into a sky that had none.

Mrs Parry, who kept the lamp shop, was the first to notice that the river had stopped, quite politely, as if it had remembered an appointment elsewhere.

*** END OF THE PROJECT GUTENBERG EBOOK A TEST BOOK ***
"""


def _client():
    def handler(req: httpx.Request):
        u = str(req.url)
        if u.startswith("https://archive.org/advancedsearch.php"):
            return httpx.Response(200, json={"response": {"docs": [
                {"identifier": "his_girl_friday", "title": "His Girl Friday", "year": 1940, "downloads": 900000,
                 "description": "<p>A newspaper editor tries to win back his ace reporter. Fast talk ensues.</p>", "runtime": "1:31:44"},
                {"identifier": "bad id with spaces", "title": "Broken"},
                {"identifier": "grind", "title": "Double Feature", "description": "ADULT CONTENT -- NUDITY"},
            ]}})
        if u.startswith("https://gutendex.com/books/"):
            return httpx.Response(200, json={"results": [{
                "id": 99999, "title": "A Test Book: Being a Novel", "authors": [{"name": "Parry, Ann"}], "copyright": False,
                "download_count": 1234, "summaries": ["A quiet town notices its river has stopped. (This is an automatically generated summary.)"],
                "formats": {"text/plain; charset=us-ascii": "https://www.gutenberg.org/cache/epub/99999/pg99999.txt",
                            "image/jpeg": "https://www.gutenberg.org/cache/epub/99999/cover.jpg"}}]})
        if u.startswith("https://www.gutenberg.org/cache/epub/99999/"):
            return httpx.Response(200, text=GUTENBERG_TEXT)
        if u.startswith("https://poetrydb.org/random/"):
            return httpx.Response(200, json=[
                {"title": "Lines on a Kettle", "author": "A. Poet", "linecount": "4",
                 "lines": ["The kettle sings its little tune,", "The window holds a paper moon,", "And all the house", "is warm by noon."]},
                {"title": "An Epic", "author": "B. Poet", "linecount": "900", "lines": ["Too long"]},
            ])
        if u.startswith("https://hn.algolia.com/"):
            return httpx.Response(200, json={"hits": []})
        return httpx.Response(404)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _scout(app):
    sources = [archive_source("feature_films", "film", 2), gutenberg_source(), poetry_source()]
    with app.ctx() as c:
        return Scout(app.settings, client=_client(), feeds=[], sources=sources).run(c.s, NOW)


def test_media_sources_ingest_playable_public_domain_things(app):
    rep = _scout(app)
    assert rep.added == 3 and rep.feeds_ok == 3
    with app.ctx() as c:
        by_kind = {d.kind: d for d in c.s.scalars(select(Discovery).where(Discovery.score.is_not(None)))}
        film, book, poem = by_kind["film"], by_kind["book"], by_kind["poem"]
        assert film.title == "His Girl Friday (1940)" and film.media == {"type": "embed", "provider": "archive", "id": "his_girl_friday", "runtime": "1:31:44"}
        assert film.rights.embed_or_play and "Public domain" in film.rights.license
        assert film.signals["reach"] == 900000 and film.signals["breakdown"]["rarity"] == 30  # popular: oneitem's rarity drops
        assert book.title == "A Test Book, by Ann Parry" and book.analysis_depth == "excerpt"
        assert book.media["text"].startswith("It was a bright cold morning") and "CONTENTS" not in book.media["text"]
        assert "automatically generated" not in book.summary
        assert poem.media["form"] == "poem" and poem.media["text"].count("\n") == 3


def test_player_is_rebuilt_from_validated_ids_only():
    assert player({"type": "embed", "provider": "archive", "id": "his_girl_friday"})["src"] == "https://archive.org/embed/his_girl_friday"
    assert player({"type": "embed", "provider": "vimeo", "id": "123456"})["src"] == "https://player.vimeo.com/video/123456?dnt=1"
    assert player({"type": "embed", "provider": "archive", "id": "x\" onload=\"alert(1)"}) is None
    assert player({"type": "embed", "provider": "vimeo", "id": "javascript:1"}) is None
    assert player({"type": "audio", "src": "javascript:alert(1)"}) is None
    assert player({"type": "audio", "src": "http://insecure.example/a.mp3"}) is None
    assert teaser("poem", "", {"type": "text", "form": "poem", "text": "One\nTwo\nThree"}) == "One / Two"


def test_gutenberg_excerpt_skips_header_and_contents():
    ex = gutenberg_excerpt(GUTENBERG_TEXT)
    assert ex.startswith("It was a bright cold morning") and "END OF THE PROJECT" not in ex


def test_excerpt_skips_a_table_of_contents_that_names_chapter_one():
    raw = ("*** START OF THE PROJECT GUTENBERG EBOOK X ***\n\nCONTENTS\n\nCHAPTER I. Jonathan Harker's Journal\n"
           "CHAPTER II. Jonathan Harker's Journal\nCHAPTER III. Jonathan Harker's Journal\nCHAPTER IV. Letters\n\n"
           "CHAPTER I\n\nJONATHAN HARKER'S JOURNAL\n\n"
           "3 May. Bistritz. Left Munich at 8:35 P.M., on 1st May, arriving at Vienna early next morning.\n\n"
           "*** END OF THE PROJECT GUTENBERG EBOOK X ***\n")
    assert gutenberg_excerpt(raw).startswith("3 May. Bistritz.")


def test_uploader_public_domain_claims_need_an_old_enough_year():
    from voidgrid.media import plausibly_public_domain

    assert plausibly_public_domain("feature_films", {"year": "1940"})
    assert not plausibly_public_domain("feature_films", {"year": 2011})  # a 2011 film marked PD by its uploader
    assert not plausibly_public_domain("classic_tv", {})  # no year, no claim we can sanity-check
    assert plausibly_public_domain("prelinger", {})  # curated public-domain collection


def test_lineup_offers_five_varied_options_with_one_logged_exploration(app):
    _scout(app)
    lounge = app.lounge()
    out = lounge.lineup("sam")  # before arriving, so nothing is on yet
    opts = out["options"]
    assert len(opts) == 5
    assert len({o["id"] for o in opts}) == 5
    assert {"film", "book", "poem"} <= {o["kind"] for o in opts[:4]}  # best of each kind before repeats
    assert [o["exploratory"] for o in opts] == [False, False, False, False, True]
    assert all(o["preview"]["teaser"] for o in opts)
    with app.ctx() as c:
        ev = c.s.get(Event, out["lineup_id"])
        assert ev.type == EventType.LINEUP_SHOWN and ev.payload["options"][4]["propensity"] > 0
    # Asking again excluding these gives five different ones
    again = lounge.lineup("sam", exclude={o["id"] for o in opts})
    assert not {o["id"] for o in again["options"]} & {o["id"] for o in opts}


def test_playing_a_pick_puts_it_on_and_the_gallery_reacts_to_it(app, provider):
    _scout(app)
    lounge = app.lounge()
    lounge.enter("sam")
    opts = lounge.lineup("sam")
    # Arriving put the top find on; pick something to read from what's left (the book or the poem)
    book = next(o for o in opts["options"] if o["kind"] in ("book", "poem"))
    assert book["player"]["type"] == "text"
    provider.requests.clear()
    out = lounge.play("sam", book["id"], slot=book["slot"], lineup_id=opts["lineup_id"])
    assert out["discovery"]["id"] == book["id"] and out["conversation"]
    # The regulars have the text itself, and know it's being read right now
    words = "Lesser Wending" if book["kind"] == "book" else "paper moon"
    assert any("<excerpt>" in r.system_prompt and words in r.system_prompt and "reading it right now" in r.system_prompt
               for r in provider.requests)
    assert lounge.current("sam")["discovery"]["id"] == book["id"]
    # It's now seen, so it leaves the lineup
    assert book["id"] not in {o["id"] for o in lounge.lineup("sam")["options"]}
    with app.ctx() as c:
        played = c.s.scalars(select(Event).where(Event.type == EventType.DISCOVERY_PLAYED)).one()
        assert played.payload == {"discovery_id": book["id"], "slot": book["slot"], "lineup_id": opts["lineup_id"], "kind": book["kind"]}


def test_ui_lineup_and_play(app):
    _scout(app)
    web = TestClient(create_app(app, start_scout=False))
    web.post("/api/enter", json={})
    lu = web.post("/api/lineup", json={"exclude": []}).json()
    assert len(lu["options"]) == 5
    with app.ctx() as c:
        film_id = c.s.scalar(select(Discovery.id).where(Discovery.kind == "film"))
    played = web.post("/api/play", json={"discovery_id": film_id, "slot": 0, "lineup_id": lu["lineup_id"]}).json()
    assert played["discovery"]["player"] == {"type": "iframe", "src": "https://archive.org/embed/his_girl_friday", "label": "Internet Archive player"}
    assert web.post("/api/play", json={"discovery_id": 999999}).status_code == 400
    assert web.post("/api/play", data={"discovery_id": "1"}).status_code == 415
