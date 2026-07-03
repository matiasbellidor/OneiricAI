# OneiricAi — Dreams, verified by your own body

> **One-liner (EN):** OneiricAi turns the dream fragments you write on waking into short vertical videos — but only if your night's biometrics (heart rate + REM sleep) back the story. No biological match, no video.
>
> **One-liner (ES):** OneiricAi convierte los fragmentos que escribís al despertar en videos verticales — pero solo si los biomarcadores de tu noche (frecuencia cardíaca + REM) respaldan la historia. Sin coincidencia biológica, no hay video.

**30-second pitch (ES):** Olvidamos el 90% de lo que soñamos a los pocos minutos de despertar. Las redes actuales premian inventar: cuanto más extremo el contenido, más viral. OneiricAi hace lo contrario. Escribís los fragmentos de tu sueño al despertar, tu wearable ya registró la noche, y un motor explicable —el **Anti-Fake Engine**— cruza relato contra biología: intensidad narrativa vs reactividad cardíaca en REM, tono emocional vs marcadores de estrés, ventana de recuerdo. Si tu cuerpo no vivió esa historia, el video no se genera. El resultado es un feed donde cada sueño lleva un sello: *verificado por biomarcadores*. La red social sana.

**30-second pitch (EN):** We forget ~90% of our dreams within minutes of waking. Today's feeds reward fabrication — the wilder the story, the more viral. OneiricAi inverts that. You write your dream fragments on waking, your wearable already logged the night, and an explainable **Anti-Fake Engine** cross-checks narrative against biology: story intensity vs cardiac reactivity during REM, emotional tone vs stress markers, recall freshness. If your body didn't live that story, the video is never rendered. The result: a feed where every dream carries a badge — *verified by biomarkers*. The healthy social network.

---

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

## Anti-Fake Engine (explainable, no black box)

| # | Check | Weight | What it verifies |
|---|-------|--------|------------------|
| 1 | `session_exists` | 25 | Real sleep data exists for that night (≥4 h full credit) |
| 2 | `rem_present` | 15 | REM sleep occurred — dream recall correlates with REM |
| 3 | `arousal_match` | **30** | Narrative intensity vs cardiac reactivity in REM (`|Δ| ≤ 0.2` full, `≥ 0.6` zero) |
| 4 | `valence_match` | 15 | Distressing stories need stress markers (HR spikes, awakenings); calm stories must lack them |
| 5 | `freshness` | 15 | Reported within the recall window (≤12 h full credit) |

Score ≥ **60/100** → video is generated and posted with a *verified* badge.
Below threshold → generation is refused, and the user sees **why**, check by check, with the actual numbers. Every rule is defensible in front of a jury or an investor.

The engine is implemented twice with identical constants: [`backend/app/services/antifake.py`](backend/app/services/antifake.py) (production) and [`frontend/src/lib/demoEngine.ts`](frontend/src/lib/demoEngine.ts) (zero-config demo).

## Demo mode vs full mode

| | Demo (default) | Full |
|---|---|---|
| Config needed | **None** | Supabase + optional keys |
| Biometrics | Deterministic synthetic night (seed 42) | Fitbit OAuth / `POST /api/biometrics/ingest` (n8n) |
| Dream analysis | Local Spanish lexicon | Claude API structured extraction |
| Video | Live canvas animation (frontend) / ffmpeg MP4 (backend) | Replicate text-to-video |
| Storage | In-memory | Supabase Postgres + Storage |

The frontend alone is a complete, deployable product demo.

## Project structure

```
oneiricai/
├── frontend/               React 18 + Vite + TS + Tailwind → Vercel
│   └── src/
│       ├── lib/demoEngine.ts    TS mirror of the Python engine
│       ├── lib/api.ts           demo/API switch (VITE_API_URL)
│       └── components/          Fragments, Night, Video, AntiFake, Feed
├── backend/                FastAPI (Python 3.11+) → Railway / Render
│   └── app/
│       ├── services/antifake.py     the engine (source of truth)
│       ├── services/lexicon.py      offline dream analysis
│       ├── services/claude_client.py Claude structured extraction
│       ├── services/wearables/      synthetic + Fitbit skeleton
│       ├── services/video/          mock (ffmpeg) + Replicate
│       └── routers/                 /biometrics /dreams /reconstruct /feed
└── db/schema.sql           Supabase Postgres + RLS + storage bucket
```

