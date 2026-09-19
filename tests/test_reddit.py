from __future__ import annotations

import httpx
import pytest
import respx

from fopost import Fopost, FopostError

from .conftest import BASE_URL


@respx.mock
def test_subreddits_rules_and_flairs(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/reddit/subreddits").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "name": "webdev",
                        "title": "Web Development",
                        "subscribers": 2_000_000,
                        "over18": False,
                        "canPost": True,
                        "flairEnabled": True,
                        "iconUrl": None,
                        "isDefault": True,
                    }
                ]
            },
        )
    )
    respx.get(f"{BASE_URL}/accounts/acc_1/reddit/subreddits/webdev/rules").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "subreddit": "webdev",
                    "rules": [
                        {
                            "name": "No self promotion",
                            "description": "Keep it useful",
                            "appliesTo": "link",
                        }
                    ],
                }
            },
        )
    )
    flairs = respx.get(f"{BASE_URL}/accounts/acc_1/reddit/flairs").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "subreddit": "webdev",
                    "flairs": [{"id": "flair-1", "text": "Showoff Saturday", "editable": False}],
                }
            },
        )
    )

    subreddits = client.accounts.list_reddit_subreddits("acc_1")
    assert subreddits[0].name == "webdev"
    assert subreddits[0].is_default is True
    assert subreddits[0].flair_enabled is True

    rules = client.accounts.list_reddit_subreddit_rules("acc_1", "webdev")
    assert rules.rules[0].applies_to == "link"

    result = client.accounts.list_reddit_flairs("acc_1", "webdev")
    assert result.flairs[0].id == "flair-1"
    assert flairs.calls.last.request.url.params["subreddit"] == "webdev"


@respx.mock
def test_default_subreddit_accepts_none(client: Fopost) -> None:
    route = respx.put(f"{BASE_URL}/accounts/acc_1/reddit/default-subreddit").mock(
        return_value=httpx.Response(200, json={"data": {"subreddit": None}})
    )

    assert client.accounts.set_reddit_default_subreddit("acc_1", None).subreddit is None
    assert route.calls.last.request.content == b'{"subreddit":null}'


@respx.mock
def test_validate_subreddit(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/validate/subreddit").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "subreddit": "webdev",
                    "exists": True,
                    "can_post": True,
                    "over_18": False,
                    "flair_enabled": True,
                    "ok": True,
                }
            },
        )
    )

    check = client.validate.subreddit(account_id="acc_1", name="webdev")
    assert check.ok is True
    assert route.calls.last.request.url.params["account_id"] == "acc_1"


@respx.mock
def test_vote_sends_the_direction(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/inbox/item_1/vote").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "id": "item_1",
                    "platform": "reddit",
                    "type": "comment",
                    "state": "unread",
                    "vote": "down",
                    "canVote": True,
                }
            },
        )
    )

    item = client.inbox.vote("item_1", "down")
    assert item.vote == "down"
    assert item.can_vote is True
    assert route.calls.last.request.content == b'{"direction":"down"}'


@respx.mock
def test_a_stale_grant_is_a_409(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/reddit/subreddits").mock(
        return_value=httpx.Response(
            409, json={"error": "reconnect_required", "message": "Reconnect this account"}
        )
    )

    with pytest.raises(FopostError) as err:
        client.accounts.list_reddit_subreddits("acc_1")
    assert err.value.status == 409
