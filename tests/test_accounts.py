from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx
import pytest
import respx

from fopost import Fopost, FopostError
from tests.conftest import ACCOUNT_FIXTURE, BASE_URL


@respx.mock
def test_list_parses_camel_case_and_sends_the_camel_query_param(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts").mock(
        return_value=httpx.Response(200, json={"data": [ACCOUNT_FIXTURE]})
    )

    accounts = client.accounts.list(workspace_id="ws_1")

    assert len(accounts) == 1
    assert accounts[0].id == "acc_1"
    assert accounts[0].workspace_id == "ws_1"
    assert accounts[0].is_primary is True
    assert accounts[0].health_status == "healthy"
    assert accounts[0].last_health_check == datetime(2026, 8, 12, 9, 0, tzinfo=timezone.utc)

    # The accounts endpoint reads workspaceId, unlike posts and labels.
    assert dict(route.calls.last.request.url.params) == {"workspaceId": "ws_1"}


@respx.mock
def test_list_without_a_workspace_sends_no_params(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts").mock(
        return_value=httpx.Response(200, json={"data": []})
    )

    assert client.accounts.list() == []
    assert dict(route.calls.last.request.url.params) == {}


@respx.mock
def test_get_returns_one_account(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1").mock(
        return_value=httpx.Response(200, json={"data": ACCOUNT_FIXTURE})
    )

    account = client.accounts.get("acc_1")

    assert account.platform == "twitter"
    assert account.username == "fopost"


@respx.mock
def test_health_returns_the_raw_payload(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/health").mock(
        return_value=httpx.Response(200, json={"data": {"status": "healthy", "checks": []}})
    )

    assert client.accounts.health("acc_1") == {"status": "healthy", "checks": []}


@respx.mock
def test_list_filters_by_group(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts").mock(
        return_value=httpx.Response(
            200, json={"data": [{**ACCOUNT_FIXTURE, "platformName": "FoPost HQ"}]}
        )
    )

    accounts = client.accounts.list(group_id="grp_1")

    assert accounts[0].platform_name == "FoPost HQ"
    assert dict(route.calls.last.request.url.params) == {"group_id": "grp_1"}


@respx.mock
def test_update_sends_the_display_name_and_null_resets_it(client: Fopost) -> None:
    route = respx.patch(f"{BASE_URL}/accounts/acc_1").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": "acc_1", "name": "Brand", "platform_name": "FoPost"}}
        )
    )

    renamed = client.accounts.update("acc_1", display_name="Brand")
    assert renamed.name == "Brand"
    assert renamed.platform_name == "FoPost"
    assert json.loads(route.calls.last.request.content) == {"display_name": "Brand"}

    client.accounts.update("acc_1", display_name=None)
    assert json.loads(route.calls.last.request.content) == {"display_name": None}


@respx.mock
def test_move_posts_the_target_workspace(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/accounts/acc_1/move").mock(
        return_value=httpx.Response(200, json={"data": {"id": "acc_1", "workspace_id": "ws_2"}})
    )

    moved = client.accounts.move("acc_1", workspace_id="ws_2")

    assert moved.workspace_id == "ws_2"
    assert json.loads(route.calls.last.request.content) == {"workspace_id": "ws_2"}


@respx.mock
def test_move_conflict_keeps_the_blocking_tables_on_the_error(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/accounts/acc_1/move").mock(
        return_value=httpx.Response(
            409,
            json={
                "error": "move_blocked",
                "message": "Account has history",
                "blocking_tables": ["posts"],
            },
        )
    )

    with pytest.raises(FopostError) as caught:
        client.accounts.move("acc_1", workspace_id="ws_2")

    assert caught.value.status == 409
    assert caught.value.code == "move_blocked"
    assert caught.value.body["blocking_tables"] == ["posts"]


@respx.mock
def test_create_telegram_connect_code(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/accounts/telegram/connect-code").mock(
        return_value=httpx.Response(
            201,
            json={
                "data": {
                    "code": "abc123",
                    "command": "/connect abc123",
                    "bot_username": "fopost_bot",
                    "deep_link": "https://t.me/fopost_bot?start=abc123",
                    "group_link": None,
                    "expires_at": "2026-09-19T12:15:00Z",
                }
            },
        )
    )

    minted = client.accounts.create_telegram_connect_code(workspace_id="ws_1")

    assert minted.command == "/connect abc123"
    assert minted.group_link is None
    assert json.loads(route.calls.last.request.content) == {"workspaceId": "ws_1"}

    client.accounts.create_telegram_connect_code()
    assert json.loads(route.calls.last.request.content) == {}


