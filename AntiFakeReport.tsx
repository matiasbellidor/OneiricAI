"""Domain models. These mirror db/schema.sql and the frontend types."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

SleepStage = Literal["awake", "light", "deep", "rem"]


class BiometricSample(BaseModel):
    ts: datetime
    heart_rate: float
    sleep_stage: SleepStage


class NightStats(BaseModel):
    avg_hr: float
    min_hr: float
    max_hr: float
    rem_minutes: float
    awakenings: int
    efficiency: float  # 0..1, share of the night actually asleep
    coverage_hours: float


class SleepSession(BaseModel):
    id: str
    user_id: str
    night_date: str  # date of the morning you woke up (YYYY-MM-DD)
    start_ts: datetime
    end_ts: datetime
    source: str = "synthetic"  # synthetic | fitbit | healthkit
    epoch_minutes: int = 5
    samples: list[BiometricSample] = Field(default_factory=list)
    stats: Optional[NightStats] = None


class Scene(BaseModel):
    text: str
    valence: float  # -1 (distressing) .. 1 (pleasant)
    arousal: float  # 0 (calm) .. 1 (intense)


class Sentiments(BaseModel):
    """The four interpreted sentiment metrics shown in the UI."""

    nostalgia: float
    tenderness: float
    calm: float
    longing: float


class StructuredDream(BaseModel):
    scenes: list[Scene]
    entities: list[str] = Field(default_factory=list)
    overall_valence: float
    overall_arousal: float
    sentiments: Sentiments
    source: Literal["claude", "local_fallback"] = "local_fallback"


class Dream(BaseModel):
    id: str
    user_id: str
    session_id: Optional[str] = None
    raw_text: str
    reported_at: datetime
    structured: Optional[StructuredDream] = None


class AntiFakeCheck(BaseModel):
    key: str
    label: str
    points: float
    max_points: float
    passed: bool
    reason: str


class AntiFakeReport(BaseModel):
    score: float
    threshold: int
    passed: bool
    bio_arousal: float
    text_arousal: float
    checks: list[AntiFakeCheck]


class Generation(BaseModel):
    id: str
    dream_id: str
    status: Literal["verified", "rejected", "rendering", "done", "failed"]
    provider: Optional[str] = None
    video_url: Optional[str] = None
    report: Optional[AntiFakeReport] = None
    created_at: datetime


class Post(BaseModel):
    id: str
    user_id: str
    handle: str
    caption: str
    verified: bool = True
    sentiments: Sentiments
    scenes: list[Scene]
    video_url: Optional[str] = None
    created_at: datetime


# ---- Request bodies ----------------------------------------------------------


class SeedIn(BaseModel):
    night_date: Optional[str] = None  # defaults to today (this morning's night)
    seed: int = 42


class IngestIn(BaseModel):
    night_date: str
    start_ts: datetime
    end_ts: datetime
    source: str = "fitbit"
    samples: list[BiometricSample]


class DreamIn(BaseModel):
    text: str
    night_date: Optional[str] = None


class ReconstructIn(BaseModel):
    text: str
    night_date: Optional[str] = None
    auto_seed: bool = True  # in demo mode, create a synthetic night if none exists


class ReconstructOut(BaseModel):
    dream: Dream
    session: SleepSession
    report: AntiFakeReport
    generation: Generation
    post: Optional[Post] = None
