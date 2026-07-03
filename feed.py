"""Video provider factory: adapter pattern so the demo never depends on a paid API."""

from pathlib import Path

from ...config import settings

MEDIA_DIR = Path(__file__).resolve().parents[3] / "media"
MEDIA_DIR.mkdir(exist_ok=True)


def get_provider():
    if settings.video_provider == "replicate":
        from .replicate_provider import ReplicateProvider
        return ReplicateProvider()
    from .mock import MockProvider
    return MockProvider(MEDIA_DIR)
