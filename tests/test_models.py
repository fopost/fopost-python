from __future__ import annotations

from typing import get_args

from fopost import PLATFORMS, Platform, Post, SocialAccount


def test_the_platform_literal_and_tuple_agree() -> None:
    assert tuple(get_args(Platform)) == PLATFORMS
    assert len(PLATFORMS) == 31
    assert len(set(PLATFORMS)) == 31


def test_the_list_covers_the_platforms_the_api_returns() -> None:
    for name in ("twitter", "wordpress", "bluesky", "hashnode", "mastodon", "skool"):
        assert name in PLATFORMS


def test_an_unknown_platform_still_parses() -> None:
    # Model fields are plain str, so a platform added server-side must not
    # break an older SDK.
    account = SocialAccount.model_validate(
        {"id": "acc_1", "platform": "a-platform-shipped-after-this-release"}
    )
    assert account.platform == "a-platform-shipped-after-this-release"


def test_unknown_response_keys_are_kept() -> None:
    post = Post.model_validate({"id": "p1", "status": "draft", "brand_new_field": 42})
    assert post.model_extra is not None
    assert post.model_extra["brand_new_field"] == 42
