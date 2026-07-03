"""Storage layer.

MemoryStore  — default (demo mode): zero-config, resets on restart.
SupabaseStore — full mode: activates automatically when SUPABASE_URL and
SUPABASE_SERVICE_KEY are set. Tables live in db/schema.sql.
Both expose the same interface, so routers never care which one is active.
"""

from __future__ import annotations

import logging
from typing import Optional

from .config import settings
from .models import Dream, Generation, Post, SleepSession

log = logging.getLogger("oneiric.db")


class MemoryStore:
    name = "memory"

    def __init__(self) -> None:
        self._sessions: dict[tuple[str, str], SleepSession] = {}
        self._dreams: dict[str, Dream] = {}
        self._generations: dict[str, Generation] = {}
        self._posts: list[Post] = []

    # sessions
    def save_session(self, session: SleepSession) -> None:
        self._sessions[(session.user_id, session.night_date)] = session

    def get_session(self, user_id: str, night_date: str) -> Optional[SleepSession]:
        return self._sessions.get((user_id, night_date))

    def latest_session(self, user_id: str) -> Optional[SleepSession]:
        mine = [s for (u, _), s in self._sessions.items() if u == user_id]
        return max(mine, key=lambda s: s.night_date) if mine else None

    # dreams / generations / posts
    def save_dream(self, dream: Dream) -> None:
        self._dreams[dream.id] = dream

    def get_dream(self, dream_id: str) -> Optional[Dream]:
        return self._dreams.get(dream_id)

    def save_generation(self, gen: Generation) -> None:
        self._generations[gen.id] = gen

    def add_post(self, post: Post) -> None:
        self._posts.insert(0, post)

    def list_posts(self, limit: int = 30) -> list[Post]:
        return self._posts[:limit]


class SupabaseStore:
    """Thin Supabase adapter over the same interface (full mode).

    Uses the service key server-side; RLS still protects direct client access.
    """

    name = "supabase"

    def __init__(self) -> None:
        from supabase import create_client  # guarded: only needed in full mode

        self.client = create_client(settings.supabase_url, settings.supabase_service_key)

    def save_session(self, session: SleepSession) -> None:
        row = session.model_dump(mode="json", exclude={"samples", "stats"})
        self.client.table("sleep_sessions").upsert(row).execute()
        samples = [
            {"session_id": session.id, "user_id": session.user_id,
             "ts": s.ts.isoformat(), "heart_rate": s.heart_rate, "sleep_stage": s.sleep_stage}
            for s in session.samples
        ]
        if samples:
            self.client.table("biometric_samples").insert(samples).execute()

    def get_session(self, user_id: str, night_date: str) -> Optional[SleepSession]:
        res = (self.client.table("sleep_sessions").select("*")
               .eq("user_id", user_id).eq("night_date", night_date)
               .limit(1).execute())
        if not res.data:
            return None
        session = SleepSession.model_validate({**res.data[0], "samples": []})
        rows = (self.client.table("biometric_samples").select("ts,heart_rate,sleep_stage")
                .eq("session_id", session.id).order("ts").execute())
        session.samples = [  # type: ignore[assignment]
            {"ts": r["ts"], "heart_rate": r["heart_rate"], "sleep_stage": r["sleep_stage"]}
            for r in rows.data
        ]
        return SleepSession.model_validate(session.model_dump())

    def latest_session(self, user_id: str) -> Optional[SleepSession]:
        res = (self.client.table("sleep_sessions").select("night_date")
               .eq("user_id", user_id).order("night_date", desc=True).limit(1).execute())
        return self.get_session(user_id, res.data[0]["night_date"]) if res.data else None

    def save_dream(self, dream: Dream) -> None:
        self.client.table("dreams").upsert(dream.model_dump(mode="json")).execute()

    def get_dream(self, dream_id: str) -> Optional[Dream]:
        res = self.client.table("dreams").select("*").eq("id", dream_id).limit(1).execute()
        return Dream.model_validate(res.data[0]) if res.data else None

    def save_generation(self, gen: Generation) -> None:
        self.client.table("generations").upsert(gen.model_dump(mode="json")).execute()

    def add_post(self, post: Post) -> None:
        self.client.table("posts").insert(post.model_dump(mode="json")).execute()

    def list_posts(self, limit: int = 30) -> list[Post]:
        res = (self.client.table("posts").select("*")
               .order("created_at", desc=True).limit(limit).execute())
        return [Post.model_validate(r) for r in res.data]


_store: MemoryStore | SupabaseStore | None = None


def get_store():
    global _store
    if _store is None:
        if settings.demo_mode:
            _store = MemoryStore()
        else:
            try:
                _store = SupabaseStore()
            except Exception as exc:  # noqa: BLE001
                log.warning("Supabase unavailable (%s); using in-memory store.", exc)
                _store = MemoryStore()
        log.info("Store: %s", _store.name)
    return _store
