"""Anti-Fake Engine — Biological Authenticity.

An explainable, rule-based score (0-100) that decides whether a dream
narrative is plausibly backed by the biometrics of that same night.
No black box: every check returns points AND a human-readable reason,
so the report can be defended in front of a jury or an investor.

Checks and weights (total 100, default threshold 60):
  1. session_exists   25  there is real sleep data for that night
  2. rem_present      15  REM sleep occurred (dream recall correlates with REM)
  3. arousal_match    30  narrative intensity vs cardiac reactivity in REM
  4. valence_match    15  emotional tone vs stress markers (spikes, awakenings)
  5. freshness        15  reported close to wake-up (recall window is short)
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from ..models import AntiFakeCheck, AntiFakeReport, NightStats, SleepSession, StructuredDream

PASS_THRESHOLD_DEFAULT = 60


@dataclass
class NightFeatures:
    baseline_hr: float      # median HR in light+deep sleep
    rem_hr_mean: float
    rem_hr_max: float
    rem_minutes: float
    awakenings: int         # awake epochs after sleep onset
    coverage_hours: float
    bio_arousal: float      # 0..1 normalized cardiac reactivity during REM


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_features(session: SleepSession) -> NightFeatures:
    epoch = session.epoch_minutes
    hr_nonrem = [s.heart_rate for s in session.samples if s.sleep_stage in ("light", "deep")]
    hr_rem = [s.heart_rate for s in session.samples if s.sleep_stage == "rem"]
    baseline = statistics.median(hr_nonrem) if hr_nonrem else 60.0
    rem_mean = statistics.fmean(hr_rem) if hr_rem else baseline
    rem_max = max(hr_rem) if hr_rem else baseline

    # awakenings after sleep onset (skip leading awake epochs)
    onset = next((i for i, s in enumerate(session.samples) if s.sleep_stage != "awake"), 0)
    awakenings = sum(1 for s in session.samples[onset:] if s.sleep_stage == "awake")

    delta = rem_mean - baseline
    bio_arousal = _clamp(delta / 18.0, 0.0, 1.0) + 0.08 * max(0, awakenings - 1)

    return NightFeatures(
        baseline_hr=round(baseline, 1),
        rem_hr_mean=round(rem_mean, 1),
        rem_hr_max=round(rem_max, 1),
        rem_minutes=len(hr_rem) * epoch,
        awakenings=awakenings,
        coverage_hours=round(len(session.samples) * epoch / 60.0, 1),
        bio_arousal=round(_clamp(bio_arousal, 0.0, 1.0), 2),
    )


def night_stats(session: SleepSession) -> NightStats:
    hrs = [s.heart_rate for s in session.samples]
    f = compute_features(session)
    asleep = sum(1 for s in session.samples if s.sleep_stage != "awake")
    total = max(1, len(session.samples))
    return NightStats(
        avg_hr=round(statistics.fmean(hrs), 1) if hrs else 0,
        min_hr=min(hrs) if hrs else 0,
        max_hr=max(hrs) if hrs else 0,
        rem_minutes=f.rem_minutes,
        awakenings=f.awakenings,
        efficiency=round(asleep / total, 2),
        coverage_hours=f.coverage_hours,
    )


def evaluate(
    structured: StructuredDream,
    session: Optional[SleepSession],
    reported_at: Optional[datetime] = None,
    threshold: int = PASS_THRESHOLD_DEFAULT,
) -> AntiFakeReport:
    reported_at = reported_at or datetime.now(timezone.utc)
    checks: list[AntiFakeCheck] = []

    # 1. Sleep data exists ------------------------------------------------------
    if session is None or not session.samples:
        checks.append(AntiFakeCheck(
            key="session_exists", label="Datos de sue\u00f1o", points=0, max_points=25,
            passed=False,
            reason="No hay registro biom\u00e9trico para esa noche. Sin datos, no hay verificaci\u00f3n posible.",
        ))
        for key, label, mx in [("rem_present", "Fase REM", 15),
                               ("arousal_match", "Intensidad vs coraz\u00f3n", 30),
                               ("valence_match", "Tono emocional vs estr\u00e9s", 15),
                               ("freshness", "Ventana de recuerdo", 15)]:
            checks.append(AntiFakeCheck(key=key, label=label, points=0, max_points=mx,
                                        passed=False, reason="Sin datos de la noche."))
        return AntiFakeReport(score=0, threshold=threshold, passed=False,
                              bio_arousal=0, text_arousal=structured.overall_arousal,
                              checks=checks)

    f = compute_features(session)

    if f.coverage_hours >= 4:
        pts, ok = 25.0, True
        reason = f"Noche registrada v\u00eda {session.source}: {f.coverage_hours} h de datos continuos."
    else:
        pts, ok = 12.0, True
        reason = f"Registro parcial ({f.coverage_hours} h). Verificaci\u00f3n con menor confianza."
    checks.append(AntiFakeCheck(key="session_exists", label="Datos de sue\u00f1o",
                                points=pts, max_points=25, passed=ok, reason=reason))

    # 2. REM present ------------------------------------------------------------
    if f.rem_minutes >= 15:
        pts, ok = 15.0, True
        reason = f"{f.rem_minutes:.0f} min de sue\u00f1o REM detectados: hubo actividad on\u00edrica real."
    elif f.rem_minutes >= 5:
        pts, ok = 8.0, True
        reason = f"Solo {f.rem_minutes:.0f} min de REM: recuerdo posible pero d\u00e9bil."
    else:
        pts, ok = 0.0, False
        reason = "Sin fase REM registrada: es muy improbable recordar un sue\u00f1o de esa noche."
    checks.append(AntiFakeCheck(key="rem_present", label="Fase REM",
                                points=pts, max_points=15, passed=ok, reason=reason))

    # 3. Arousal match (the core of the engine) ---------------------------------
    text_a = _clamp(structured.overall_arousal, 0, 1)
    diff = abs(text_a - f.bio_arousal)
    if diff <= 0.2:
        pts = 30.0
    elif diff >= 0.6:
        pts = 0.0
    else:
        pts = round(30.0 * (0.6 - diff) / 0.4, 1)
    ok = pts >= 15
    reason = (
        f"Reactividad card\u00edaca en REM {f.bio_arousal:.2f} "
        f"(FC {f.rem_hr_mean:.0f} lpm vs base {f.baseline_hr:.0f}) frente a intensidad "
        f"del relato {text_a:.2f}. "
        + ("Coherente: tu cuerpo vivi\u00f3 lo que contaste." if ok
           else "Incoherente: el relato no coincide con lo que registr\u00f3 tu coraz\u00f3n esa noche.")
    )
    checks.append(AntiFakeCheck(key="arousal_match", label="Intensidad vs coraz\u00f3n",
                                points=pts, max_points=30, passed=ok, reason=reason))

    # 4. Valence consistency ----------------------------------------------------
    v = structured.overall_valence
    stress_markers = f.rem_hr_max >= f.baseline_hr + 15 or f.awakenings >= 2
    if v <= -0.25:  # distressing narrative -> expect stress markers
        if stress_markers:
            pts, ok = 15.0, True
            reason = (f"Relato angustiante y marcadores de estr\u00e9s presentes "
                      f"(pico {f.rem_hr_max:.0f} lpm, {f.awakenings} despertares): coherente.")
        else:
            pts, ok = 0.0, False
            reason = (f"Relato angustiante pero sin marcadores de estr\u00e9s: pico de solo "
                      f"{f.rem_hr_max:.0f} lpm y {f.awakenings} despertar(es). Tu cuerpo no lo vivi\u00f3.")
    elif v >= 0.25:  # pleasant/calm narrative -> expect no extreme stress
        if f.rem_hr_max < f.baseline_hr + 25 and f.awakenings <= 2:
            pts, ok = 15.0, True
            reason = "Relato calmo y noche sin picos de estr\u00e9s: coherente."
        else:
            pts, ok = 0.0, False
            reason = (f"Relato calmo pero la noche muestra estr\u00e9s real "
                      f"(pico {f.rem_hr_max:.0f} lpm, {f.awakenings} despertares).")
    else:
        pts, ok = 10.0, True
        reason = "Tono emocional neutro: sin se\u00f1ales contradictorias."
    checks.append(AntiFakeCheck(key="valence_match", label="Tono emocional vs estr\u00e9s",
                                points=pts, max_points=15, passed=ok, reason=reason))

    # 5. Freshness --------------------------------------------------------------
    end = session.end_ts if session.end_ts.tzinfo else session.end_ts.replace(tzinfo=timezone.utc)
    rep = reported_at if reported_at.tzinfo else reported_at.replace(tzinfo=timezone.utc)
    hours = max(0.0, (rep - end).total_seconds() / 3600.0)
    if hours <= 12:
        pts, ok = 15.0, True
        reason = f"Registrado {hours:.1f} h despu\u00e9s de despertar: dentro de la ventana de recuerdo."
    elif hours <= 24:
        pts, ok = 8.0, True
        reason = f"Registrado {hours:.1f} h despu\u00e9s: el recuerdo ya se degrad\u00f3 parcialmente."
    else:
        pts, ok = 3.0, False
        reason = f"Registrado {hours:.0f} h despu\u00e9s de la noche declarada: recuerdo poco confiable."
    checks.append(AntiFakeCheck(key="freshness", label="Ventana de recuerdo",
                                points=pts, max_points=15, passed=ok, reason=reason))

    score = round(sum(c.points for c in checks), 1)
    return AntiFakeReport(
        score=score,
        threshold=threshold,
        passed=score >= threshold,
        bio_arousal=f.bio_arousal,
        text_arousal=round(text_a, 2),
        checks=checks,
    )
