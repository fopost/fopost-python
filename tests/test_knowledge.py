from __future__ import annotations

import httpx
import respx

from fopost import Fopost, KnowledgeMatch, KnowledgeSource
from tests.conftest import BASE_URL

SOURCE_FIXTURE = {
    "id": "know_1",
    "kind": "url",
    "title": "Refund policy",
    "status": "ready",
    "statusMessage": None,
    "url": "https://yourbrand.com/help/refunds",
    "mediaId": None,
    "brandVoiceId": None,
    "chunkCount": 3,
    "content": None,
    "lastSyncedAt": "2026-09-20T00:00:00.000Z",
    "createdAt": "2026-09-19T00:00:00.000Z",
    "updatedAt": "2026-09-20T00:00:00.000Z",
}


@respx.mock
def test_list_reads_camel_case_fields_into_snake_case(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/knowledge/sources").mock(
        return_value=httpx.Response(200, json={"data": [SOURCE_FIXTURE]})
    )

    sources = client.knowledge.list(workspace_id="ws_1")

    assert len(sources) == 1
    assert isinstance(sources[0], KnowledgeSource)
    assert sources[0].chunk_count == 3
    assert sources[0].status == "ready"
    assert sources[0].status_message is None
    assert dict(route.calls.last.request.url.params) == {"workspace_id": "ws_1"}


@respx.mock
def test_create_sends_a_snake_case_body(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/knowledge/sources").mock(
        return_value=httpx.Response(200, json={"data": SOURCE_FIXTURE})
    )

    client.knowledge.create(
        kind="file",
        title="Price list",
        media_id="media_1",
        brand_voice_id="brand_1",
        workspace_id="ws_1",
    )

    assert route.calls.last.request.read() == (
        b'{"kind":"file","title":"Price list","content":null,"url":null,'
        b'"media_id":"media_1","brand_voice_id":"brand_1","workspace_id":"ws_1"}'
    )


@respx.mock
def test_search_passes_top_k_and_parses_matches(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/knowledge/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "sourceId": "know_1",
                        "sourceTitle": "Refund policy",
                        "sourceKind": "url",
                        "sourceUrl": "https://yourbrand.com/help/refunds",
                        "text": "We refund within 30 days.",
                        "score": 0.82,
                    }
                ]
            },
        )
    )

    matches = client.knowledge.search("how long do refunds take?", top_k=3)

    assert len(matches) == 1
    assert isinstance(matches[0], KnowledgeMatch)
    assert matches[0].source_title == "Refund policy"
    assert matches[0].score == 0.82
    assert dict(route.calls.last.request.url.params) == {
        "q": "how long do refunds take?",
        "top_k": "3",
    }


@respx.mock
def test_sync_queues_a_reindex(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/knowledge/sources/know_1/sync").mock(
        return_value=httpx.Response(200, json={"data": {"id": "know_1", "status": "pending"}})
    )

    assert client.knowledge.sync("know_1").status == "pending"
