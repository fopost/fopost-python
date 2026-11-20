from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

DOCUMENT = {"version": 1, "width": 1080, "height": 1080, "pages": [{"elements": []}]}

DESIGN = {
    "id": "des_1",
    "name": "Launch",
    "kind": "post",
    "width": 1080,
    "height": 1080,
    "document": DOCUMENT,
    "thumbnail_media_id": "med_9",
    "thumbnail_url": "https://api.test.fopost.com/v1/media/med_9/file",
    "created_at": "2026-11-20T10:00:00.000Z",
    "updated_at": "2026-11-20T10:05:00.000Z",
}

VERSION = {"id": "ver_1", "version": 3, "created_at": "2026-11-20T10:05:00.000Z"}


@respx.mock
def test_list_sends_filters_and_maps_designs(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/designs").mock(
        return_value=httpx.Response(200, json={"data": [{**DESIGN, "document": None}]})
    )

    designs = client.designs.list(workspace_id="ws_1", kind="post", limit=10, offset=20)

    assert dict(route.calls.last.request.url.params) == {
        "workspace_id": "ws_1",
        "kind": "post",
        "limit": "10",
        "offset": "20",
    }
    assert designs[0].id == "des_1"
    assert designs[0].thumbnail_media_id == "med_9"
    assert designs[0].document is None


@respx.mock
def test_create_sends_the_document_through(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/designs").mock(
        return_value=httpx.Response(201, json={"data": DESIGN})
    )

    design = client.designs.create(
        workspace_id="ws_1", kind="post", name="Launch", document=DOCUMENT, brand_voice_id="bv_1"
    )

    assert json.loads(route.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "kind": "post",
        "name": "Launch",
        "document": DOCUMENT,
        "brand_voice_id": "bv_1",
    }
    assert design.document == DOCUMENT
    assert design.kind == "post"


@respx.mock
def test_get(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/designs/des_1").mock(
        return_value=httpx.Response(200, json={"data": DESIGN})
    )

    design = client.designs.get("des_1")

    assert route.called
    assert design.width == 1080 and design.updated_at is not None


@respx.mock
def test_update_patches_only_what_was_passed_and_returns_the_version(client: Fopost) -> None:
    route = respx.patch(f"{BASE_URL}/designs/des_1").mock(
        return_value=httpx.Response(200, json={"data": DESIGN, "version": VERSION})
    )

    result = client.designs.update("des_1", document=DOCUMENT, create_version=True)

    assert json.loads(route.calls.last.request.content) == {
        "document": DOCUMENT,
        "create_version": True,
    }
    assert result.design.id == "des_1"
    assert result.version is not None and result.version.version == 3


@respx.mock
def test_update_without_a_version(client: Fopost) -> None:
    route = respx.patch(f"{BASE_URL}/designs/des_1").mock(
        return_value=httpx.Response(200, json={"data": DESIGN, "version": None})
    )

    result = client.designs.update("des_1", name="Renamed")

    assert json.loads(route.calls.last.request.content) == {"name": "Renamed"}
    assert result.version is None


@respx.mock
def test_delete(client: Fopost) -> None:
    route = respx.delete(f"{BASE_URL}/designs/des_1").mock(
        return_value=httpx.Response(200, json={"data": {"id": "des_1", "deleted": True}})
    )

    result = client.designs.delete("des_1")

    assert route.called
    assert result.id == "des_1" and result.deleted is True


@respx.mock
def test_versions_and_restore(client: Fopost) -> None:
    listed = respx.get(f"{BASE_URL}/designs/des_1/versions").mock(
        return_value=httpx.Response(200, json={"data": [{**VERSION, "document": DOCUMENT}]})
    )
    restored = respx.post(f"{BASE_URL}/designs/des_1/versions/ver_1/restore").mock(
        return_value=httpx.Response(200, json={"data": DESIGN, "version": VERSION})
    )

    versions = client.designs.versions("des_1", include_document=True)
    assert dict(listed.calls.last.request.url.params) == {"include": "document"}
    assert versions[0].document == DOCUMENT

    client.designs.versions("des_1")
    assert dict(listed.calls.last.request.url.params) == {}

    result = client.designs.restore_version("des_1", "ver_1")
    assert restored.called
    assert result.design.id == "des_1" and result.version is not None