## Quickstart

### A — Instant demo (zero config)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Paste a dream (or use the example chips) and hit **Reconstruir sueño**.

### B — Deploy the demo to Vercel (2 minutes)

1. Push this repo to GitHub (commands below).
2. In Vercel: **Add New → Project → import `oneiricai`**.
3. **Root Directory: `frontend`** · Framework preset: Vite · no env vars.
4. Deploy. You now have a public URL people can actually use.

### C — Full stack

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # everything is optional
uvicorn app.main:app --reload # http://localhost:8000/docs

# Frontend against the API
cd ../frontend
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
```

For persistence: create a Supabase project, run [`db/schema.sql`](db/schema.sql) in the SQL Editor, and set `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` in `backend/.env`.

## Environment variables (all optional)

| Variable | Where | Effect when set |
|---|---|---|
| `VITE_API_URL` | frontend | Talk to the real API instead of demo engine |
| `ANTHROPIC_API_KEY` | backend | Claude structured extraction replaces the lexicon |
| `ANTHROPIC_MODEL` | backend | Defaults to `claude-sonnet-4-6` |
| `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | backend | Postgres persistence replaces in-memory store |
| `VIDEO_PROVIDER` | backend | `mock` (default) or `replicate` |
| `REPLICATE_API_TOKEN`, `REPLICATE_MODEL` | backend | Real text-to-video generation |
| `ANTIFAKE_THRESHOLD` | backend | Pass threshold, default `60` |
| `CORS_ORIGINS` | backend | Comma-separated origins, default `*` |

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Mode, provider, threshold |
| POST | `/api/biometrics/seed` | Generate a synthetic night |
| POST | `/api/biometrics/ingest` | Push real wearable samples (n8n target) |
| GET | `/api/biometrics/night` | Night session + stats |
| POST | `/api/dreams` | Store a dream text |
| POST | `/api/reconstruct` | Full pipeline: extract → verify → render → post |
| GET | `/api/feed` | Verified posts only |

## Wearables roadmap & health-data consent

1. **Fitbit Web API** (skeleton included): pure REST + OAuth2, `sleep` + `heartrate` scopes — fastest path to real data.
2. **Apple HealthKit**: requires a native iOS companion app (no REST API); planned second.
3. **Android Health Connect**: Google Fit's successor; planned alongside HealthKit.
4. **n8n**: nightly cron pulls the wearable and POSTs to `/api/biometrics/ingest`; a morning workflow reminds the user to write their dream inside the recall window.

Biometric data is health data. The design commitments: **explicit opt-in** per source, **data minimization** (only HR + sleep stages, 5-min epochs), **revocable** at any time with deletion, **row-level security** in Postgres (see `db/schema.sql` — biometrics are private, only posts are public), encrypted at rest by Supabase, and **never used to train models**.

## Tests

```bash
cd backend && python -m pytest app/tests -q
```

Four tests pin the engine's behavior, including the two canonical cases: a calm, real dream **passes** (score ≥ 80) and an invented viral dream **is rejected** (arousal/valence mismatch).

## Deploy notes

- **Frontend → Vercel**: root `frontend`, preset Vite, no env vars for demo.
- **Backend → Railway or Render**: root `backend`, `Procfile` included (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`). Set env vars as needed, then point Vercel's `VITE_API_URL` at it.

---

Built by **Matías Bellido** ([@matiasbellidor](https://github.com/matiasbellidor)) — Buenos Aires. Born as a 4-hour hackathon pitch; engineered to demo in zero config and scale with keys.
