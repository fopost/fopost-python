from __future__ import annotations

import json

import httpx
import pytest
import respx

from fopost import FileTooLargeError, Fopost, FopostError, NotFoundError
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


LIMITS_FIXTURE = {
    "maxFileBytes": 104857600,
    "source": "accounts",
    "connectedAccounts": 2,
    "largeUploadsEnabled": False,
    "nextTier": {"upToAccounts": 7, "maxFileBytes": 419430400},
    "multipartMaxFileBytes": 104857600,
    "maxFilesPerUpload": 5,
    "directUploadAvailable": True,
    "allowedTypes": ["image/png", "video/mp4"],
}


@respx.mock
def test_limits_reads_the_ceilings_for_a_workspace(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/media/limits").mock(
        return_value=httpx.Response(200, json={"data": LIMITS_FIXTURE})
    )

    limits = client.media.limits(workspace_id="ws_1")

    assert dict(route.calls.last.request.url.params) == {"workspaceId": "ws_1"}
    assert route.calls.last.request.headers["x-api-key"] == API_KEY
    assert limits.max_file_bytes == 104857600
    assert limits.source == "accounts"
    assert limits.multipart_max_file_bytes == 104857600
    assert limits.max_files_per_upload == 5
    assert limits.next_tier is not None
    assert limits.next_tier.up_to_accounts == 7
    assert limits.next_tier.max_file_bytes == 419430400
    assert limits.allowed_types == ["image/png", "video/mp4"]


@respx.mock
def test_limits_without_a_workspace_sends_no_query(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/media/limits").mock(
        return_value=httpx.Response(200, json={"data": LIMITS_FIXTURE})
    )

    client.media.limits()

    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
def test_presign_sends_the_optional_fields_and_reads_max_file_bytes(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/media/presign").mock(
        return_value=httpx.Response(
            201, json={"data": {**PRESIGN_FIXTURE, "maxFileBytes": 5368709120}}
        )
    )

    slot = client.media.presign(
        workspace_id="ws_1",
        filename="clip.mp4",
        mime_type="video/mp4",
        size=5368709120,
        folder_id="fld_1",
        origin="chat",
        brand_role="person",
        brand_voice_id="bv_1",
        person_consent={"subject": "Jane", "statement": "I agree"},
    )

    assert slot.max_file_bytes == 5368709120
    assert json.loads(route.calls.last.request.content) == {
        "workspaceId": "ws_1",
        "filename": "clip.mp4",
        "mimeType": "video/mp4",
        "size": 5368709120,
        "folderId": "fld_1",
        "origin": "chat",
        "brandRole": "person",
        "brandVoiceId": "bv_1",
        "personConsent": {"subject": "Jane", "statement": "I agree"},
    }


@respx.mock
def test_a_413_surfaces_as_file_too_large_with_the_ceiling(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/media/presign").mock(
        return_value=httpx.Response(
            413,
            json={
                "error": "file_too_large",
                "message": "This file is over your upload limit.",
                "max_file_bytes": 104857600,
                "file_bytes": 209715200,
                "upgrade_url": "/settings/billing",
            },
        )
    )

    with pytest.raises(FileTooLargeError) as excinfo:
        client.media.presign(
            workspace_id="ws_1", filename="big.mp4", mime_type="video/mp4", size=209715200
        )

    error = excinfo.value
    assert isinstance(error, FopostError)
    assert error.status == 413
    assert error.code == "file_too_large"
    assert error.max_file_bytes == 104857600
    assert error.file_bytes == 209715200
    assert error.upgrade_url == "/settings/billing"
    assert error.body["max_file_bytes"] == 104857600
