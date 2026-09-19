from __future__ import annotations

import json

import httpx
import pytest
import respx

from fopost import Fopost, FopostError, NotFoundError
from tests.conftest import API_KEY, BASE_URL

UPLOAD_URL = "https://storage.test.fopost.com/uploads/up_1?sig=abc"

PRESIGN_FIXTURE = {
    "uploadId": "up_1",
    "uploadUrl": UPLOAD_URL,
    "method": "PUT",
    "headers": {"Content-Type": "image/png"},
    "expiresAt": "2026-09-19T12:00:00.000Z",
}

MEDIA_FIXTURE = {
    "id": "med_1",
    "type": "image",
    "name": "chart.png",
    "url": "media/ws_1/med_1.png",
    "previewUrl": "https://api.test.fopost.com/v1/media/med_1/file",
    "size": 4,
}


@respx.mock
def test_presign_sends_the_declared_file_and_returns_the_slot(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/media/presign").mock(
        return_value=httpx.Response(201, json={"data": PRESIGN_FIXTURE})
    )

    slot = client.media.presign(
        workspace_id="ws_1", filename="chart.png", mime_type="image/png", size=4
    )

    assert slot.upload_id == "up_1"
    assert slot.upload_url == UPLOAD_URL
    assert slot.headers == {"Content-Type": "image/png"}
    assert slot.expires_at is not None
    assert json.loads(route.calls.last.request.content) == {
        "workspaceId": "ws_1",
        "filename": "chart.png",
        "mimeType": "image/png",
        "size": 4,
    }


@respx.mock
def test_complete_returns_the_media_item(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/media/presign/up_1/complete").mock(
        return_value=httpx.Response(201, json={"data": MEDIA_FIXTURE})
    )

    item = client.media.complete("up_1")

    assert item.id == "med_1"
    assert item.type == "image"
    assert item.preview_url == MEDIA_FIXTURE["previewUrl"]
    assert item.size == 4
    assert route.calls.last.request.headers["x-api-key"] == API_KEY


@respx.mock
def test_upload_direct_presigns_puts_the_bytes_and_completes(client: Fopost) -> None:
    presign = respx.post(f"{BASE_URL}/media/presign").mock(
        return_value=httpx.Response(201, json={"data": PRESIGN_FIXTURE})
    )
    put = respx.put(UPLOAD_URL).mock(return_value=httpx.Response(200))
    complete = respx.post(f"{BASE_URL}/media/presign/up_1/complete").mock(
        return_value=httpx.Response(201, json={"data": MEDIA_FIXTURE})
    )

    item = client.media.upload_direct(
        workspace_id="ws_1", filename="chart.png", mime_type="image/png", data=b"\x89PNG"
    )

    assert item.id == "med_1"
    assert presign.called and put.called and complete.called
    assert json.loads(presign.calls.last.request.content)["size"] == 4

    upload = put.calls.last.request
    assert upload.content == b"\x89PNG"
    assert upload.headers["content-type"] == "image/png"
    assert upload.headers["content-length"] == "4"
    assert "x-api-key" not in upload.headers


@respx.mock
def test_upload_direct_raises_on_a_failed_put_and_never_completes(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/media/presign").mock(
        return_value=httpx.Response(201, json={"data": PRESIGN_FIXTURE})
    )
    respx.put(UPLOAD_URL).mock(return_value=httpx.Response(403, text="SignatureDoesNotMatch"))
    complete = respx.post(f"{BASE_URL}/media/presign/up_1/complete")

    with pytest.raises(FopostError) as excinfo:
        client.media.upload_direct(
            workspace_id="ws_1", filename="chart.png", mime_type="image/png", data=b"\x89PNG"
        )

    assert excinfo.value.status == 403
    assert not complete.called


@respx.mock
def test_complete_maps_an_unknown_upload_to_not_found(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/media/presign/nope/complete").mock(
        return_value=httpx.Response(404, json={"error": "not_found", "message": "Unknown upload."})
    )

    with pytest.raises(NotFoundError):
        client.media.complete("nope")
