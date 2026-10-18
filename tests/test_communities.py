from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

COMMUNITY = {
    "id": 5,
    "account_id": "acc_1",
    "community_id": "1700000000000000000",
    "name": "Builders",
    "member_count": 1200,
    "description": None,
    "image_url": None,
    "last_synced_at": "2026-10-18T12:00:00.000Z",
    "created_at": "2026-10-18T12:00:00.000Z",
}


@respx.mock
def test_communities_list_sync_search_add_and_remove(client: Fopost) -> None:
    listed = respx.get(f"{BASE_URL}/accounts/acc_1/communities").mock(
        return_value=httpx.Response(200, json={"data": [COMMUNITY]})
    )
    synced = respx.post(f"{BASE_URL}/accounts/acc_1/communities/sync").mock(
        return_value=httpx.Response(200, json={"data": [COMMUNITY], "note": "stored list"})
    )
    searched = respx.get(f"{BASE_URL}/accounts/acc_1/communities/search").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "17", "name": "Makers", "description": "", "member_count": 9}]},
        )
    )
    added = respx.post(f"{BASE_URL}/accounts/acc_1/communities/manual").mock(
        return_value=httpx.Response(201, json=COMMUNITY)
    )
    removed = respx.delete(f"{BASE_URL}/accounts/acc_1/communities/5").mock(
        return_value=httpx.Response(204)
    )

    assert client.accounts.list_communities("acc_1")[0].community_id == "1700000000000000000"
    assert listed.called
    assert client.accounts.sync_communities("acc_1")[0].name == "Builders" and synced.called

    found = client.accounts.search_communities("acc_1", "makers")
    assert found[0].id == "17" and found[0].member_count == 9
    assert dict(searched.calls.last.request.url.params) == {"q": "makers"}

    community = client.accounts.add_community("acc_1", community_id="1700000000000000000")
    assert community.id == 5
    assert json.loads(added.calls.last.request.content) == {"communityId": "1700000000000000000"}

    client.accounts.remove_community("acc_1", 5)
    assert removed.called
