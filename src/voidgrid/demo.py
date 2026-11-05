"""The v5 vertical-slice demo (spec §12), end to end, including an application restart.

    uv run voidgrid-demo                 # offline, scripted regulars
    VOIDGRID_LLM_PROVIDER=anthropic uv run voidgrid-demo   # real Claude regulars (needs credentials)
"""

from __future__ import annotations

import os
import sys
import tempfile
from datetime import datetime, timedelta

from .app import App
from .common import LoungeError
from .config import Settings


class Clock:
    def __init__(self, start: datetime):
        self.t = start

    def __call__(self) -> datetime:
        return self.t

    def advance(self, **kw) -> None:
        self.t += timedelta(**kw)


def banner(title: str) -> None:
    print("\n" + "=" * 72 + f"\n{title}\n" + "=" * 72)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    db = os.path.join(tempfile.mkdtemp(prefix="voidgrid-demo-"), "demo.db")
    base = Settings()
    settings = base.model_copy(update={"database_url": f"sqlite:///{db}"})
    clock = Clock(datetime(2026, 11, 2, 19, 30))  # a Monday evening

    app = App(settings, clock=clock)
    L, V = app.lounge(), app.vip()

    banner("1-2. First visit: the host greets, the regulars talk about a fresh find")
    L.customize("sam", theme="neighborhood_bar", seat="the stool by the window")
    print(L.enter("sam")["narration"])

    banner("3. Sam joins in (name + a taste), then reacts")
    r = L.say("sam", "My name is Sam, and I love octopuses. Theo, is that real?")
    print(r["narration"])
    print("Remembered:", r["remembered"])
    print(L.react("sam", "loved")["narration"])

    banner("4. Sam pins the find to the wall (free, no quest) and invites their sister")
    print(L.pin_to_wall("sam")["narration"])
    inv = V.invite("sam", "sister", "Ana")
    print(inv["narration"])
    print(V.set_join_policy("sam", "open")["narration"])
    print(L.leave("sam")["narration"])

    banner("5. While Sam is away: Ana visits through her AI client, then via her private link")
    clock.advance(days=1, hours=1)  # Tuesday
    V.accept("ana", inv["invite_code"])
    print(V.drop_in("ana", "sam")["narration"])
    print(V.say("ana", "sam", "Jules, I bet Sam made you talk about octopuses all night.")["narration"])
    V.leave("ana", "sam")
    token = inv["vip_link"].rsplit("/", 1)[1]
    V.leave_note(None, None, "Saw the tree thing on your wall. Call Mum on Sunday!", link_token=token)
    V.pin(None, None, label="a postcard from Lisbon", link_token=token)
    try:
        V.drop_in("stranger", "sam")
    except LoungeError as e:
        print("Unapproved visitor denied:", e)
    V.set_join_policy("sam", "knock")
    print("Knock-first door:", V.drop_in("ana", "sam")["narration"])
    V.set_join_policy("sam", "open")

    banner("6. Restart the application (new process state, same database)")
    app.dispose()
    clock.advance(days=1)  # Wednesday
    app = App(settings, clock=clock)
    L, V = app.lounge(), app.vip()

    banner("7. Second visit: greeted by name, truthful catch-up, new find, wall persists")
    print(L.enter("sam")["narration"])

    banner("8. Live VIP: Ana walks in while Sam is here, then Sam revokes her access")
    print(V.drop_in("ana", "sam")["narration"])
    print(L.listen("sam")["narration"])
    V.leave("ana", "sam")
    print(V.revoke("sam", "sister")["narration"])
    for attempt in (lambda: V.drop_in("ana", "sam"), lambda: V.leave_note(None, None, "hi", link_token=token)):
        try:
            attempt()
        except LoungeError as e:
            print("After revocation:", e)

    banner("9. Memory controls: what the regulars remember, and forgetting one thing")
    mem = L.remember("sam")
    print(mem["narration"])
    likes = next(f for f in mem["facts"] if f["kind"] == "likes" and f["content"] == "octopuses")
    print(L.forget("sam", likes["id"])["narration"])

    banner("10. Empty bar: every find has been seen, so nothing new is invented")
    L.leave("sam")
    with app.ctx() as c:
        from sqlalchemy import select

        from .models import Discovery, User

        user = c.s.scalar(select(User).where(User.handle == "sam"))
        for d in c.s.scalars(select(Discovery)):
            c.content.mark_seen(user, d)
    clock.advance(days=1)
    print(L.enter("sam")["narration"])

    banner("11. Sam never earned an item and still had a complete visit")
    print(L.leave("sam")["narration"])
    print(f"\n(Demo database: {db})")


if __name__ == "__main__":
    main()
