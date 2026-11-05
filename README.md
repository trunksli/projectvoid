# VoidGrid (working title)

A living digital third place you drop into through your AI assistant (MCP):

1. **Something worth your five minutes is happening when you arrive.** A fresh, source-backed find, and the regulars talking about it.
2. **The regulars remember you.** Wren (host), Theo, Jules and Pip are AI characters who remember your name, your tastes, what you said, and what they promised you. They hedge when they're unsure.
3. **Occasionally someone you love drops by.** Trusted VIPs can walk in live, or leave a note or pin something while you're away. Wren tells you truthfully next time.

You can also make the place yours, for free: pick a setting and a favourite seat, and pin things to the wall.

The product spec is [voidgrid_master_prompt_v5_mission_focus.md](voidgrid_master_prompt_v5_mission_focus.md). This code implements its **v1 scope** (Phases 1–2). Everything marked [LATER] in the spec is intentionally not built.

## Quick start

Requires [uv](https://docs.astral.sh/uv/). It installs Python 3.12 for you.

```bash
uv sync
uv run voidgrid-demo
```

The demo runs the spec §12 walkthrough end to end: first visit, the sister's async visit, an app restart, the catch-up, a live drop-in, revocation, memory deletion, and a quiet night. It runs offline with scripted regulars.

```bash
uv run --group dev pytest
```

## Connect it to Claude Desktop (or any MCP client)

Each person runs their own server process; identity comes from `VOIDGRID_USER_HANDLE`, never from tool arguments. Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "voidgrid": {
      "command": "uv",
      "args": ["--directory", "C:/Documents/Code/antigravity/void", "run", "voidgrid-mcp"],
      "env": {
        "VOIDGRID_USER_HANDLE": "sam",
        "VOIDGRID_DATABASE_URL": "sqlite:///C:/Documents/Code/antigravity/void/voidgrid.db"
      }
    }
  }
}
```

Then say "take me to my usual spot". A VIP on the same machine/database uses the same config with their own handle.

### Real Claude regulars

By default the regulars are **scripted** (offline, deterministic, free). To have each regular voiced by Claude:

```bash
VOIDGRID_LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=... uv run voidgrid-demo
```

Every line is its own API call with that regular's private prompt and memories (model `claude-opus-5-5`, effort `low`, server-side refusal fallback on). An arrival is typically 4–5 calls. Change `VOIDGRID_ANTHROPIC_MODEL` / `VOIDGRID_ANTHROPIC_EFFORT` to trade cost for quality. `VOIDGRID_DAILY_TURN_BUDGET_PER_LOUNGE` caps the number of calls per lounge per day.

### The VIP link (for family without an AI assistant)

```bash
uv run voidgrid-web     # http://127.0.0.1:8000
```

`invite_vip` returns a private link `/v/<token>`. The page shows only the owner's wall and discovery titles. From it, a VIP can leave a note or pin one of those titles. Revoking the VIP kills the link (HTTP 410). For anyone outside your machine to use it, it has to be deployed behind HTTPS. Set `VOIDGRID_WEB_BASE_URL` to that address.

### Real content

Fixtures (16 hand-written summaries linking to Wikipedia) are always loaded. `VOIDGRID_ENABLE_WIKIPEDIA_SOURCE=true` also pulls Wikipedia's daily featured feed (CC BY-SA 4.0, link-first, with attribution). Grim items (deaths, disasters, violence) are filtered out.

## Configuration

All settings are `VOIDGRID_*` env vars or a `.env` file; see [.env.example](.env.example) and [config.py](src/voidgrid/config.py).

## Production database

SQLite is the default. For PostgreSQL:

```bash
uv sync --extra postgres
VOIDGRID_DATABASE_URL=postgresql+psycopg://voidgrid:voidgrid@localhost:5432/voidgrid uv run alembic upgrade head
```

`docker compose up` starts PostgreSQL and the VIP web link.

## Layout

| Path | What it does |
|---|---|
| `src/voidgrid/lounge.py` | Arrive, listen, say, react, customize, pin, leave; the truthful catch-up |
| `src/voidgrid/gallery.py` | Conversation engine: host opens, dynamic turn selection, silence, budgets |
| `src/voidgrid/memory.py` | User facts (bypass the 20% budget), per-regular episodes and relationships, consolidation |
| `src/voidgrid/vip.py` | Invites, door policy (open/knock/private), live and async visits, revocation |
| `src/voidgrid/content.py` | Rights records (default deny), ingestion, freshness floor, Wikipedia adapter |
| `src/voidgrid/characters.py` | The regulars and the settings |
| `src/voidgrid/llm.py` | Scripted and Claude providers |
| `src/voidgrid/mcp_server.py` | 24 MCP tools |
| `src/voidgrid/web.py` | The VIP link page |
| `migrations/` | Alembic migrations |

## Known limitations (v1)

- **Not yet tried with real Claude voices.** The Claude provider's request shape is tested against the SDK, but no live conversation has been run. Voice quality and per-visit cost are unmeasured.
- **Scripted mode is a placeholder voice.** It's fine for tests and offline use, but repetitive over many visits.
- **Fact extraction is rule-based** ("my name is…", "I love…"). It misses things said less directly.
- **Taste tags and the grim-content filter are keyword lists**, not classifiers.
- **Identity is per-process** (`VOIDGRID_USER_HANDLE`). There's no login, so a hosted multi-user deployment needs MCP auth first.
- **Presence is polled.** Live arrivals show up on your next tool call, not as a push.
- **PostgreSQL and Docker are untested here.** Tests run on SQLite; the migration was generated and checked against SQLite only.
