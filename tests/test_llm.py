"""The Claude provider builds the request we intend, without touching the network."""

import json

import anthropic
import httpx2

from voidgrid.characters import JULES
from voidgrid.llm import AnthropicProvider, RoomLine, SpeakRequest


def _provider(handler):
    p = AnthropicProvider.__new__(AnthropicProvider)
    p._anthropic = anthropic
    p.client = anthropic.Anthropic(api_key="test", max_retries=0,
                                   http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)))
    p.model, p.effort, p.max_tokens = "claude-opus-5-5", "low", 2000
    return p


def _msg(text, stop="end_turn"):
    return {"id": "m", "type": "message", "role": "assistant", "model": "claude-opus-5-5",
            "content": [{"type": "text", "text": text}] if text else [], "stop_reason": stop,
            "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 1}}


REQ = SpeakRequest(character=JULES, system_prompt="sys", room=[RoomLine("Theo", "bot", "Hello")], instruction="Reply.", intent="reply")


def test_request_shape():
    seen = {}

    def handler(req):
        seen["body"] = json.loads(req.content)
        seen["beta"] = req.headers.get("anthropic-beta")
        return httpx2.Response(200, json=_msg("Seven out of ten, Theo."))

    assert _provider(handler).speak(REQ) == "Seven out of ten, Theo."
    b = seen["body"]
    assert b["model"] == "claude-opus-5-5" and b["output_config"] == {"effort": "low"}
    assert b["fallbacks"] == "default" and seen["beta"] == "server-side-fallback-2026-07-01"
    assert b["system"] == "sys" and "[Theo (AI regular)]: Hello" in b["messages"][0]["content"]


def test_silence_refusal_and_errors_become_none():
    assert _provider(lambda r: httpx2.Response(200, json=_msg("(silent)"))).speak(REQ) is None
    assert _provider(lambda r: httpx2.Response(200, json=_msg("", stop="refusal"))).speak(REQ) is None
    assert _provider(lambda r: httpx2.Response(500, json={"type": "error", "error": {"type": "api_error", "message": "x"}})).speak(REQ) is None
