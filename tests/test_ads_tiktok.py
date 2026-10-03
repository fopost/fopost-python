from __future__ import annotations

import json

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL
from tests.test_ads import AD_FIXTURE

BUDGET = {"minor": 2000, "type": "daily"}
TARGETING = {"countries": ["US"], "ageMin": 18, "ageMax": 44, "gender": "all"}


@respx.mock
def test_identities_and_spark_posts_read_the_right_paths(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/ads/tiktok/business-centers").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "bc1", "name": "Brand HQ"}]})
    )
    respx.get(f"{BASE_URL}/ads/tiktok/identities").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "idt_1", "type": "CUSTOMIZED_USER", "name": "Your Brand"}]},
        )
    )
    spark = respx.get(f"{BASE_URL}/ads/spark-posts").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "item_99", "identityId": "idt_1", "views": 48213}]}
        )
    )

    centers = client.ads.tiktok_business_centers(workspace_id="ws_1", connection_id="conn_1")
    assert centers[0].name == "Brand HQ"

    identities = client.ads.tiktok_identities(
        workspace_id="ws_1", connection_id="conn_1", ad_account_id="7011"
    )
    assert identities[0].type == "CUSTOMIZED_USER"

    posts = client.ads.spark_posts(
        workspace_id="ws_1", connection_id="conn_1", ad_account_id="7011", identity_id="idt_1"
    )
    assert posts[0].views == 48213
    assert spark.calls.last.request.url.params["identity_id"] == "idt_1"


@respx.mock
def test_spark_post_id_and_smart_plus_travel_in_the_body(client: Fopost) -> None:
    ad_route = respx.post(f"{BASE_URL}/ads").mock(
        return_value=httpx.Response(201, json={"data": AD_FIXTURE})
    )
    campaign_route = respx.post(f"{BASE_URL}/ads/campaigns").mock(
        return_value=httpx.Response(
            201,
            json={"data": {"id": "c1", "name": "Smart", "status": "PAUSED"}},
        )
    )

    client.ads.create(
        workspace_id="ws_1",
        connection_id="conn_1",
        ad_account_id="7011",
        page_id="idt_1",
        name="Spark",
        goal="traffic",
        budget=BUDGET,
        targeting=TARGETING,
        text="",
        spark_post_id="item_99",
    )
    assert json.loads(ad_route.calls.last.request.content)["sparkPostId"] == "item_99"

    client.ads.create_campaign(
        workspace_id="ws_1",
        connection_id="conn_1",
        ad_account_id="7011",
        name="Smart",
        goal="traffic",
        smart_plus=True,
    )
    assert json.loads(campaign_route.calls.last.request.content)["smartPlus"] is True


@respx.mock
def test_conversions_hash_nothing_locally_and_report_what_was_accepted(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/ads/conversions").mock(
        return_value=httpx.Response(202, json={"data": {"accepted": 1}})
    )

    result = client.ads.upload_conversions(
        workspace_id="ws_1",
        connection_id="conn_1",
        ad_account_id="7011",
        pixel_id="px_1",
        events=[{"eventName": "CompletePayment", "occurredAt": "2026-09-18T10:04:00Z"}],
    )

    assert result["accepted"] == 1
    body = json.loads(route.calls.last.request.content)
    assert body["pixelId"] == "px_1"
    assert body["events"][0]["eventName"] == "CompletePayment"


@respx.mock
def test_comments_page_and_the_three_writes(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/ads/comments").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "comments": [{"id": "cm_1", "text": "nice", "hidden": True, "likes": 3}],
                    "nextCursor": "2",
                }
            },
        )
    )
    reply = respx.post(f"{BASE_URL}/ads/comments/cm_1/reply").mock(
        return_value=httpx.Response(201, json={"data": {"replyId": "cm_2"}})
    )
    hide = respx.post(f"{BASE_URL}/ads/comments/cm_1/hide").mock(
        return_value=httpx.Response(200, json={"message": "Comment hidden"})
    )
    delete = respx.delete(f"{BASE_URL}/ads/comments/cm_1").mock(
        return_value=httpx.Response(200, json={"message": "Comment deleted"})
    )

    page = client.ads.comments(workspace_id="ws_1", connection_id="conn_1", ad_id="ad_1")
    assert page.next_cursor == "2"
    assert page.comments[0].hidden is True

    scope = {"workspace_id": "ws_1", "connection_id": "conn_1", "ad_id": "ad_1"}
    assert client.ads.reply_to_comment("cm_1", text="Friday!", **scope)["replyId"] == "cm_2"
    assert json.loads(reply.calls.last.request.content)["adId"] == "ad_1"

    client.ads.set_comment_hidden("cm_1", hidden=True, **scope)
    assert json.loads(hide.calls.last.request.content)["hidden"] is True

    client.ads.delete_comment("cm_1", **scope)
    # The ad travels in the body, because the path already carries the comment.
    assert json.loads(delete.calls.last.request.content)["adId"] == "ad_1"
