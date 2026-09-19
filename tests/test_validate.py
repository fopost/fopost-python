from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL


@respx.mock
def test_post_sends_the_body_and_parses_each_platform(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/validate/post").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "ready": False,
                    "platforms": [
                        {
                            "platform": "linkedin",
                            "ready": False,
                            "issues": ["Unsupported media type: image/webp"],
                            "score": 95,
                            "signals": [{"level": "info", "code": "no_emoji", "message": "x"}],
                        }
                    ],
                }
            },
        )
    )

    result = client.validate.post(
        content="hi",
        media=[{"url": "https://cdn.example.com/a.webp", "mime_type": "image/webp"}],
        platforms=["linkedin"],
    )

    assert result.ready is False
    assert result.platforms[0].issues == ["Unsupported media type: image/webp"]
    assert result.platforms[0].signals[0].code == "no_emoji"
    assert json.loads(route.calls.last.request.content) == {
        "platforms": ["linkedin"],
        "content": "hi",
        "media": [{"url": "https://cdn.example.com/a.webp", "mime_type": "image/webp"}],
    }


@respx.mock
def test_length_reports_the_limit_per_platform(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/validate/length").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "ok": False,
                    "platforms": [
                        {
                            "platform": "bluesky",
                            "length": 320,
                            "limit": 300,
                            "unit": "chars",
                            "ok": False,
                            "signals": [{"level": "warn", "code": "over_length", "message": "x"}],
                        }
                    ],
                }
            },
        )
    )

    result = client.validate.length(text="x" * 320, platforms=["bluesky"])

    assert result.ok is False
    assert result.platforms[0].limit == 300
    assert json.loads(route.calls.last.request.content) == {
        "text": "x" * 320,
        "platforms": ["bluesky"],
    }


@respx.mock
def test_media_returns_the_verified_type(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/validate/media").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "ok": True,
                    "issues": [],
                    "name": "a.png",
                    "size": 12,
                    "mime_type": "image/png",
                    "type": "image",
                }
            },
        )
    )

    result = client.validate.media(url="https://cdn.example.com/a.png")

    assert result.ok is True
    assert result.mime_type == "image/png"
    assert result.type == "image"
