from __future__ import annotations

import io
import json

import httpx
import respx

from fopost import FileTooLargeError, Fopost
from tests.conftest import BASE_URL, POST_FIXTURE

UPLOAD_URL = "https://storage.test.fopost.com/uploads/up_1?sig=abc"

LIMITS = {
    "maxFileBytes": 5368709120,
    "source": "add_on",
    "connectedAccounts": 2,
    "largeUploadsEnabled": True,
    "nextTier": None,
    "multipartMaxFileBytes": 16,
    "maxFilesPerUpload": 5,
    "directUploadAvailable": True,
    "allowedTypes": ["image/png", "video/mp4"],
}

PRESIGN = {
    "uploadId": "up_1",
    "uploadUrl": UPLOAD_URL,
    "method": "PUT",
    "headers": {"Content-Type": "video/mp4"},
    "maxFileBytes": 5368709120,
}

MEDIA = {
    "id": "med_1",
    "type": "video",
    "name": "clip.mp4",
    "url": "media/ws_1/med_1.mp4",
    "size": 32,
}


@respx.mock
def test_create_sends_one_multipart_request_when_every_file_fits(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/media/limits").mock(
        return_value=httpx.Response(200, json={"data": LIMITS})
    )
    create = respx.post(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(201, json=POST_FIXTURE)
    )
    presign = respx.post(f"{BASE_URL}/media/presign")

    post = client.posts.create(
        workspace_id="ws_1",
        content="Hello",
        accounts=["acc_1"],
        files=[("chart.png", b"\x89PNG", "image/png"), io.BytesIO(b"\x00" * 16)],
    )

    assert post.id == "post_1"
    assert not presign.called
    request = create.calls.last.request
    content_type = request.headers["content-type"]
    assert content_type.startswith("multipart/form-data; boundary=")
    raw = request.content
    assert b'name="post"' in raw
    assert b'name="files"; filename="chart.png"' in raw
    assert b"Content-Type: image/png" in raw
    assert b'name="files"; filename="upload"' in raw
    start = raw.index(b'name="post"')
    body_json = raw[start:].split(b"\r\n\r\n", 1)[1].split(b"\r\n--", 1)[0]
    assert json.loads(body_json) == {
        "workspace_id": "ws_1",
        "status": "draft",
        "content": [{"text": "Hello"}],
        "accounts": ["acc_1"],
    }


@respx.mock
def test_create_uploads_directly_and_attaches_media_when_a_file_is_too_big(
    client: Fopost,
) -> None:
    respx.get(f"{BASE_URL}/media/limits").mock(
        return_value=httpx.Response(200, json={"data": LIMITS})
    )
    presign = respx.post(f"{BASE_URL}/media/presign").mock(
        return_value=httpx.Response(201, json={"data": PRESIGN})
    )
    put = respx.put(UPLOAD_URL).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE_URL}/media/presign/up_1/complete").mock(
        return_value=httpx.Response(201, json={"data": MEDIA})
    )
    create = respx.post(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(201, json=POST_FIXTURE)
    )

    client.posts.create(
        workspace_id="ws_1",
        content="Hello",
        accounts=["acc_1"],
        files=[("clip.mp4", b"\x00" * 32, "video/mp4")],
    )

    assert json.loads(presign.calls.last.request.content) == {
        "workspaceId": "ws_1",
        "filename": "clip.mp4",
        "mimeType": "video/mp4",
        "size": 32,
    }
    assert put.calls.last.request.content == b"\x00" * 32
    request = create.calls.last.request
    assert request.headers["content-type"] == "application/json"
    assert json.loads(request.content) == {
        "workspace_id": "ws_1",
        "status": "draft",
        "content": [
            {
                "text": "Hello",
                "media": [
                    {
                        "type": "video",
                        "name": "clip.mp4",
                        "url": "media/ws_1/med_1.mp4",
                        "size": 32,
                    }
                ],
            }
        ],
        "accounts": ["acc_1"],
    }


@respx.mock
def test_create_falls_back_to_the_default_ceiling_when_limits_fail(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/media/limits").mock(return_value=httpx.Response(500))
    create = respx.post(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(201, json=POST_FIXTURE)
    )

    client.posts.create(
        workspace_id="ws_1", content="Hello", files=[("clip.mp4", b"\x00" * 32, "video/mp4")]
    )

    assert create.calls.last.request.headers["content-type"].startswith("multipart/form-data")


@respx.mock
def test_update_without_content_appends_to_the_existing_first_block(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/media/limits").mock(
        return_value=httpx.Response(200, json={"data": LIMITS})
    )
    respx.get(f"{BASE_URL}/posts/post_1").mock(return_value=httpx.Response(200, json=POST_FIXTURE))
    respx.post(f"{BASE_URL}/media/presign").mock(
        return_value=httpx.Response(201, json={"data": PRESIGN})
    )
    respx.put(UPLOAD_URL).mock(return_value=httpx.Response(200))
    respx.post(f"{BASE_URL}/media/presign/up_1/complete").mock(
        return_value=httpx.Response(201, json={"data": MEDIA})
    )
    update = respx.put(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(200, json=POST_FIXTURE)
    )

    client.posts.update("post_1", files=[("clip.mp4", b"\x00" * 32, "video/mp4")])

    body = json.loads(update.calls.last.request.content)
    assert body["content"][0]["text"] == "Hello from Python"
    assert body["content"][0]["media"] == [
        {"type": "video", "name": "clip.mp4", "url": "media/ws_1/med_1.mp4", "size": 32}
    ]


@respx.mock
def test_update_with_small_files_is_one_multipart_put(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/media/limits").mock(
        return_value=httpx.Response(200, json={"data": LIMITS})
    )
    get = respx.get(f"{BASE_URL}/posts/post_1")
    update = respx.put(f"{BASE_URL}/posts/post_1").mock(
        return_value=httpx.Response(200, json=POST_FIXTURE)
    )

    client.posts.update("post_1", title="Renamed", files=[("a.png", b"\x89PNG", "image/png")])

    assert not get.called
    raw = update.calls.last.request.content
    assert b'name="files"; filename="a.png"' in raw
    assert b'"title": "Renamed"' in raw


@respx.mock
def test_a_413_from_the_post_endpoint_is_file_too_large(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/media/limits").mock(
        return_value=httpx.Response(200, json={"data": LIMITS})
    )
    respx.post(f"{BASE_URL}/posts").mock(
        return_value=httpx.Response(
            413,
            json={
                "error": "file_too_large",
                "message": "Too big.",
                "max_file_bytes": 104857600,
                "file_bytes": 4,
                "upgrade_url": "/settings/billing",
            },
        )
    )

    try:
        client.posts.create(
            workspace_id="ws_1", content="x", files=[("a.png", b"\x89PNG", "image/png")]
        )
    except FileTooLargeError as error:
        assert error.status == 413
        assert error.max_file_bytes == 104857600
    else:
        raise AssertionError("expected FileTooLargeError")
