"""MockProvider — free, deterministic dream rendering.

Renders one gradient frame per scene (palette driven by valence/arousal, scene
text overlaid) and stitches them into a vertical MP4 with ffmpeg (3 s/scene).
If Pillow or ffmpeg are missing it returns None and the frontend shows its
animated canvas reconstruction instead — the demo never breaks.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
import textwrap
from pathlib import Path
from typing import Optional

from ...models import Scene, StructuredDream

log = logging.getLogger("oneiric.video")

W, H = 720, 1280
SECONDS_PER_SCENE = 3


def _palette(scene: Scene) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if scene.valence >= 0.25 and scene.arousal < 0.5:
        return (20, 20, 40), (138, 121, 214)      # warm violet dusk
    if scene.valence >= 0.25:
        return (26, 15, 46), (214, 121, 150)      # vivid pleasant
    if scene.valence <= -0.25:
        return (28, 11, 11), (214, 92, 58)        # distress embers
    return (15, 20, 32), (121, 184, 214)          # neutral deep blue


class MockProvider:
    name = "mock"

    def __init__(self, media_dir: Path):
        self.media_dir = media_dir

    def generate(self, generation_id: str, structured: StructuredDream) -> Optional[str]:
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            log.info("Pillow not installed; skipping MP4 render.")
            return None
        if not shutil.which("ffmpeg"):
            log.info("ffmpeg not found; skipping MP4 render.")
            return None

        try:
            with tempfile.TemporaryDirectory() as tmp:
                tmpdir = Path(tmp)
                for i, scene in enumerate(structured.scenes[:5]):
                    top, bottom = _palette(scene)
                    img = Image.new("RGB", (W, H))
                    for y in range(H):
                        t = y / H
                        img.paste(tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3)),
                                  (0, y, W, y + 1))
                    draw = ImageDraw.Draw(img)
                    wrapped = textwrap.fill(scene.text, width=30)
                    draw.multiline_text((60, H - 320), wrapped, fill=(237, 232, 218), spacing=10)
                    draw.text((60, 80), f"ONEIRIC \u00b7 escena {i + 1}", fill=(180, 172, 190))
                    img.save(tmpdir / f"frame_{i:02d}.png")

                out = self.media_dir / f"{generation_id}.mp4"
                cmd = [
                    "ffmpeg", "-y",
                    "-framerate", f"1/{SECONDS_PER_SCENE}",
                    "-i", str(tmpdir / "frame_%02d.png"),
                    "-vf", "fps=24,format=yuv420p",
                    str(out),
                ]
                subprocess.run(cmd, check=True, capture_output=True)
                return f"/media/{out.name}"
        except Exception as exc:  # noqa: BLE001 — rendering is best-effort by design
            log.warning("Mock render failed (%s); frontend canvas will take over.", exc)
            return None
