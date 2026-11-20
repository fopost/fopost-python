from __future__ import annotations

from pathlib import Path

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

UPLOADED = {
    "id": "fnt_1",
    "family": "Brand Sans",
    "style": "normal",
    "weight": 700,
    "format": "woff2",
    "file_url": "https://api.test.fopost.com/v1/fonts/fnt_1/file",
    "created_at": "2026-11-20T10:00:00.000Z",
}


@respx.mock
def test_list_returns_library_and_uploads(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/fonts").mock(
        return_value=httpx.Response(
            200,
            json={
                "library": [
                    {
                        "slug": "geist",
                        "family": "Geist",
                        "category": "sans-serif",
                        "scripts": ["latin"],
                        "weights": [400, 700],
                        "files": [{"path": "geist.woff2", "subset": "latin", "weight": 400}],
                    }
                ],
                "uploaded": [UPLOADED],
            },
        )
    )

    fonts = client.fonts.list(workspace_id="ws_1")

    assert dict(route.calls.last.request.url.params) == {"workspace_id": "ws_1"}
    assert fonts.library[0].slug == "geist"
    assert fonts.library[0].files[0].subset == "latin"
    assert fonts.uploaded[0].id == "fnt_1"
    assert fonts.uploaded[0].weight == 700


@respx.mock
def test_upload_from_bytes_sends_multipart(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/fonts").mock(return_value=httpx.Response(201, json=UPLOADED))

    font = client.fonts.upload(
        workspace_id="ws_1",
        file=("brand.woff2", b"wOF2", "font/woff2"),
        family="Brand Sans",
        weight=700,
        style="normal",
    )

    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data")
    assert b'name="workspace_id"\r\n\r\nws_1' in request.content
    assert b'name="family"\r\n\r\nBrand Sans' in request.content
    assert b'name="weight"\r\n\r\n700' in request.content
    assert b'name="style"\r\n\r\nnormal' in request.content
    assert b'name="file"; filename="brand.woff2"' in request.content
    assert b"wOF2" in request.content
    assert font.id == "fnt_1" and font.family == "Brand Sans"


@respx.mock
def test_upload_from_a_path(client: Fopost, tmp_path: Path) -> None:
    path = tmp_path / "brand.ttf"
    path.write_bytes(b"\x00\x01\x00\x00")
    route = respx.post(f"{BASE_URL}/fonts").mock(return_value=httpx.Response(201, json=UPLOADED))

    client.fonts.upload(workspace_id="ws_1", file=path)

    content = route.calls.last.request.content
    assert b'name="file"; filename="brand.ttf"' in content
    assert b'name="family"' not in content


@respx.mock
def test_delete(client: Fopost) -> None:
    route = respx.delete(f"{BASE_URL}/fonts/fnt_1").mock(return_value=httpx.Response(204))

    assert client.fonts.delete("fnt_1") is None
    assert route.called
