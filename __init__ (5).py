"""Video provider interface.

Providers turn a structured dream into a vertical 9:16 video and return a URL
(relative to the API host) — or None when rendering is unavailable, in which
case the frontend falls back to its live canvas reconstruction.
"""

from typing import Optional, Protocol

from ...models import StructuredDream


class VideoProvider(Protocol):
    name: str

    def generate(self, generation_id: str, structured: StructuredDream) -> Optional[str]:
        ...
