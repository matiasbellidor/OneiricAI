"""The full pipeline in one call: fragments -> Claude -> Anti-Fake gate -> video -> post.

POST /api/reconstruct is what the frontend uses. If the Anti-Fake score is
below the threshold, no video is generated and no post is created — the
explainable report says exactly why. That rejection is the product.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from fastapi import APIRouter, HTTPException

from ..config import settings
from ..db import get_store
from ..models import Dream, Generation, Post, ReconstructIn, ReconstructOut
from ..services import antifake, claude_client
from ..services.video import get_provider
from ..services.wearables.synthetic import SyntheticSource

router = APIRouter(tags=["generate"])


@router.post("/reconstruct", response_model=ReconstructOut)
async def reconstruct(body: ReconstructIn) -> ReconstructOut:
    if len(body.text.strip()) < 12:
        raise HTTPException(422, "Contanos un poco m\u00e1s: el relato es demasiado corto para analizar.")

    store = get_store()
    night = body.night_date or date.today().isoformat()

    session = store.get_session(settings.demo_user_id, night)
    if session is None:
        if body.auto_seed and settings.demo_mode:
            session = SyntheticSource().fetch_night(settings.demo_user_id, night)
            store.save_session(session)
        else:
            raise HTTPException(
                404,
                "No hay datos biom\u00e9tricos para esa noche. Sincroniz\u00e1 tu wearable "
                "o gener\u00e1 una noche de prueba con /api/biometrics/seed.",
            )

    now = datetime.now(timezone.utc)
    structured = await claude_client.extract(body.text)
    dream = Dream(
        id=str(uuid.uuid4()),
        user_id=settings.demo_user_id,
        session_id=session.id,
        raw_text=body.text.strip(),
        reported_at=now,
        structured=structured,
    )
    store.save_dream(dream)

    report = antifake.evaluate(structured, session, reported_at=now,
                               threshold=settings.antifake_threshold)

    gen = Generation(
        id=str(uuid.uuid4()),
        dream_id=dream.id,
        status="verified" if report.passed else "rejected",
        report=report,
        created_at=now,
    )

    post: Post | None = None
    if report.passed:
        provider = get_provider()
        gen.provider = provider.name
        gen.video_url = provider.generate(gen.id, structured)
        gen.status = "done" if gen.video_url else "verified"
        post = Post(
            id=str(uuid.uuid4()),
            user_id=settings.demo_user_id,
            handle=settings.demo_handle,
            caption=dream.raw_text[:140],
            verified=True,
            sentiments=structured.sentiments,
            scenes=structured.scenes,
            video_url=gen.video_url,
            created_at=now,
        )
        store.add_post(post)

    store.save_generation(gen)
    return ReconstructOut(dream=dream, session=session, report=report,
                          generation=gen, post=post)
