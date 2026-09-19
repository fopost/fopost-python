from __future__ import annotations

import httpx
import respx

from fopost import Fopost
from tests.conftest import BASE_URL

ARTICLE = {
    "id": "99",
    "blog_id": "11",
    "title": "Spring drop",
    "body_html": "<p>Hello</p>",
    "excerpt": "A short summary",
    "status": "published",
    "author_name": "Store Owner",
    "tags": ["news"],
    "image_url": None,
    "url": "https://demo.myshopify.com/blogs/article/spring-drop",
    "published_at": "2026-09-01T10:00:00Z",
    "updated_at": None,
}


@respx.mock
def test_list_blogs_parses_every_blog(client: Fopost) -> None:
    respx.get(f"{BASE_URL}/accounts/a1/blogs").mock(
        return_value=httpx.Response(
            200,
            json={"data": [{"id": "11", "title": "News", "handle": "news", "url": None}]},
        )
    )

    blogs = client.blogs.list_blogs("a1")

    assert [b.id for b in blogs] == ["11"]
    assert blogs[0].title == "News"


@respx.mock
def test_list_articles_passes_the_filters(client: Fopost) -> None:
    route = respx.get(f"{BASE_URL}/accounts/a1/blogs/11/articles").mock(
        return_value=httpx.Response(200, json={"data": [ARTICLE]})
    )

    articles = client.blogs.list_articles("a1", "11", limit=5, status="draft", q="spring")

    assert dict(route.calls.last.request.url.params) == {
        "limit": "5",
        "status": "draft",
        "q": "spring",
    }
    assert articles[0].id == "99"
    assert articles[0].tags == ["news"]


@respx.mock
def test_update_article_changes_it_in_place(client: Fopost) -> None:
    # The article id is in the path, which is what stops an edit from creating
    # a second post on the site.
    route = respx.patch(f"{BASE_URL}/accounts/a1/blogs/11/articles/99").mock(
        return_value=httpx.Response(200, json={"data": ARTICLE})
    )

    client.blogs.update_article("a1", "11", "99", title="Spring drop, restocked")

    assert route.calls.last.request.url.path.endswith("/accounts/a1/blogs/11/articles/99")
    assert route.calls.last.request.method == "PATCH"
    # Only what the caller set travels, so nothing else on the article is blanked.
    body = route.calls.last.request.content
    assert b"Spring drop, restocked" in body
    # Nothing else is sent, so the rest of the article stays as it is.
    assert b"body" not in body and b"status" not in body


@respx.mock
def test_create_article_sends_the_optional_fields_it_was_given(client: Fopost) -> None:
    route = respx.post(f"{BASE_URL}/accounts/a1/blogs/11/articles").mock(
        return_value=httpx.Response(200, json={"data": ARTICLE})
    )

    client.blogs.create_article(
        "a1", "11", title="Spring drop", body="Hello", status="draft", tags=["news"]
    )

    content = route.calls.last.request.content
    assert b'"title":"Spring drop"' in content or b'"title": "Spring drop"' in content
    assert b"news" in content
    # Never sent, so the site keeps its own defaults.
    assert b"author_name" not in content
    assert b"image_url" not in content


@respx.mock
def test_delete_article_hits_the_article_route(client: Fopost) -> None:
    route = respx.delete(f"{BASE_URL}/accounts/a1/blogs/11/articles/99").mock(
        return_value=httpx.Response(204)
    )

    client.blogs.delete_article("a1", "11", "99")

    assert route.called


@respx.mock
def test_update_product_sends_only_what_changed(client: Fopost) -> None:
    route = respx.patch(f"{BASE_URL}/accounts/a1/products/7").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "id": "7",
                    "title": "Mug XL",
                    "handle": "mug",
                    "status": "draft",
                    "description": None,
                    "vendor": None,
                    "product_type": "Drinkware",
                    "tags": [],
                    "image_url": None,
                    "url": None,
                    "price": "12.00",
                    "currency": "USD",
                    "updated_at": None,
                }
            },
        )
    )

    product = client.blogs.update_product("a1", "7", title="Mug XL", product_type="Drinkware")

    content = route.calls.last.request.content
    assert b"Mug XL" in content
    assert b"Drinkware" in content
    assert b"vendor" not in content
    assert product.price == "12.00"
