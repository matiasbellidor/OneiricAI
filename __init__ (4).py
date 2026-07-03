"""Dream structuring via the Anthropic API, with a local fallback.

If ANTHROPIC_API_KEY is set, Claude extracts scenes, entities, valence/arousal
and the four sentiment metrics as strict JSON. On any failure — or with no key
at all — the explainable local lexicon takes over, so the pipeline never breaks.
"""

from __future__ import annotations

import json
import logging
import re

import httpx

from ..config import settings
from ..models import StructuredDream
from . import lexicon

log = logging.getLogger("oneiric.claude")

API_URL = "https://api.anthropic.com/v1/messages"

SYSTEM_PROMPT = """Sos el analizador de sueños de OneiricAi. Recibís el relato \
crudo de un sueño en español rioplatense y devolvés SOLO un objeto JSON válido, \
sin markdown, sin backticks, sin texto adicional, con esta forma exacta:

{
  "scenes": [{"text": "...", "valence": -1..1, "arousal": 0..1}],
  "entities": ["..."],
  "overall_valence": -1..1,
  "overall_arousal": 0..1,
  "sentiments": {"nostalgia": 0..1, "tenderness": 0..1, "calm": 0..1, "longing": 0..1}
}

Reglas: entre 1 y 5 escenas en orden narrativo; "arousal" mide intensidad \
fisiológica (0 = calma total, 1 = pánico/acción extrema); "valence" mide tono \
emocional (-1 angustiante, 1 placentero); "entities" son personas, lugares u \
objetos con nombre propio. Números con 2 decimales."""


def _strip_fences(text: str) -> str:
    return re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()


async def extract(raw_text: str) -> StructuredDream:
    if settings.anthropic_api_key:
        try:
            return await _claude_extract(raw_text)
        except Exception as exc:  # noqa: BLE001 — any failure falls back, never breaks
            log.warning("Claude extraction failed (%s); using local fallback.", exc)
    return lexicon.analyze(raw_text)


async def _claude_extract(raw_text: str) -> StructuredDream:
    payload = {
        "model": settings.anthropic_model,
        "max_tokens": 1024,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": raw_text}],
    }
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(API_URL, json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    parsed = json.loads(_strip_fences(text))
    parsed["source"] = "claude"
    return StructuredDream.model_validate(parsed)
