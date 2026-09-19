"""``client.media`` — direct uploads through a presigned URL."""

from __future__ import annotations

from .._http import unwrap
from ..errors import error_from_response
from ..models import MediaItem, PresignedUpload
from ._base import Resource

__all__ = ["MediaResource"]


class MediaResource(Resource):
    def presign(
        self, *, workspace_id: str, filename: str, mime_type: str, size: int
    ) -> PresignedUpload:
        """Reserve an upload slot for a file of ``size`` bytes."""
        body = {
            "workspaceId": workspace_id,
            "filename": filename,
            "mimeType": mime_type,
            "size": size,
        }
        return PresignedUpload.model_validate(unwrap(self._http.post("/media/presign", body)))

    def complete(self, upload_id: str) -> MediaItem:
        """Register the uploaded bytes as a library item."""
        return MediaItem.model_validate(
            unwrap(self._http.post(f"/media/presign/{upload_id}/complete"))
        )

    def upload_direct(
        self, *, workspace_id: str, filename: str, mime_type: str, data: bytes
    ) -> MediaItem:
        """Presign, PUT the bytes to storage, then complete. Returns the library item."""
        slot = self.presign(
            workspace_id=workspace_id, filename=filename, mime_type=mime_type, size=len(data)
        )
        # Storage takes the raw bytes with the presigned headers only, never the API key.
        headers = {**slot.headers, "Content-Length": str(len(data))}
        response = self._http._client.request(
            slot.method, slot.upload_url, content=data, headers=headers
        )
        if not response.is_success:
            raise error_from_response(response.status_code, response.text)
        return self.complete(slot.upload_id)
