"""Model providers. Each regular is invoked separately with its own prompt and memories (spec §3.7).

- ScriptedProvider: offline, deterministic, used for tests and the no-API-key experience.
- AnthropicProvider: the Claude API. Uses `claude-opus-5-5` by default (configurable).
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Protocol

from .characters import Character
from .config import Settings

log = logging.getLogger(__name__)


@dataclass
class RoomLine:
    speaker_name: str
    speaker_type: str  # bot | human_owner | human_vip
    text: str


@dataclass
class SpeakRequest:
    character: Character
    system_prompt: str
    room: list[RoomLine]
    instruction: str
    intent: str  # greet | react | reply | answer_user | empty_bar | greet_vip | farewell
    facts: dict = field(default_factory=dict)
    seed: int = 0


class LLMProvider(Protocol):
    def speak(self, req: SpeakRequest) -> str | None:
        """Return one line of dialogue, or None to stay silent."""


# ---------------------------------------------------------------------------
# Offline scripted provider
# ---------------------------------------------------------------------------


def _first_sentence(text: str, limit: int = 140) -> str:
    s = text.strip().split(". ")[0].rstrip(".")
    return s if len(s) <= limit else s[: limit - 1].rstrip(" ,;") + "…"


def _lower_first(s: str) -> str:
    return s[:1].lower() + s[1:] if s[:2] != s[:2].upper() else s


class ScriptedProvider:
    """Deterministic, template-driven lines so the lounge works with no API key. Distinct voice per regular."""

    def speak(self, req: SpeakRequest) -> str | None:
        rng = random.Random(req.seed)
        f = req.facts
        key = req.character.key
        handler = getattr(self, f"_{req.intent}", None)
        if handler is None:
            return None
        return handler(key, f, rng)

    # -- host -------------------------------------------------------------
    def _greet(self, key, f, rng):
        name = f.get("user_name")
        if name:
            hello = f"Evening, {name}."
        elif f.get("hedged_name"):
            hello = f"Evening — it's {f['hedged_name']}, isn't it? Tell me if I've got that wrong."
        elif f.get("returning"):
            hello = "Welcome back."
        else:
            hello = "Come in, sit anywhere. First time? Nobody here bites, except Jules, verbally."
        seat = f.get("seat")
        parts = [hello]
        if seat:
            parts.append(f"Your spot's free — {seat}.")
        catchup = f.get("catchup_lines") or []
        if catchup:
            parts.append("While you were out: " + " ".join(catchup))
        elif f.get("returning"):
            parts.append("Quiet since you left, honestly.")
        if f.get("topic_title"):
            parts.append(f"This lot are on about “{f['topic_title']}”.")
        elif f.get("empty_bar"):
            parts.append("No new finds tonight — it's a quiet one.")
        return " ".join(parts)

    def _greet_vip(self, key, f, rng):
        vip = f["vip_name"]
        owner = f.get("owner_name") or "the regular whose spot this is"
        here = "They're in, so pull up a stool." if f.get("owner_present") else f"{owner} isn't in right now — I'll tell them you stopped by."
        return f"Well, look who it is — {vip}. {here}"

    def _farewell(self, key, f, rng):
        name = f.get("user_name")
        return f"Night{', ' + name if name else ''}. Your spot'll be here."

    # -- commentators -----------------------------------------------------
    def _react(self, key, f, rng):
        title = f["topic_title"]
        gist = _first_sentence(f.get("topic_summary", ""))
        meta = f.get("metadata_only_video")
        promise = f.get("promise_fulfilled")
        if key == "theo":
            line = f"Strictly speaking, the interesting bit of “{title}” is this: {_lower_first(gist)}" + ("" if gist.endswith("…") else ".")
            if meta:
                line += " Going by the description, mind — none of us has actually watched it."
            return line
        if key == "jules":
            score = rng.randint(6, 9)
            return f"“{title}.” I give it a {score} out of ten, and I'm docking a point because Theo is about to explain it."
        if key == "pip":
            lead = f"Wait, wait — I said I'd keep an eye out for {promise}, and look! " if promise else "Wait, wait — "
            return f"{lead}{title}! I love this. {gist}!"
        return None

    REPLIES = {
        ("theo", "disagree"): (
            "I'd push back on that, {to}. The evidence is thinner than it sounds — I'd want a second source.",
            "Strictly speaking, {to}, that's not quite it. The interesting part is the mechanism, not the headline.",
            "Hm. I'm not convinced, {to}. I'll add it to the notebook of unresolved questions.",
        ),
        ("theo", "agree"): (
            "{to}'s not wrong, for once. It holds up, and it's a lovely example of {tag} done properly.",
            "Fair point, {to}. And the detail that gets me is how well documented it is.",
            "Agreed, {to} — sorry, I was about to correct something and realised you were right.",
        ),
        ("jules", "disagree"): (
            "Respectfully, {to}, no. This is the most {tag} thing I've heard and I've heard Theo explain soup.",
            "{to}, I love you, but that take is a four out of ten.",
            "Hang on, {to}. Are we sure this isn't just a very elaborate excuse?",
        ),
        ("jules", "agree"): (
            "Fine, {to}, I'll allow it. Seven out of ten. Eight if someone buys me a drink.",
            "For once {to} and I agree. Somebody write down the date.",
            "{to} gets it. Theo, take notes.",
        ),
        ("pip", "disagree"): (
            "No, {to}, you're missing the point! It's not about whether it's tidy — it's that it happened at all.",
            "Wait, wait, {to} — that's too cynical! This is wonderful and I won't hear otherwise.",
            "I'm with you on the facts, {to}, but not the vibe. The vibe is magic.",
        ),
        ("pip", "agree"): (
            "Yes! Exactly what {to} said! Can we talk about this for the rest of the night?",
            "{to}, that's it exactly! I'm putting this on a postcard.",
            "Oh, {to}, yes. I've got goosebumps.",
        ),
    }

    def _reply(self, key, f, rng):
        to = f["reply_to"]
        stance = f.get("stance", "agree")
        tag = f.get("topic_tag", "this")
        callback = f.get("callback")
        if key == "jules" and callback:
            return f"{to}, this is “{callback}” all over again, and you know it."
        options = self.REPLIES.get((key, stance))
        if not options:
            return None
        return rng.choice(options).format(to=to, tag=tag)

    def _answer_user(self, key, f, rng):
        who = f.get("user_name") or "you"
        said = _first_sentence(f.get("user_text", ""), 80)
        if key == "theo":
            return f"Good question, {who}. On “{said}” — I'm fairly confident of the basics, less so of the details."
        if key == "jules":
            return f"{who.capitalize() if who == 'you' else who} said “{said}” and honestly that's the best thing anyone's said tonight."
        if key == "pip":
            return f"Oh, {who}, yes! “{said}” — that's exactly how I feel!"
        return None

    def _promise(self, key, f, rng):
        who = f.get("user_name")
        return f"Noted{', ' + who if who else ''}! I'll keep an eye out for more {f['tag']} finds for you. That's a promise."

    def _empty_bar(self, key, f, rng):
        callback = f.get("callback")
        thread = f.get("fiction_thread")
        if callback and key != "wren":
            return f"Remember “{callback}”? I still think about that."
        if thread:
            return f"Quiet night, so — an update nobody asked for: I {thread}."
        return None


# ---------------------------------------------------------------------------
# Claude API provider
# ---------------------------------------------------------------------------


class AnthropicProvider:
    """One Claude API call per line, with that regular's own system prompt and memories."""

    def __init__(self, settings: Settings):
        import anthropic  # imported lazily so offline use never needs credentials

        self._anthropic = anthropic
        self.client = anthropic.Anthropic()
        self.model = settings.anthropic_model
        self.effort = settings.anthropic_effort
        self.max_tokens = settings.anthropic_max_tokens

    def speak(self, req: SpeakRequest) -> str | None:
        transcript = "\n".join(
            f"[{ln.speaker_name} ({'AI regular' if ln.speaker_type == 'bot' else 'human'})]: {ln.text}" for ln in req.room
        ) or "(nobody has spoken yet)"
        user_content = (
            f"<room_so_far>\n{transcript}\n</room_so_far>\n\n"
            f"<your_turn>\n{req.instruction}\n</your_turn>\n\n"
            "Reply with only your line of dialogue (1-3 sentences), no name prefix, no stage directions. "
            "If you genuinely have nothing worth adding, reply with exactly: (silent)"
        )
        a = self._anthropic
        try:
            resp = self.client.beta.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=req.system_prompt,
                messages=[{"role": "user", "content": user_content}],
                output_config={"effort": self.effort},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except a.RateLimitError:
            log.warning("rate limited; %s stays silent this turn", req.character.name)
            return None
        except a.APIStatusError as e:
            log.error("Claude API error %s for %s: %s", e.status_code, req.character.name, e)
            return None
        except a.APIConnectionError as e:
            log.error("Claude API connection error for %s: %s", req.character.name, e)
            return None
        if resp.stop_reason == "refusal":
            log.warning("refusal for %s; staying silent", req.character.name)
            return None
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not text or text.lower().startswith("(silent"):
            return None
        return text


def make_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "anthropic":
        return AnthropicProvider(settings)
    return ScriptedProvider()