@respx.mock
def test_get_telegram_connect_status(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts/telegram/connect-code/status").mock(
        return_value=httpx.Response(
            200, json={"data": {"status": "failed", "account_id": None, "reason": "slot_taken"}}
        )
    )

    status = client.accounts.get_telegram_connect_status("abc123")

    assert status.status == "failed"
    assert status.reason == "slot_taken"
    assert dict(route.calls.last.request.url.params) == {"code": "abc123"}


@respx.mock
def test_telegram_bot_commands_routes(client: Fopost) -> None:
    path = f"{BASE_URL}/accounts/acc_1/telegram/commands"
    commands = [{"command": "start", "description": "Start the bot"}]
    respx.get(path).mock(return_value=httpx.Response(200, json={"data": {"commands": commands}}))
    put = respx.put(path).mock(
        return_value=httpx.Response(200, json={"data": {"commands": commands}})
    )
    respx.delete(path).mock(return_value=httpx.Response(200, json={"data": {"commands": []}}))

    assert client.accounts.get_telegram_bot_commands("acc_1").commands[0].command == "start"

    result = client.accounts.set_telegram_bot_commands("acc_1", commands)
    assert result.commands[0].description == "Start the bot"
    assert json.loads(put.calls.last.request.content) == {"commands": commands}

    assert client.accounts.delete_telegram_bot_commands("acc_1").commands == []


@respx.mock
def test_slack_channels_and_members(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/slack/channels").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "C1",
                        "name": "general",
                        "is_private": False,
                        "is_member": True,
                        "is_current": True,
                    }
                ]
            },
        )
    )
    respx.get(f"{BASE_URL}/accounts/acc_1/slack/members").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "U1",
                        "name": "sam",
                        "real_name": "Sam Rivera",
                        "display_name": None,
                        "avatar": None,
                        "is_bot": False,
                    }
                ]
            },
        )
    )

    channels = client.accounts.list_slack_channels("acc_1")
    assert channels[0].id == "C1"
    assert channels[0].is_current is True

    members = client.accounts.list_slack_members("acc_1")
    assert members[0].id == "U1"
    assert members[0].display_name is None


@respx.mock
def test_slack_identity_get_and_partial_update(client: Fopost) -> None:
    path = f"{BASE_URL}/accounts/acc_1/slack/identity"
    identity = {"username": "Launch Bot", "icon_url": None, "icon_emoji": ":rocket:"}
    respx.get(path).mock(return_value=httpx.Response(200, json={"data": identity}))
    patch = respx.patch(path).mock(return_value=httpx.Response(200, json={"data": identity}))

    assert client.accounts.get_slack_identity("acc_1").icon_emoji == ":rocket:"

    result = client.accounts.update_slack_identity("acc_1", username="Launch Bot", icon_url=None)
    assert result.username == "Launch Bot"
    # Omitted fields stay off the wire; None is sent to clear.
    assert json.loads(patch.calls.last.request.content) == {
        "username": "Launch Bot",
        "icon_url": None,
    }


@respx.mock
def test_slack_webhook_connection_raises_with_its_code(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/slack/channels").mock(
        return_value=httpx.Response(
            409, json={"error": "webhook_connection", "message": "Reconnect with the Slack app"}
        )
    )

    with pytest.raises(FopostError) as exc:
        client.accounts.list_slack_channels("acc_1")
    assert exc.value.status == 409
    assert exc.value.code == "webhook_connection"


@respx.mock
def test_discord_channels_and_identity(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/discord/channels").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "id": "c2",
                        "name": "launches",
                        "type": 0,
                        "parent_id": None,
                        "nsfw": False,
                        "can_post": True,
                        "is_current": True,
                    }
                ]
            },
        )
    )
    switch = respx.patch(f"{BASE_URL}/accounts/acc_1/discord/channels/current").mock(
        return_value=httpx.Response(
            200, json={"data": {"id": "c2", "name": "launches", "is_current": True}}
        )
    )
    identity = respx.patch(f"{BASE_URL}/accounts/acc_1/discord/identity").mock(
        return_value=httpx.Response(
            200, json={"data": {"username": "Release Bot", "avatar_url": None}}
        )
    )

    channels = client.accounts.list_discord_channels("acc_1")
    assert channels[0].id == "c2"
    assert channels[0].is_current is True

    client.accounts.switch_discord_channel("acc_1", "c2")
    assert json.loads(switch.calls.last.request.content) == {"channel_id": "c2"}

    # Omitted fields never reach the wire, so Discord keeps them.
    assert client.accounts.update_discord_identity("acc_1", username="Release Bot").username == (
        "Release Bot"
    )
    assert json.loads(identity.calls.last.request.content) == {"username": "Release Bot"}


