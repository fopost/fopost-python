"""``client.media`` — upload limits and direct uploads through a presigned URL."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._http import unwrap
from ..errors import error_from_response
from ..models import MediaItem, PresignedUpload, UploadLimits
from ._base import Resource

__all__ = ["MediaResource"]

#: What a multipart request may carry per file when ``GET /media/limits`` is unreachable.
DEFAULT_MULTIPART_MAX_FILE_BYTES = 100 * 1024 * 1024


class MediaResource(Resource):
    def limits(self, *, workspace_id: str | None = None) -> UploadLimits:
        """The upload ceilings for the caller's account."""
        return UploadLimits.model_validate(
            unwrap(self._http.get("/media/limits", {"workspaceId": workspace_id}))
        )

    def presign(
        self,
        *,
        workspace_id: str,
        filename: str,
        mime_type: str,
        size: int,
        folder_id: str | None = None,
        origin: str | None = None,
        brand_role: str | None = None,
        brand_voice_id: str | None = None,
        person_consent: Mapping[str, str] | None = None,
    ) -> PresignedUpload:
        """Reserve an upload slot for a file of ``size`` bytes."""
        body: dict[str, Any] = {
            "workspaceId": workspace_id,
            "filename": filename,
            "mimeType": mime_type,
            "size": size,
        }
        optional = {
            "folderId": folder_id,
            "origin": origin,
            "brandRole": brand_role,
            "brandVoiceId": brand_voice_id,
            "personConsent": dict(person_consent) if person_consent is not None else None,
        }
        body.update({k: v for k, v in optional.items() if v is not None})
        return PresignedUpload.model_validate(unwrap(self._http.post("/media/presign", body)))

    def complete(self, upload_id: str) -> MediaItem:
        """Register the uploaded bytes as a library item."""
        return MediaItem.model_validate(
            unwrap(self._http.post(f"/media/presign/{upload_id}/complete"))
        )

    def upload_direct(
        self,
        *,
        workspace_id: str,
        filename: str,
        mime_type: str,
        data: bytes,
        folder_id: str | None = None,
        origin: str | None = None,
        brand_role: str | None = None,
        brand_voice_id: str | None = None,
        person_consent: Mapping[str, str] | None = None,
    ) -> MediaItem:
        """Presign, PUT the bytes to storage, then complete. Returns the library item."""
        slot = self.presign(
            workspace_id=workspace_id,
            filename=filename,
            mime_type=mime_type,
            size=len(data),
            folder_id=folder_id,
            origin=origin,
            brand_role=brand_role,
            brand_voice_id=brand_voice_id,
            person_consent=person_consent,
        )
        # Storage takes the raw bytes with the presigned headers only, never the API key.
        headers = {**slot.headers, "Content-Length": str(len(data))}
        response = self._http._client.request(
            slot.method, slot.upload_url, content=data, headers=headers
        )
        if not response.is_success:
            raise error_from_response(response.status_code, response.text)
        return self.complete(slot.upload_id)
