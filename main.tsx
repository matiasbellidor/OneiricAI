-- ============================================================
-- OneiricAi — Supabase schema
-- Run in: Supabase Dashboard > SQL Editor > New query
-- Safe to re-run (idempotent-ish: uses IF NOT EXISTS where possible)
-- ============================================================

-- ---------- 1. profiles (extends auth.users) ----------
create table if not exists public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  handle text unique not null,
  display_name text,
  created_at timestamptz not null default now()
);

-- ---------- 2. sleep_sessions (one row per night per source) ----------
create table if not exists public.sleep_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  night_date date not null,               -- date the night "belongs to" (morning date)
  source text not null default 'synthetic', -- synthetic | fitbit | healthkit | health_connect
  started_at timestamptz not null,
  ended_at timestamptz not null,
  epoch_minutes int not null default 5,
  stats jsonb,                            -- cached NightStats (avg_hr, rem_minutes, ...)
  created_at timestamptz not null default now(),
  unique (user_id, night_date, source)
);

-- ---------- 3. biometric_samples (time series, 5-min epochs) ----------
create table if not exists public.biometric_samples (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.profiles (id) on delete cascade,
  session_id uuid not null references public.sleep_sessions (id) on delete cascade,
  ts timestamptz not null,
  hr numeric(5,1) not null,               -- heart rate bpm
  stage text not null,                    -- awake | light | deep | rem
  unique (session_id, ts)
);

-- Hot paths: "give me this user's night ordered by time"
create index if not exists idx_biosamples_user_ts
  on public.biometric_samples (user_id, ts);
create index if not exists idx_biosamples_session
  on public.biometric_samples (session_id);

-- ---------- 4. dreams (raw text + structured extraction) ----------
create table if not exists public.dreams (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  night_date date not null,
  reported_at timestamptz not null default now(),  -- freshness check input
  raw_text text not null check (char_length(raw_text) >= 12),
  structured jsonb,                       -- scenes, entities, valence, arousal, sentiments, source
  created_at timestamptz not null default now()
);

create index if not exists idx_dreams_user_night
  on public.dreams (user_id, night_date);

-- ---------- 5. generations (Anti-Fake verdict + video job) ----------
create table if not exists public.generations (
  id uuid primary key default gen_random_uuid(),
  dream_id uuid not null references public.dreams (id) on delete cascade,
  user_id uuid not null references public.profiles (id) on delete cascade,
  status text not null default 'pending', -- pending | rejected | rendering | done | failed
  antifake_score numeric(5,1),
  antifake_passed boolean,
  antifake_report jsonb,                  -- full per-check breakdown (explainable)
  video_provider text,                    -- mock | replicate
  video_url text,
  created_at timestamptz not null default now()
);

create index if not exists idx_generations_user
  on public.generations (user_id, created_at desc);

-- ---------- 6. posts (only verified content reaches the feed) ----------
create table if not exists public.posts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles (id) on delete cascade,
  generation_id uuid not null references public.generations (id) on delete cascade,
  caption text,
  verified boolean not null default true, -- invariant: feed only holds verified posts
  sentiments jsonb,                       -- {nostalgia, tenderness, calm, longing}
  video_url text,
  created_at timestamptz not null default now()
);

create index if not exists idx_posts_created
  on public.posts (created_at desc);

-- ---------- 7. Row Level Security ----------
alter table public.profiles         enable row level security;
alter table public.sleep_sessions   enable row level security;
alter table public.biometric_samples enable row level security;
alter table public.dreams           enable row level security;
alter table public.generations      enable row level security;
alter table public.posts            enable row level security;

-- Own-data policies (biometrics and dreams are private by default)
create policy "own profile"        on public.profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);
create policy "own sessions"       on public.sleep_sessions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own samples"        on public.biometric_samples
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own dreams"         on public.dreams
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "own generations"    on public.generations
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Posts: owner writes, everyone reads (it's a social feed)
create policy "own posts write"    on public.posts
  for insert with check (auth.uid() = user_id);
create policy "own posts update"   on public.posts
  for update using (auth.uid() = user_id);
create policy "public feed read"   on public.posts
  for select using (true);

-- ---------- 8. Storage bucket for rendered videos ----------
-- Run once (or create "dream-videos" bucket from Dashboard > Storage):
insert into storage.buckets (id, name, public)
values ('dream-videos', 'dream-videos', true)
on conflict (id) do nothing;