@respx.mock
def test_discord_event_round_trip(client: Fopost) -> None:
    created = {
        "id": "e1",
        "name": "Launch stream",
        "description": None,
        "channel_id": None,
        "location": "https://example.com/live",
        "start_time": "2026-10-01T18:00:00.000Z",
        "end_time": "2026-10-01T19:00:00.000Z",
        "status": "scheduled",
        "user_count": 0,
    }
    create = respx.post(f"{BASE_URL}/accounts/acc_1/discord/events").mock(
        return_value=httpx.Response(201, json={"data": created})
    )
    respx.get(f"{BASE_URL}/accounts/acc_1/discord/events").mock(
        return_value=httpx.Response(200, json={"data": [created]})
    )
    patch = respx.patch(f"{BASE_URL}/accounts/acc_1/discord/events/e1").mock(
        return_value=httpx.Response(200, json={"data": {**created, "status": "canceled"}})
    )
    respx.delete(f"{BASE_URL}/accounts/acc_1/discord/events/e1").mock(
        return_value=httpx.Response(200, json={"data": {"deleted": True}})
    )

    event = client.accounts.create_discord_event(
        "acc_1",
        name="Launch stream",
        start_time="2026-10-01T18:00:00.000Z",
        end_time="2026-10-01T19:00:00.000Z",
        location="https://example.com/live",
    )
    assert event.id == "e1"
    assert json.loads(create.calls.last.request.content) == {
        "name": "Launch stream",
        "start_time": "2026-10-01T18:00:00.000Z",
        "end_time": "2026-10-01T19:00:00.000Z",
        "location": "https://example.com/live",
    }

    assert [e.id for e in client.accounts.list_discord_events("acc_1")] == ["e1"]

    assert client.accounts.update_discord_event("acc_1", "e1", status="canceled").status == (
        "canceled"
    )
    assert json.loads(patch.calls.last.request.content) == {"status": "canceled"}

    assert client.accounts.delete_discord_event("acc_1", "e1") is True


@respx.mock
def test_discord_members_roles_and_dm(client: Fopost) -> None:
    members = respx.get(f"{BASE_URL}/accounts/acc_1/discord/members").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "u7", "username": "ada", "is_bot": False, "roles": ["r1"]}]},
        )
    )
    respx.post(f"{BASE_URL}/accounts/acc_1/discord/roles").mock(
        return_value=httpx.Response(201, json={"data": {"id": "r2", "name": "Beta"}})
    )
    respx.put(f"{BASE_URL}/accounts/acc_1/discord/roles/r2/members/u7").mock(
        return_value=httpx.Response(200, json={"data": {"assigned": True}})
    )
    dm = respx.post(f"{BASE_URL}/accounts/acc_1/discord/dm").mock(
        return_value=httpx.Response(201, json={"data": {"id": "m1", "channel_id": "dm1"}})
    )

    found = client.accounts.list_discord_members("acc_1", query="ada")
    assert found[0].id == "u7"
    assert members.calls.last.request.url.params["q"] == "ada"

    assert client.accounts.create_discord_role("acc_1", name="Beta").id == "r2"
    assert client.accounts.add_discord_member_role("acc_1", "r2", "u7") is True

    assert client.accounts.send_discord_dm("acc_1", "u7", "hi").channel_id == "dm1"
    assert json.loads(dm.calls.last.request.content) == {"member_id": "u7", "content": "hi"}


@respx.mock
def test_discord_webhook_connection_raises(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/discord/channels").mock(
        return_value=httpx.Response(
            409, json={"error": "webhook_connection", "message": "Upgrade it to the bot first"}
        )
    )
    with pytest.raises(FopostError) as excinfo:
        client.accounts.list_discord_channels("acc_1")
    assert excinfo.value.status == 409
    assert excinfo.value.code == "webhook_connection"


