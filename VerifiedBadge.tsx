"""Biometric endpoints: seed a synthetic night, ingest real wearable data,
and read a night back (chart data for the frontend)."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..db import get_store
from ..models import IngestIn, SeedIn, SleepSession
from ..services.antifake import night_stats
from ..services.wearables.synthetic import SyntheticSource

router = APIRouter(tags=["biometrics"])


@router.post("/biometrics/seed", response_model=SleepSession)
def seed_night(body: SeedIn) -> SleepSession:
    """Generate and store a synthetic night (demo / development)."""
    night = body.night_date or date.today().isoformat()
    session = SyntheticSource(seed=body.seed).fetch_night(settings.demo_user_id, night)
    get_store().save_session(session)
    return session


@router.post("/biometrics/ingest", response_model=SleepSession)
def ingest(body: IngestIn) -> SleepSession:
    """Ingest a night from a real source (n8n cron -> Fitbit sync posts here)."""
    session = SleepSession(
        id=str(uuid.uuid4()),
        user_id=settings.demo_user_id,
        night_date=body.night_date,
        start_ts=body.start_ts,
        end_ts=body.end_ts,
        source=body.source,
        samples=body.samples,
    )
    session.stats = night_stats(session)
    get_store().save_session(session)
    return session


@router.get("/biometrics/night", response_model=SleepSession)
def get_night(night_date: str | None = None) -> SleepSession:
    store = get_store()
    session = (store.get_session(settings.demo_user_id, night_date)
               if night_date else store.latest_session(settings.demo_user_id))
    if session is None:
        raise HTTPException(404, "No hay datos de sue\u00f1o para esa noche. Us\u00e1 /api/biometrics/seed.")
    return session
