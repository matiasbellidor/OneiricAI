# OneiricAi — Dreams, verified by your own body

> **One-liner (EN):** OneiricAi turns the dream fragments you write on waking into short vertical videos — but only if your night's biometrics (heart rate + REM sleep) back the story. No biological match, no video.
>
> **One-liner (ES):** OneiricAi convierte los fragmentos que escribís al despertar en videos verticales — pero solo si los biomarcadores de tu noche (frecuencia cardíaca + REM) respaldan la historia. Sin coincidencia biológica, no hay video.

## The problem

Two failures overlap. **Memory:** we forget ~90% of what we dream within minutes of waking — dreams are the most personal content we produce, and almost all of it evaporates. **Incentives:** today's social feeds reward fabrication; the more extreme the story, the more viral it gets, so any "dream sharing" platform without verification degenerates into creative-writing bait.

OneiricAi addresses both at once: it captures the dream inside the short recall window, and it refuses to render anything your body didn't actually live.

## The idea

**30-second pitch (ES):** Olvidamos el 90% de lo que soñamos a los pocos minutos de despertar. Las redes actuales premian inventar: cuanto más extremo el contenido, más viral. OneiricAi hace lo contrario. Escribís los fragmentos de tu sueño al despertar, tu wearable ya registró la noche, y un motor explicable —el **Anti-Fake Engine**— cruza relato contra biología: intensidad narrativa vs reactividad cardíaca en REM, tono emocional vs marcadores de estrés, ventana de recuerdo. Si tu cuerpo no vivió esa historia, el video no se genera. El resultado es un feed donde cada sueño lleva un sello: *verificado por biomarcadores*. La red social sana.

**30-second pitch (EN):** We forget ~90% of our dreams within minutes of waking. Today's feeds reward fabrication — the wilder the story, the more viral. OneiricAi inverts that. You write your dream fragments on waking, your wearable already logged the night, and an explainable **Anti-Fake Engine** cross-checks narrative against biology: story intensity vs cardiac reactivity during REM, emotional tone vs stress markers, recall freshness. If your body didn't live that story, the video is never rendered. The result: a feed where every dream carries a badge — *verified by biomarkers*. The healthy social network.

## How it works

```
 wearable (HR + sleep stages)          dream fragments (text, on waking)
            │                                        │
            ▼                                        ▼
   biometrics ingest  ────────────►  Claude structured extraction
   (Fitbit / synthetic)              (scenes, entities, valence, arousal,
            │                         4 sentiment metrics) — local lexicon
            │                         fallback when no API key
            ▼                                        │
            └────────────►  ANTI-FAKE ENGINE  ◄──────┘
                        explainable score /100, threshold 60
                           │                    │
                     REJECTED (with        VERIFIED → video provider
                     per-check reasons)    (mock ffmpeg / Replicate)
                                                │
                                                ▼
                                    feed of verified dreams only
```

The narrative side extracts scenes, named entities, emotional **valence** (−1 distressing … +1 pleasant), **arousal** (0 calm … 1 intense) and four sentiment metrics shown in the UI: *nostalgia, ternura, calma, añoranza*. The biological side reduces the night to features: median non-REM heart rate as baseline, mean/max HR during REM, REM minutes, awakenings after sleep onset, and hours of coverage.

## The Anti-Fake Engine

An explainable, rule-based score out of 100. Five checks; a dream passes at **≥ 60**.

| # | Check | Weight | What it verifies |
|---|-------|--------|------------------|
| 1 | `session_exists` | 25 | Real sleep data exists for that night (≥ 4 h full credit) |
| 2 | `rem_present` | 15 | REM sleep occurred — dream recall correlates strongly with REM |
| 3 | `arousal_match` | **30** | Narrative intensity vs cardiac reactivity in REM (`|Δ| ≤ 0.2` full credit, `≥ 0.6` zero, linear between) |
| 4 | `valence_match` | 15 | Distressing stories require stress markers (HR spikes, awakenings); calm stories must lack them |
| 5 | `freshness` | 15 | Reported within the recall window (≤ 12 h after waking for full credit) |

The core signal is **check 3**: cardiac reactivity during REM — how far REM heart rate rises above the non-REM baseline, plus a penalty for repeated awakenings — is normalized to 0..1 and compared directly against the narrative's arousal. A heart that stayed at baseline all night cannot back a story about fleeing a tsunami.

Every check returns points **and a human-readable reason with the actual numbers**, so a rejection is never a mystery. The report can be defended line by line in front of a jury or an investor — that is the point of using a transparent heuristic instead of a black-box classifier.

### Two canonical verdicts

These two texts are pinned by the automated test suite:

**Real, calm dream** — *"Estaba en la casa de mi abuela en Lanús. Olor a pan recién hecho… Mi perro Simón me esperaba en la puerta…"* → low narrative arousal matches a quiet night → **84.7/100, verified**, all five checks pass.

**Invented viral dream** — *"Me perseguía un tsunami gigante por la 9 de Julio. Corría entre autos en llamas… Sentí pánico total…"* → maximum narrative arousal against the same quiet night → **48/100, rejected**. `arousal_match` and `valence_match` fail with reasons like: *"Relato angustiante pero sin marcadores de estrés… Tu cuerpo no lo vivió."*