@respx.mock
def test_pinterest_board_create_sends_only_what_was_given(client: Fopost) -> None:
    board = {"id": "b1", "name": "Recipes", "privacy": "PUBLIC", "description": None}
    route = respx.post(f"{BASE_URL}/accounts/acc_1/pinterest/boards").mock(
        return_value=httpx.Response(201, json={"data": board})
    )

    created = client.accounts.create_pinterest_board("acc_1", name="Recipes")
    assert created.id == "b1"
    assert json.loads(route.calls.last.request.content) == {"name": "Recipes"}


@respx.mock
def test_youtube_playlists_and_transcript(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/youtube/playlists").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "PL1", "title": "Tutorials", "is_default": True}]}
        )
    )
    respx.get(f"{BASE_URL}/accounts/acc_1/youtube/captions/cap1").mock(
        return_value=httpx.Response(
            200, json={"data": {"caption_id": "cap1", "transcript": "1\nHello\n"}}
        )
    )

    playlists = client.accounts.list_youtube_playlists("acc_1")
    assert playlists[0].is_default is True
    assert client.accounts.read_youtube_transcript("acc_1", "cap1").transcript.endswith("\n")


@respx.mock
def test_bluesky_languages_round_trip(client: Fopost) -> None:
    path = f"{BASE_URL}/accounts/acc_1/bluesky/languages"
    route = respx.put(path).mock(
        return_value=httpx.Response(200, json={"data": {"languages": ["en", "pt-BR"]}})
    )

    result = client.accounts.set_bluesky_languages("acc_1", ["en", "pt-BR"])
    assert result.languages == ["en", "pt-BR"]
    assert json.loads(route.calls.last.request.content) == {"languages": ["en", "pt-BR"]}


@respx.mock
def test_instagram_and_linkedin_reads(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/instagram/publishing-limit").mock(
        return_value=httpx.Response(
            200, json={"data": {"quota_usage": 12, "quota_total": 50, "remaining": 38}}
        )
    )
    respx.get(f"{BASE_URL}/accounts/acc_1/linkedin/mentions").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": [
                    {
                        "urn": "urn:li:organization:2414183",
                        "name": "Devtestco",
                        "annotation": "@[Devtestco](urn:li:organization:2414183)",
                    }
                ]
            },
        )
    )

    assert client.accounts.get_instagram_publishing_limit("acc_1").remaining == 38
    mentions = client.accounts.search_linkedin_mentions("acc_1", "devtestco")
    assert mentions[0].annotation.endswith("(urn:li:organization:2414183)")


@respx.mock
def test_tiktok_creator_info_reports_the_accounts_own_switches(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/acc_1/tiktok/creator-info").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "privacy_level_options": ["PUBLIC_TO_EVERYONE"],
                    "duet_disabled": True,
                    "max_video_post_duration_sec": 600,
                }
            },
        )
    )

    info = client.accounts.get_tiktok_creator_info("acc_1")
    assert info.duet_disabled is True
    assert info.stitch_disabled is False
    assert info.max_video_post_duration_sec == 600


@respx.mock
def test_tiktok_music_and_place_search_pass_the_query_through(client: Fopost) -> None:
    music = respx.get(f"{BASE_URL}/accounts/acc_1/tiktok/music").mock(
        return_value=httpx.Response(
            200, json={"data": [{"id": "m1", "title": "Sunrise", "author": "Kite"}]}
        )
    )
    respx.get(f"{BASE_URL}/accounts/acc_1/tiktok/locations").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "p1", "name": "Blue Bottle"}]})
    )

    tracks = client.accounts.search_tiktok_music("acc_1", q="sunrise", limit=5)
    assert tracks[0].id == "m1"
    assert music.calls.last.request.url.params["q"] == "sunrise"
    assert music.calls.last.request.url.params["limit"] == "5"

    places = client.accounts.search_tiktok_locations("acc_1", q="cafe")
    assert places[0].name == "Blue Bottle"


@respx.mock
def test_tiktok_video_lookup_returns_the_address_a_repurpose_run_reads(client: Fopost) -> None:
    respx.post(f"{BASE_URL}/accounts/acc_1/tiktok/video-download").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "video_id": "7300000000000000000",
                    "download_url": "https://www.tiktok.com/@a/video/7300000000000000000",
                }
            },
        )
    )

    video = client.accounts.lookup_tiktok_video(
        "acc_1", "https://www.tiktok.com/@a/video/7300000000000000000"
    )
    assert video.video_id == "7300000000000000000"
    assert video.download_url is not None
