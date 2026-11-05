"""Runtime configuration. Every value can be overridden with a VOIDGRID_* env var or a .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOIDGRID_", env_file=".env", extra="ignore")

    # The consumer brand is not final (spec §0); keep it configurable everywhere.
    brand_name: str = "VoidGrid"

    # SQLite for local dev/tests, PostgreSQL in production (postgresql+psycopg://...).
    database_url: str = "sqlite:///./voidgrid.db"

    # "scripted" runs fully offline and deterministically; "anthropic" uses the Claude API.
    llm_provider: str = "scripted"
    anthropic_model: str = "claude-opus-5-5"
    anthropic_effort: str = "low"  # chat lines do well at low effort; raise if quality needs it
    anthropic_max_tokens: int = 2000

    # Who this MCP server instance acts as (stdio = one person per server process).
    user_handle: str = "me"

    # Conversation engine bounds (spec §3.7 "Conversation engine").
    max_gallery_turns: int = 5
    quiet_gallery_turns: int = 2
    daily_turn_budget_per_lounge: int = 200

    # Memory (spec §3.7 + §3.16).
    episodic_retention_ratio: float = 0.2
    episodic_cap_per_agent: int = 60
    fact_hedge_threshold: float = 0.7

    # Lightweight VIP link (spec §3.13 B2).
    web_base_url: str = "http://127.0.0.1:8000"
    vip_link_actions_per_hour: int = 20

    # Real, rights-cleared source (spec §3.15 freshness floor). Off by default so tests stay offline.
    enable_wikipedia_source: bool = False
    contact_url: str = "https://github.com/trunksli/projectvoid"


@lru_cache
def get_settings() -> Settings:
    return Settings()
