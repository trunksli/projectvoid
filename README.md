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

## The web UI (fastest way to iterate)

```bash
uv run voidgrid-ui     # http://127.0.0.1:8010
```

Three panels: the **find** in the middle, a **forecast** on the left (a placeholder for now, showing current buzz and the scout's score breakdown), and the **peanut gallery** on the right, where you can talk to the room. On first start the scout reads its feeds in the background (about 30 seconds); press **Next find** to see what it found.

The UI runs the same lounge as the MCP server (same database, same `VOIDGRID_USER_HANDLE`). It's **local only**: there's no login, so it binds to 127.0.0.1, rejects other Host headers, and only accepts JSON posts. Don't expose it; `voidgrid-web` is the one meant for the internet.

### Where finds come from: the scout (ported from project oneitem)

[scout.py](src/voidgrid/scout.py) is oneitem's pipeline:

- **Sources:** its hand-picked list of expert publications, films and podcasts, at most 3 new items per feed per run, skipping grim items and anything older than 30 days.
- **Buzz (the trend signal):** Hacker News points, comments and points per hour for the item's own link. oneitem used YouTube views against the channel's subscriber count, which needs an API key; feeds have no view counts.
- **Diamond score:** oneitem's formula, `0.45·quality + 0.25·interestingness + 0.20·rarity + 0.10·originality + outlier bonus (up to 30 for a fast riser in its first 14 days) − 0.5·clickbait`, with anything under 50 trust rejected. With `VOIDGRID_LLM_PROVIDER=anthropic`, Claude judges quality, interest, originality, clickbait and trust. Offline, a simple heuristic does.
- **Rotation:** after an article, a near-equal film or podcast wins.

### What the gallery reacts with: briefings

For each find, [briefing.py](src/voidgrid/briefing.py) gathers real material, and each regular has a job:

| Regular | Beat | From |
|---|---|---|
| Theo | a real fact | Wikipedia, with a link to the page |
| Pip | what people are saying | Hacker News comments on this exact link; failing that, a well-discussed HN thread about the find's named subject (labelled as such) |
| Jules | a joke | Jules's own (needs Claude voices to be actually funny) |

Every line that uses outside material shows its receipt (source link) in the UI. Third-party text is fenced as data in the prompts. A wrong fact is worse than none, so a Wikipedia page or HN thread only counts if it shares real words with the find. When nothing is relevant, that beat is skipped.

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
| `src/voidgrid/ui.py`, `static/ui.html` | The owner's web UI |
| `src/voidgrid/scout.py` | Feeds, buzz, diamond score (oneitem port) |
| `src/voidgrid/briefing.py` | Real commentary and facts for the gallery |
| `migrations/` | Alembic migrations |

## Known limitations (v1)

- **Not yet tried with real Claude voices.** The Claude provider's request shape is tested against the SDK, but no live conversation has been run. Voice quality and per-visit cost are unmeasured.
- **Scripted mode is a placeholder voice.** It's fine for tests and offline use, but repetitive over many visits.
- **Commentary coverage is thin.** Most fresh niche articles haven't been posted to Hacker News yet, so Pip's beat is often skipped. Bluesky and Reddit search both refuse unauthenticated requests (checked 2026-11-06); adding them needs app credentials.
- **Fact matching is word overlap**, unless Claude is on (then Claude suggests the Wikipedia articles). Offline it can land on a related-but-tangential page (a fact about Berkeley for a story set there).
- **Offline scoring is a heuristic.** Without Claude, the diamond score mostly reflects buzz and freshness, not quality.
- **Fact extraction is rule-based** ("my name is…", "I love…"). It misses things said less directly.
- **Taste tags and the grim-content filter are keyword lists**, not classifiers.
- **Identity is per-process** (`VOIDGRID_USER_HANDLE`). There's no login, so a hosted multi-user deployment needs MCP auth first.
- **Presence is polled.** Live arrivals show up on your next tool call, not as a push.
- **PostgreSQL and Docker are untested here.** Tests run on SQLite; the migration was generated and checked against SQLite only.
