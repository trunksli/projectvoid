"""The lightweight VIP link (spec §3.13 B2): a tiny page so family can leave a note or pin something without an AI client.

It can show only the owner's wall and discovery titles already shown in their lounge. Nothing private.
"""

from __future__ import annotations

from html import escape

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .app import App
from .common import LinkInactive, LoungeError

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<title>{title}</title><style>
:root{{--bg:#1d1814;--card:#2a221c;--ink:#f3e9dc;--muted:#bfae99;--accent:#e0a458}}
@media (prefers-color-scheme: light){{:root{{--bg:#f7f1e8;--card:#fffaf2;--ink:#2b2118;--muted:#6f5d4b;--accent:#a8641b}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 Georgia,serif}}
main{{max-width:560px;margin:0 auto;padding:24px 16px}}
h1{{font-size:1.5rem;margin:0 0 4px}} p.sub{{color:var(--muted);margin:0 0 20px}}
section{{background:var(--card);border-radius:12px;padding:16px;margin:0 0 16px}}
h2{{font-size:1rem;margin:0 0 8px;color:var(--accent)}} ul{{margin:0;padding-left:18px}}
textarea,select{{width:100%;box-sizing:border-box;font:inherit;padding:8px;border-radius:8px;border:1px solid var(--muted);background:var(--bg);color:var(--ink)}}
button{{margin-top:8px;font:inherit;padding:8px 14px;border:0;border-radius:8px;background:var(--accent);color:#1d1814;cursor:pointer}}
.ok{{color:var(--accent)}}</style></head><body><main>{body}</main></body></html>"""


def create_app(app: App | None = None) -> FastAPI:
    core = app or App()
    vip = core.vip()
    web = FastAPI(title=f"{core.settings.brand_name} VIP link", docs_url=None, redoc_url=None, openapi_url=None)

    def page(title: str, body: str, status: int = 200) -> HTMLResponse:
        return HTMLResponse(PAGE.format(title=escape(title), body=body), status_code=status, headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"})

    def gone() -> HTMLResponse:
        return page("Link not active", "<h1>This link isn't active</h1><p class='sub'>Ask the person who sent it for a new one.</p>", 410)

    @web.get("/health")
    def health() -> dict:
        return {"ok": True}

    @web.get("/v/{token}", response_class=HTMLResponse)
    def view(token: str, done: str | None = None) -> HTMLResponse:
        try:
            v = vip.link_view(token)
        except LinkInactive:
            return gone()
        wall = "".join(f"<li>“{escape(w['label'])}” — {escape(w['spot'])}</li>" for w in v["wall"]) or "<li>Nothing up yet.</li>"
        body = [
            f"<h1>{escape(v['owner'])}'s place</h1>",
            f"<p class='sub'>You're here as their {escape(v['you_are_their'])}. It's {escape(v['setting'])}. Wren (the host, an AI) will pass things on.</p>",
        ]
        if done:
            body.append(f"<p class='ok'>{'Note left.' if done == 'note' else 'Pinned to the wall.'} They'll hear about it next time they're in.</p>")
        body.append(f"<section><h2>On the wall</h2><ul>{wall}</ul></section>")
        if v["can_note"]:
            body.append(
                f"<section><h2>Leave a note</h2><form method='post' action='/v/{escape(token)}/note'>"
                "<textarea name='text' rows='3' maxlength='500' required></textarea><button type='submit'>Leave note</button></form></section>"
            )
        if v["can_pin"] and v["shareable"]:
            opts = "".join(f"<option value='{d['id']}'>{escape(d['title'])}</option>" for d in v["shareable"])
            body.append(
                f"<section><h2>Pin something to their wall</h2><form method='post' action='/v/{escape(token)}/pin'>"
                f"<select name='discovery_id'>{opts}</select><button type='submit'>Pin it</button></form></section>"
            )
        return page(f"{v['owner']}'s place", "".join(body))

    @web.post("/v/{token}/note")
    def note(token: str, text: str = Form(...)):
        try:
            vip.leave_note(None, None, text, link_token=token)
        except LinkInactive:
            return gone()
        except LoungeError as e:
            return page("Hmm", f"<p>{escape(str(e))}</p>", 400)
        return RedirectResponse(f"/v/{token}?done=note", status_code=303)

    @web.post("/v/{token}/pin")
    def pin(token: str, discovery_id: int = Form(...)):
        try:
            vip.pin(None, None, discovery_id=discovery_id, link_token=token)
        except LinkInactive:
            return gone()
        except LoungeError as e:
            return page("Hmm", f"<p>{escape(str(e))}</p>", 400)
        return RedirectResponse(f"/v/{token}?done=pin", status_code=303)

    return web


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
