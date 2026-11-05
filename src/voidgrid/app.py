"""Application container: one per process. Opens a unit-of-work session per request/tool call."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .content import ContentService, load_fixtures, refresh_wikipedia
from .db import init_db, make_engine, make_session_factory
from .gallery import Gallery
from .llm import LLMProvider, make_provider
from .memory import MemoryService
from .models import utcnow


@dataclass
class Ctx:
    """Everything one request needs, bound to one DB session."""

    s: Session
    settings: Settings
    now: Callable[[], datetime]
    provider: LLMProvider

    @property
    def memory(self) -> MemoryService:
        return MemoryService(self.s, self.settings, self.now)

    @property
    def content(self) -> ContentService:
        return ContentService(self.s, self.memory, self.now)

    @property
    def gallery(self) -> Gallery:
        return Gallery(self.s, self.settings, self.provider, self.memory, self.now)


class App:
    def __init__(
        self,
        settings: Settings | None = None,
        *,
        provider: LLMProvider | None = None,
        clock: Callable[[], datetime] | None = None,
        create_tables: bool = True,
        load_fixture_content: bool = True,
    ):
        self.settings = settings or get_settings()
        self.engine = make_engine(self.settings.database_url)
        if create_tables:
            init_db(self.engine)
        self.sessions = make_session_factory(self.engine)
        self.provider = provider or make_provider(self.settings)
        self.clock = clock or utcnow
        if load_fixture_content:
            with self.ctx() as c:
                load_fixtures(c.s, c.now())
                if self.settings.enable_wikipedia_source:
                    refresh_wikipedia(c.s, self.settings, c.now())

    @contextmanager
    def ctx(self) -> Iterator[Ctx]:
        s = self.sessions()
        try:
            yield Ctx(s=s, settings=self.settings, now=self.clock, provider=self.provider)
            s.commit()
        except Exception:
            s.rollback()
            raise
        finally:
            s.close()

    def lounge(self):
        from .lounge import LoungeService

        return LoungeService(self)

    def vip(self):
        from .vip import VipService

        return VipService(self)

    def dispose(self) -> None:
        self.engine.dispose()