@respx.mock
def test_duplicate(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/designs/des_1/duplicate").mock(
        return_value=httpx.Response(201, json={"data": {**DESIGN, "id": "des_2"}})
    )

    copy = client.designs.duplicate("des_1", name="Copy")

    assert json.loads(route.calls.last.request.content) == {"name": "Copy"}
    assert copy.id == "des_2"


@respx.mock
def test_export(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/designs/des_1/export").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "format": "png",
                    "files": [
                        {
                            "media_id": "med_1",
                            "page_index": 0,
                            "mime_type": "image/png",
                            "preview_url": "https://api.test.fopost.com/v1/media/med_1/file",
                        }
                    ],
                }
            },
        )
    )

    export = client.designs.export("des_1", format="png", page_indexes=[0], duration_sec=5)

    assert json.loads(route.calls.last.request.content) == {
        "format": "png",
        "page_indexes": [0],
        "duration_sec": 5,
    }
    assert export.format == "png"
    assert export.files[0].media_id == "med_1"
    assert export.files[0].page_index == 0


@respx.mock
def test_bulk_create(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/designs/des_1/bulk").mock(
        return_value=httpx.Response(201, json={"data": [DESIGN, {**DESIGN, "id": "des_3"}]})
    )

    designs = client.designs.bulk_create(
        "des_1", rows=[{"name": "A", "headline": "Hi"}, {"name": "B"}], name_column="name"
    )

    assert json.loads(route.calls.last.request.content) == {
        "rows": [{"name": "A", "headline": "Hi"}, {"name": "B"}],
        "name_column": "name",
    }
    assert [d.id for d in designs] == ["des_1", "des_3"]


@respx.mock
def test_posts(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/designs/des_1/posts").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "post_1",
                        "status": "published",
                        "title": None,
                        "text": "Launch",
                        "schedule_at": None,
                        "published_at": "2026-11-20T12:00:00.000Z",
                        "platforms": ["twitter"],
                        "engagement": 12,
                        "views": 300,
                    }
                ]
            },
        )
    )

    posts = client.designs.posts("des_1")

    assert route.called
    assert posts[0].status == "published"
    assert posts[0].platforms == ["twitter"] and posts[0].views == 300


@respx.mock
def test_text_to_slides(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/designs/text-to-slides").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "cover": {"title": "Five tips", "subtitle": "For launch day"},
                    "slides": [{"heading": "One", "body": "Plan early"}],
                    "cta": {"heading": "Follow", "body": "for more"},
                    "brand": {"colors": ["#111111"], "fonts": {}, "logo_media_id": None},
                }
            },
        )
    )

    result = client.designs.text_to_slides(workspace_id="ws_1", text="Some notes", max_slides=5)

    assert json.loads(route.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "text": "Some notes",
        "max_slides": 5,
    }
    assert result.cover is not None and result.cover.title == "Five tips"
    assert result.slides[0].body == "Plan early"
    assert result.brand is not None and result.brand.colors == ["#111111"]


@respx.mock
def test_from_post(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/designs/from-post").mock(
        return_value=httpx.Response(201, json={"data": {**DESIGN, "kind": "carousel"}})
    )

    design = client.designs.from_post(
        workspace_id="ws_1", post_id="post_1", style="quote", carousel=True
    )

    assert json.loads(route.calls.last.request.content) == {
        "workspace_id": "ws_1",
        "post_id": "post_1",
        "style": "quote",
        "carousel": True,
    }
    assert design.kind == "carousel"
