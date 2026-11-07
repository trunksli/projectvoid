"""The owner's web UI: the find in the middle, the forecast on the left, the peanut gallery on the right.

Local only. There is no login: whoever can reach this server *is* the owner (``VOIDGRID_USER_HANDLE``),
so it binds to 127.0.0.1, rejects other Host headers (DNS rebinding), and only accepts JSON POSTs
(a cross-site form can't send those without a CORS preflight, which we never grant).
Don't deploy it publicly; ``voidgrid-web`` (the VIP link page) is the one meant for that.
"""

from __future__ import annotations

import logging
import threading
from importlib import resources

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from starlette.middleware.trustedhost import TrustedHostMiddleware

from .app import App
from .common import LoungeError
from .config import Settings, get_settings
from .models import Discovery

log = logging.getLogger(__name__)

PREFETCH_BRIEFINGS = 5


class SayIn(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class ReactIn(BaseModel):
    reaction: str


class PlayIn(BaseModel):
    discovery_id: int
    slot: int | None = Field(default=None, ge=0, le=20)
    lineup_id: int | None = None


class LineupIn(BaseModel):
    exclude: list[int] = Field(default_factory=list, max_length=200)


class ScoutState:
    def __init__(self):
        self.running = False
        self.message = "Idle"
        self.last: dict | None = None
        self.lock = threading.Lock()


def require_json(request: Request) -> None:
    if not request.headers.get("content-type", "").startswith("application/json"):
        raise HTTPException(415, "JSON only")


def create_app(app: App | None = None, *, start_scout: bool | None = None) -> FastAPI:
    core = app or App()
    lounge = core.lounge()
    handle = core.settings.user_handle
    gate = threading.Lock()  # one lounge operation at a time (SQLite, one owner)
    scout = ScoutState()

    web = FastAPI(title=f"{core.settings.brand_name}", docs_url=None, redoc_url=None, openapi_url=None)
    web.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    def run(fn, *args):
        with gate:
            try:
                return fn(handle, *args)
            except LoungeError as e:
                raise HTTPException(400, str(e)) from e

    @web.exception_handler(HTTPException)
    def _err(_req, exc: HTTPException):
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code)

    @web.get("/", response_class=HTMLResponse)
    def index() -> HTMLResponse:
        html = resources.files("voidgrid.static").joinpath("ui.html").read_text(encoding="utf-8")
        return HTMLResponse(html.replace("{{BRAND}}", core.settings.brand_name), headers={"Cache-Control": "no-store"})

    @web.get("/api/current")
    def current() -> dict:
        out = run(lounge.current)
        out["scout"] = scout_status()
        out["settings"] = {
            "voices": core.settings.llm_provider,
            "briefings": core.briefer is not None,
            "scout": core.settings.enable_scout,
        }
        return out

    @web.post("/api/enter", dependencies=[Depends(require_json)])
    def enter() -> dict:
        return run(lounge.enter)

    @web.post("/api/listen", dependencies=[Depends(require_json)])
    def listen() -> dict:
        return run(lounge.listen)

    @web.post("/api/next", dependencies=[Depends(require_json)])
    def next_find() -> dict:
        return run(lounge.next_find)

    @web.post("/api/lineup", dependencies=[Depends(require_json)])
    def lineup(body: LineupIn) -> dict:
        return run(lounge.lineup, set(body.exclude))

    @web.post("/api/play", dependencies=[Depends(require_json)])
    def play(body: PlayIn) -> dict:
        with gate:
            try:
                return lounge.play(handle, body.discovery_id, slot=body.slot, lineup_id=body.lineup_id)
            except LoungeError as e:
                raise HTTPException(400, str(e)) from e

    @web.post("/api/say", dependencies=[Depends(require_json)])
    def say(body: SayIn) -> dict:
        return run(lounge.say, body.text)

    @web.post("/api/react", dependencies=[Depends(require_json)])
    def react(body: ReactIn) -> dict:
        return run(lounge.react, body.reaction)

    @web.post("/api/leave", dependencies=[Depends(require_json)])
    def leave() -> dict:
        return run(lounge.leave)

    # ------------------------------------------------------------------ the scout, in the background
    def scout_status() -> dict:
        return {"running": scout.running, "message": scout.message, "last": scout.last}

    def _prefetch() -> None:
        if core.briefer is None:
            return
        with core.ctx() as c:
            ids = list(c.s.scalars(select(Discovery.id).where(Discovery.briefing.is_(None), Discovery.score.is_not(None))
                                   .order_by(Discovery.score.desc()).limit(PREFETCH_BRIEFINGS)))
        for i, did in enumerate(ids, 1):
            scout.message = f"Looking up what people say ({i}/{len(ids)})"
            with core.ctx() as c:
                c.ensure_briefing(c.s.get(Discovery, did))

    def _scout_job() -> None:
        try:
            rep = core.scout(progress=lambda m: setattr(scout, "message", m))
            scout.last = {"added": rep.added, "feeds_ok": rep.feeds_ok, "feeds_failed": rep.feeds_failed, "rejected": rep.rejected}
            _prefetch()
            scout.message = f"Found {rep.added} new finds from {rep.feeds_ok} feeds"
        except Exception as e:
            log.exception("scout run failed")
            scout.message = f"Scout failed: {type(e).__name__}"
        finally:
            scout.running = False

    def start_scout_job() -> bool:
        with scout.lock:
            if scout.running:
                return False
            scout.running = True
            scout.message = "Starting"
        threading.Thread(target=_scout_job, name="scout", daemon=True).start()
        return True

    @web.get("/api/scout")
    def scout_get() -> dict:
        return scout_status()

    @web.post("/api/scout", dependencies=[Depends(require_json)])
    def scout_post() -> dict:
        if not core.settings.enable_scout:
            raise HTTPException(400, "The scout is off. Set VOIDGRID_ENABLE_SCOUT=true.")
        started = start_scout_job()
        return dict(scout_status(), started=started)

    should_start = core.settings.enable_scout if start_scout is None else start_scout
    if should_start:
        with core.ctx() as c:
            has_real = c.s.scalar(select(Discovery.id).where(Discovery.score.is_not(None)).limit(1)) is not None
        if not has_real:
            start_scout_job()

    return web


def ui_settings() -> Settings:
    """The UI is the place to iterate on the experience, so live sources default ON here (unless set)."""
    s = get_settings()
    updates = {f: True for f in ("enable_scout", "enable_briefings") if f not in s.model_fields_set}
    return s.model_copy(update=updates) if updates else s


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    settings = ui_settings()
    print(f"{settings.brand_name} is open at http://{settings.ui_host}:{settings.ui_port}  (voices: {settings.llm_provider})")
    uvicorn.run(create_app(App(settings)), host=settings.ui_host, port=settings.ui_port)


if __name__ == "__main__":
    main()
