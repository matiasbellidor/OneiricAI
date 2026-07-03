"""Synthetic wearable source.

Generates a deterministic, physiologically plausible night:
~90-minute sleep cycles, REM growing toward the morning, a brief awakening
around 03:00, and heart rate varying by stage. Mirrored in
frontend/src/lib/demoEngine.ts for the zero-backend demo.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

from ...models import BiometricSample, SleepSession
from ..antifake import night_stats

EPOCH_MIN = 5

# (stage, minutes) — sums to 450 min: 23:40 -> 07:10
STAGE_PLAN: list[tuple[str, int]] = [
    ("awake", 10),
    ("light", 45), ("deep", 35), ("rem", 10),    # cycle 1
    ("light", 40), ("deep", 30), ("rem", 15),    # cycle 2
    ("light", 35), ("deep", 20), ("rem", 25),    # cycle 3
    ("awake", 5),                                 # brief awakening ~03:00
    ("light", 40), ("deep", 10), ("rem", 30),    # cycle 4
    ("light", 35), ("rem", 30),                   # cycle 5 (morning REM)
    ("light", 35),
]

HR_BY_STAGE = {"awake": (68, 4), "light": (55, 2), "deep": (50, 2), "rem": (60, 3)}
AWAKENING_SPIKE = 74.0


class SyntheticSource:
    name = "synthetic"

    def __init__(self, seed: int = 42):
        self.seed = seed

    def fetch_night(self, user_id: str, night_date: str) -> SleepSession:
        rng = random.Random(self.seed)
        wake_day = datetime.strptime(night_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        start = wake_day - timedelta(days=1) + timedelta(hours=23, minutes=40)

        samples: list[BiometricSample] = []
        t = start
        awakenings_seen = 0
        for stage, minutes in STAGE_PLAN:
            for _ in range(minutes // EPOCH_MIN):
                mean, jitter = HR_BY_STAGE[stage]
                hr = mean + rng.uniform(-jitter, jitter)
                if stage == "awake" and t > start + timedelta(hours=1):
                    hr = AWAKENING_SPIKE + rng.uniform(-1, 1)
                    awakenings_seen += 1
                samples.append(BiometricSample(
                    ts=t, heart_rate=round(hr, 1), sleep_stage=stage))
                t += timedelta(minutes=EPOCH_MIN)

        session = SleepSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            night_date=night_date,
            start_ts=start,
            end_ts=t,
            source=self.name,
            epoch_minutes=EPOCH_MIN,
            samples=samples,
        )
        session.stats = night_stats(session)
        return session
