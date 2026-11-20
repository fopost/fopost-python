from __future__ import annotations

import json

import httpx
import pytest
import respx

from fopost import Fopost, PaymentRequiredError, VideoEditOperation
from tests.conftest import BASE_URL

EDIT = {
    "id": "ve_1",
    "status": "succeeded",
    "progress": 1,
    "source_media_id": "med_1",
    "operations": [{"op": "trim", "params": {"start": 0, "end": 10}}],
    "result_media_id": "med_2",
    "result_media": {
        "id": "med_2",
        "preview_url": "https://api.test.fopost.com/v1/media/med_2/file",
        "mime_type": "video/mp4",
    },
    "extra_outputs": [{"media_id": "med_3", "label": "Captions", "mime": "text/vtt"}],
    "result": {},
    "error": None,
    "created_at": "2026-11-20T10:00:00.000Z",
    "updated_at": "2026-11-20T10:01:00.000Z",
    "completed_at": "2026-11-20T10:01:00.000Z",
}


@respx.mock
def test_ops(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/video-edits/ops").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {"name": "trim", "available": True, "uses_ai": False},
                    {"name": "subtitles", "available": False, "uses_ai": True},
                ]
            },
        )
    )

    ops = client.video_edits.ops()

    assert route.called
    assert [o.name for o in ops] == ["trim", "subtitles"]
    assert ops[1].uses_ai is True and ops[1].available is False


@respx.mock
def test_list_sends_filters(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/video-edits").mock(
        return_value=httpx.Response(200, json={"data": [EDIT]})
    )

    edits = client.video_edits.list(workspace_id="ws_1", media_id="med_1", limit=5)

    assert dict(route.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "media_id": "med_1",
        "limit": "5",
    }
    assert edits[0].id == "ve_1"
    assert edits[0].result_media is not None and edits[0].result_media.mime_type == "video/mp4"


@respx.mock
def test_create_sends_operations_in_order(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/video-edits").mock(
        return_value=httpx.Response(201, json={**EDIT, "status": "queued", "progress": 0})
    )

    edit = client.video_edits.create(
        workspace_id="ws_1",
        media_id="med_1",
        operations=[
            {"op": "trim", "params": {"start": 0, "end": 10}},
            VideoEditOperation(op="denoise"),
            {"op": "remove_silence"},
        ],
    )

    assert json.loads(route.calls.last.request.content) == {
        "media_id": "med_1",
        "operations": [
            {"op": "trim", "params": {"start": 0, "end": 10}},
            {"op": "denoise", "params": {}},
            {"op": "remove_silence"},
        ],
        "workspace_id": "ws_1",
    }
    assert edit.status == "queued"
    assert edit.operations[0].params == {"start": 0, "end": 10}


@respx.mock
def test_get(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/video-edits/ve_1").mock(
        return_value=httpx.Response(200, json=EDIT)
    )

    edit = client.video_edits.get("ve_1", workspace_id="ws_1")

    assert dict(route.calls.last.request.url.params) == {"workspace_id": "ws_1"}
    assert edit.result_media_id == "med_2"
    assert edit.extra_outputs[0].label == "Captions"
    assert edit.completed_at is not None


@respx.mock
def test_an_empty_balance_raises_payment_required(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/video-edits").mock(
        return_value=httpx.Response(
            402,
            json={
                "error": "insufficient_credits",
                "message": "Your AI balance is empty.",
                "upgrade_url": "/settings/billing",
            },
        )
    )

    with pytest.raises(PaymentRequiredError) as excinfo:
        client.video_edits.create(media_id="med_1", operations=[{"op": "subtitles"}])

    assert excinfo.value.upgrade_url == "/settings/billing"
