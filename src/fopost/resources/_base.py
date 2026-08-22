from __future__ import annotations

from typing import Any, TypeVar

from .._http import HttpClient
from ..models import FopostModel

T = TypeVar("T", bound=FopostModel)


class Resource:
    def __init__(self, http: HttpClient) -> None:
        self._http = http


def parse_list(model: type[T], data: Any) -> list[T]:
    if not isinstance(data, list):
        return []
    return [model.model_validate(item) for item in data]


def drop_unset(body: dict[str, Any]) -> dict[str, Any]:
    """Strip keys the caller never passed so PUT stays a partial update."""
    return {k: v for k, v in body.items() if v is not UNSET}


class _Unset:
    _instance: _Unset | None = None

    def __new__(cls) -> _Unset:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNSET"

    def __bool__(self) -> bool:
        return False


UNSET = _Unset()
