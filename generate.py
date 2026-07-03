"""ReplicateProvider — optional real text-to-video generation (paid API).

Enable with VIDEO_PROVIDER=replicate plus REPLICATE_API_TOKEN and
REPLICATE_MODEL (an owner/model:version string for a vertical-capable
text-to-video model). Kept intentionally thin: create a prediction from the
dream's scene prompts, poll until it finishes, return the output URL.
"""

from __future__ import annotations

import logging
import time
from typing import Optional

import httpx

from ...config import settings
from ...models import StructuredDream

log = logging.getLogger("oneiric.video")

API = "https://api.replicate.com/v1/predictions"


class ReplicateProvider:
    name = "replicate"

    def generate(self, generation_id: str, structured: StructuredDream) -> Optional[str]:
        if not (settings.replicate_api_token and settings.replicate_model):
            log.info("Replicate not configured; skipping.")
            return None

        prompt = (
            "Dreamlike cinematic vertical video, soft grain, slow camera. "
            + " Then ".join(s.text for s in structured.scenes[:3])
        )
        headers = {"Authorization": f"Bearer {settings.replicate_api_token}"}
        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(API, headers=headers, json={
                    "version": settings.replicate_model,
                    "input": {"prompt": prompt, "aspect_ratio": "9:16"},
                })
                resp.raise_for_status()
                pred = resp.json()
                for _ in range(60):  # poll up to ~5 min
                    time.sleep(5)
                    status = client.get(pred["urls"]["get"], headers=headers).json()
                    if status["status"] == "succeeded":
                        out = status.get("output")
                        return out[0] if isinstance(out, list) else out
                    if status["status"] in ("failed", "canceled"):
                        break
        except Exception as exc:  # noqa: BLE001
            log.warning("Replicate generation failed: %s", exc)
        return None