The engine is implemented **twice with identical constants**: [`backend/app/services/antifake.py`](backend/app/services/antifake.py) is the source of truth, and [`frontend/src/lib/demoEngine.ts`](frontend/src/lib/demoEngine.ts) mirrors it so the zero-config demo behaves exactly like the API. Tuning one side means tuning both.

## Design decisions

**Verification is a gate, not a label.** Most platforms moderate after publishing. Here, an unverified dream is never rendered at all — the feed's integrity is structural, not curated.

**Explainability over sophistication.** A weighted heuristic with published thresholds beats an opaque model for this use case: users deserve to know *why* their dream was rejected, and the scoring must survive adversarial questioning.

**Graceful degradation.** Every external dependency is optional and has a local fallback, so the full pipeline always runs:

| Capability | Production path | Fallback (zero config) |
|---|---|---|
| Dream analysis | Claude API structured extraction | Spanish lexicon, same output shape |
| Biometrics | Fitbit OAuth / wearable ingest | Deterministic synthetic night (seed 42) |
| Video | Replicate text-to-video | Live canvas animation / ffmpeg MP4 |
| Storage | Supabase Postgres + Storage | In-memory store |

**Wearable-only biometrics — no EEG.** Heart rate and sleep stages from consumer devices are enough for the arousal/valence checks and keep the entry barrier at "a watch you already own", not lab hardware.

**Privacy by architecture.** Biometrics and raw dreams are private rows; only verified posts are publicly readable. This split lives in the database policies, not in application goodwill.

## Architecture

```
oneiricai/
├── frontend/               React 18 + Vite + TypeScript + Tailwind
│   └── src/
│       ├── lib/demoEngine.ts    TS mirror of the Python engine
│       ├── lib/api.ts           API client with demo-mode switch
│       └── components/          Fragments, Night, Video, AntiFake, Feed
├── backend/                FastAPI (Python 3.11+)
│   └── app/
│       ├── services/antifake.py      the engine (source of truth)
│       ├── services/lexicon.py       offline dream analysis
│       ├── services/claude_client.py Claude structured extraction
│       ├── services/wearables/       synthetic source + Fitbit skeleton
│       ├── services/video/           mock (ffmpeg) + Replicate providers
│       └── routers/                  biometrics · dreams · reconstruct · feed
└── db/schema.sql           Postgres schema + row-level security
```

The UI is a single page that exposes the pipeline in order: **01 Fragmentos** (dream input) → **02 Tu noche** (hypnogram: REM bands, awakenings, HR curve against baseline) → **03 Reconstrucción** (9:16 video panel with the four sentiment metrics) → **Anti-Fake report** (score, per-check breakdown, and a body-vs-narrative arousal track) → **Feed** (verified dreams only).

## API surface

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/biometrics/seed` | Generate a synthetic night |
| POST | `/api/biometrics/ingest` | Receive real wearable samples (n8n target) |
| GET | `/api/biometrics/night` | Night session + stats |
| POST | `/api/dreams` | Store a dream text |
| POST | `/api/reconstruct` | Full pipeline: extract → verify → render → post |
| GET | `/api/feed` | Verified posts only |

`/api/reconstruct` is the one-shot endpoint that runs everything above and returns the dream, the session, the full Anti-Fake report, the generation status, and the post (only if verified).

## Data model

Six tables in [`db/schema.sql`](db/schema.sql): `profiles`, `sleep_sessions` (one row per night per source), `biometric_samples` (5-minute-epoch time series, indexed on `(user_id, ts)`), `dreams` (raw text + structured JSON), `generations` (verdict, score, full report, video URL), and `posts`. Row-level security enforces the privacy split: every table is own-data-only except `posts`, which is world-readable — the feed is the *only* public surface.

## Wearables roadmap & health-data ethics

1. **Fitbit Web API** (skeleton included): pure REST + OAuth2 with `sleep` and `heartrate` scopes — the fastest path to real data.
2. **Apple HealthKit**: requires a native iOS companion (no REST API); planned second.
3. **Android Health Connect**: Google Fit's successor; planned alongside HealthKit.
4. **n8n orchestration**: a nightly workflow pulls the wearable and posts to the ingest endpoint; a morning workflow reminds the user to write their dream while it is still inside the recall window.

Biometric data is health data. The commitments baked into the design: **explicit opt-in** per source, **data minimization** (only HR + sleep stage, 5-minute epochs — nothing else is collected), **revocable** access with deletion, **private by default** at the database-policy level, encrypted at rest, and **never used to train models**.

## Scope & honesty

This is an MVP born as a 4-hour hackathon pitch. What is real today: the full verification pipeline, the explainable engine with pinned tests, the synthetic wearable source, and a complete product UI. What is deliberately mocked: the default video output (canvas animation / ffmpeg gradient render) stands in for generative text-to-video, and the default night is synthetic until a wearable is connected. The production integrations — Claude extraction, Replicate rendering, Supabase persistence, Fitbit OAuth — are wired as optional providers on the same interfaces.

---

Built by **Matías Bellido** ([@matiasbellidor](https://github.com/matiasbellidor)) — Buenos Aires.
