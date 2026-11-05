from datetime import datetime, timedelta

import pytest

from voidgrid.app import App
from voidgrid.config import Settings
from voidgrid.llm import ScriptedProvider


class Clock:
    def __init__(self):
        self.t = datetime(2026, 11, 2, 19, 0)

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


class RecordingProvider(ScriptedProvider):
    """Scripted lines, but remembers every request so tests can inspect prompts."""

    def __init__(self):
        self.requests = []

    def speak(self, req):
        self.requests.append(req)
        return super().speak(req)


@pytest.fixture
def clock():
    return Clock()


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}", llm_provider="scripted")


@pytest.fixture
def provider():
    return RecordingProvider()


@pytest.fixture
def make_app(settings, clock, provider):
    apps = []

    def _make(**overrides):
        s = settings.model_copy(update=overrides) if overrides else settings
        a = App(s, provider=provider, clock=clock)
        apps.append(a)
        return a

    yield _make
    for a in apps:
        a.dispose()


@pytest.fixture
def app(make_app):
    return make_app()
