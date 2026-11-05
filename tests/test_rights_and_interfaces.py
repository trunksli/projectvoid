"""Content rights, the Wikipedia adapter, the MCP surface and the VIP web link."""

import asyncio
from datetime import date

import pytest
from fastapi.testclient import TestClient

from voidgrid.content import WikipediaFeaturedSource, ingest, upsert_rights
from voidgrid.mcp_server import build_server
from voidgrid.web import create_app


def test_rights_denied_source_is_never_shown(app, clock):
    with app.ctx() as c:
        upsert_rights(c.s, {"source_key": "denied_catalog", "rights_holder": "X", "license": "none", "index_metadata": True, "link": True})
        ingest(c.s, "denied_catalog", [{"external_id": "a", "title": "Forbidden", "summary": "s", "canonical_url": "https://example.com/a", "tags": ["animals"]}], clock())
    L = app.lounge()
    for _ in range(20):
        r = L.enter("sam")
        if r["discovery"] is None:
            break
        assert r["discovery"]["title"] != "Forbidden"


def test_ingest_requires_rights_record(app, clock):
    with app.ctx() as c, pytest.raises(PermissionError):
        ingest(c.s, "unknown_source", [{"external_id": "x", "title": "t", "canonical_url": "https://e.com"}], clock())


def test_metadata_only_video_is_labelled_honestly(app, clock, provider):
    with app.ctx() as c:
        upsert_rights(c.s, {"source_key": "link_only_videos", "rights_holder": "Y", "license": "link only",
                            "index_metadata": True, "read_metadata": True, "link": True})
        ingest(c.s, "link_only_videos", [{"external_id": "v", "title": "A lighthouse documentary", "summary": "About lighthouses.",
                                           "canonical_url": "https://example.com/v", "kind": "video", "tags": ["engineering", "history"]}], clock())
    L = app.lounge()
    for _ in range(30):
        r = L.enter("sam")
        if r["discovery"] and r["discovery"]["kind"] == "video":
            break
    assert r["discovery"]["what_we_accessed"] == "metadata_only"
    assert "metadata only" in r["narration"]
    vid_reqs = [q for q in provider.requests if "A lighthouse documentary" in q.system_prompt]
    assert vid_reqs and all("you have only its title/description" in q.system_prompt for q in vid_reqs)
    assert all("watched it" not in line["text"] or "none of us has actually watched it" in line["text"] for line in r["conversation"])


def test_wikipedia_parser():
    feed = {
        "tfa": {"titles": {"normalized": "Lighthouse of Alexandria"}, "extract": "An ancient lighthouse.",
                "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Lighthouse_of_Alexandria"}}},
        "onthisday": [{"text": "The first crossword is published.", "year": 1913,
                       "pages": [{"pageid": 42, "extract": "A word puzzle.", "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Crossword"}}}]}],
    }
    items = WikipediaFeaturedSource.parse(feed, date(2026, 11, 4))
    assert [i["canonical_url"] for i in items] == ["https://en.wikipedia.org/wiki/Lighthouse_of_Alexandria", "https://en.wikipedia.org/wiki/Crossword"]
    assert items[1]["title"].startswith("On this day in 1913")
    assert all(i["tags"] for i in items)
    assert WikipediaFeaturedSource.parse({}, date(2026, 11, 4)) == []
    grim = {"onthisday": [{"text": "A plane crashed, killing 12.", "year": 2025,
                           "pages": [{"pageid": 1, "extract": "x", "content_urls": {"desktop": {"page": "https://e.org/a"}}}]}]}
    assert WikipediaFeaturedSource.parse(grim, date(2026, 11, 4)) == []


def test_mcp_tools_and_identity(app):
    server = build_server(app, handle="sam")
    tools = asyncio.run(server.list_tools())
    names = {t.name for t in tools}
    for expected in ("enter_lounge", "listen", "say", "pin_to_wall", "what_do_you_remember", "forget", "invite_vip", "set_door", "visit_lounge", "visit_leave_note"):
        assert expected in names
    # identity is never a tool argument
    for t in tools:
        schema = getattr(t, "input_schema", None) or getattr(t, "inputSchema", None) or {}
        assert "handle" not in schema.get("properties", {})
    result = asyncio.run(server.call_tool("enter_lounge", {}))
    assert not (getattr(result, "is_error", False) or getattr(result, "isError", False))


def test_mcp_refusals_are_tool_errors(app):
    server = build_server(app, handle="sam")
    from mcp.server.mcpserver.exceptions import ToolError

    with pytest.raises(ToolError):
        asyncio.run(server.call_tool("listen", {}))


def test_vip_link_page(app):
    L, V = app.lounge(), app.vip()
    L.enter("sam")
    L.pin_to_wall("sam")
    inv = V.invite("sam", "sister", "Ana")
    token = inv["vip_link"].rsplit("/", 1)[1]
    client = TestClient(create_app(app))
    page = client.get(f"/v/{token}")
    assert page.status_code == 200 and "sam's place" in page.text and "Leave a note" in page.text
    L.say("sam", "My name is Sam and my secret is pineapples")
    page = client.get(f"/v/{token}")
    assert "pineapples" not in page.text and "Sam" not in page.text  # never chat or memories
    r = client.post(f"/v/{token}/note", data={"text": "<script>alert(1)</script> hi"}, follow_redirects=False)
    assert r.status_code == 303
    assert "Note left" in client.get(r.headers["location"]).text
    V.revoke("sam", "sister")
    assert client.get(f"/v/{token}").status_code == 410
    assert client.post(f"/v/{token}/note", data={"text": "x"}).status_code == 410
    assert client.get("/v/not-a-real-token").status_code == 410


def test_vip_link_escapes_html(app):
    L, V = app.lounge(), app.vip()
    L.enter("sam")
    L.pin_to_wall("sam", label="<b>bold</b>")
    inv = V.invite("sam", "sister", "Ana")
    token = inv["vip_link"].rsplit("/", 1)[1]
    page = TestClient(create_app(app)).get(f"/v/{token}")
    assert "<b>bold</b>" not in page.text and "&lt;b&gt;bold&lt;/b&gt;" in page.text
