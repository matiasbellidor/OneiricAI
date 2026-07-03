"""Explainable local dream analysis (no API key required).

A deliberately simple Spanish lexicon estimates arousal, valence and the four
sentiment metrics from the dream fragments. When ANTHROPIC_API_KEY is set,
claude_client.py replaces this with structured extraction — but the fallback
keeps the whole pipeline (and the demo) working offline.

The constants below are mirrored in frontend/src/lib/demoEngine.ts.
"""

from __future__ import annotations

import re

from ..models import Scene, Sentiments, StructuredDream

HIGH_AROUSAL = [
    "corr", "persegu", "persec", "escap", "hu\u00ed", "grit", "explot", "explos",
    "fuego", "llama", "tsunami", "tormenta", "ca\u00ed", "cae", "salt", "monstruo",
    "disparo", "sangre", "terremoto", "choque", "veloc", "p\u00e1nico", "panico",
    "miedo", "ahog", "helic\u00f3ptero", "helicoptero",
]

CALM = [
    "calma", "lento", "c\u00e1lid", "calid", "flot", "suave", "silencio", "paz",
    "brisa", "tarde", "luz", "olor", "aroma", "mar", "patio", "abuel",
    "infancia", "sonre", "descans", "despacio",
]

NEGATIVE = [
    "miedo", "p\u00e1nico", "panico", "oscur", "monstruo", "sangre", "grit",
    "llor", "muert", "perd", "ahog", "angusti", "atrapa", "encerr",
]

POSITIVE = [
    "abuel", "c\u00e1lid", "calid", "sonre", "abraz", "perro", "amig", "luz",
    "pan", "hogar", "feliz", "paz", "amor", "jug", "dorada", "esperaba",
]

NOSTALGIA = ["abuel", "infancia", "cuando era chic", "barrio", "recuerdo",
             "escuela", "viej", "a\u00f1os", "casa de"]
TENDERNESS = ["abraz", "perro", "gato", "abuel", "mam", "beb", "suave",
              "cari", "mano", "cola"]
LONGING = ["extra\u00f1", "volver", "lejos", "ganas de", "qued", "despedi",
           "otra vez", "irme"]

_SENT_SPLIT = re.compile(r"[.!?\u2026]+\s+")
_ENTITY = re.compile(r"\b[A-Z\u00c1\u00c9\u00cd\u00d3\u00da\u00d1][a-z\u00e1\u00e9\u00ed\u00f3\u00fa\u00f1]{2,}\b")


def _hits(text: str, words: list[str]) -> int:
    """Presence-based count: each lexicon entry scores at most once."""
    return sum(1 for w in words if w in text)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _arousal_valence(text_lower: str) -> tuple[float, float]:
    high = _hits(text_lower, HIGH_AROUSAL)
    calm = _hits(text_lower, CALM)
    pos = _hits(text_lower, POSITIVE)
    neg = _hits(text_lower, NEGATIVE)
    arousal = _clamp(0.15 + 0.13 * high - 0.06 * calm, 0.0, 1.0)
    valence = _clamp(0.12 * pos - 0.14 * neg, -1.0, 1.0)
    return arousal, valence


def _entities(raw_text: str) -> list[str]:
    """Capitalized words that are not sentence-initial (Lanús, Simón, ...)."""
    found: list[str] = []
    for sentence in _SENT_SPLIT.split(raw_text):
        tokens = sentence.split()
        for tok in tokens[1:]:
            m = _ENTITY.fullmatch(tok.strip(",;:\u2014()\u00bf\u00a1"))
            if m and m.group(0) not in found:
                found.append(m.group(0))
    return found[:6]


def analyze(raw_text: str) -> StructuredDream:
    text = raw_text.lower()
    overall_arousal, overall_valence = _arousal_valence(text)

    sentences = [s.strip() for s in _SENT_SPLIT.split(raw_text) if len(s.strip()) > 15]
    if not sentences:
        sentences = [raw_text.strip()]
    scenes: list[Scene] = []
    for s in sentences[:5]:
        a, v = _arousal_valence(s.lower())
        scenes.append(Scene(
            text=s,
            arousal=round(_clamp(0.6 * a + 0.4 * overall_arousal, 0, 1), 2),
            valence=round(_clamp(0.6 * v + 0.4 * overall_valence, -1, 1), 2),
        ))

    nost = _hits(text, NOSTALGIA)
    tend = _hits(text, TENDERNESS)
    long_ = _hits(text, LONGING)
    calm_hits = _hits(text, CALM)
    sentiments = Sentiments(
        nostalgia=round(_clamp(0.08 + 0.18 * nost, 0, 0.96), 2),
        tenderness=round(_clamp(0.08 + 0.2 * tend, 0, 0.96), 2),
        calm=round(_clamp(0.85 - 0.75 * overall_arousal + 0.02 * calm_hits, 0.02, 0.96), 2),
        longing=round(_clamp(0.08 + 0.2 * long_, 0, 0.96), 2),
    )

    return StructuredDream(
        scenes=scenes,
        entities=_entities(raw_text),
        overall_valence=round(overall_valence, 2),
        overall_arousal=round(overall_arousal, 2),
        sentiments=sentiments,
        source="local_fallback",
    )
