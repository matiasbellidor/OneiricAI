import type { Post } from "../types";
import VerifiedBadge from "./VerifiedBadge";

const SENT_LABELS: Record<string, string> = {
  nostalgia: "Nostalgia",
  tenderness: "Ternura",
  calm: "Calma",
  longing: "Añoranza",
};

function topSentiment(p: Post): [string, number] {
  const entries = Object.entries(p.sentiments) as Array<[string, number]>;
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0] ?? ["calm", 0];
}

function thumbGradient(p: Post): string {
  const sc = p.scenes[0] ?? { valence: 0, arousal: 0.2 };
  if (sc.valence >= 0.15 && sc.arousal < 0.45)
    return "linear-gradient(160deg,#2A1F3D 0%,#8A79D6 60%,#E8C398 110%)";
  if (sc.valence >= 0.15) return "linear-gradient(160deg,#1E2A3D 0%,#5B8DD6 60%,#9AE0C8 110%)";
  if (sc.valence <= -0.15) return "linear-gradient(160deg,#141824 0%,#3D4A6B 70%,#8E8798 120%)";
  return "linear-gradient(160deg,#191625 0%,#6B5FA8 65%,#B8AECF 115%)";
}

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString("es-AR", { day: "numeric", month: "short" });
}

export default function Feed({ posts }: { posts: Post[] }) {
  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-baseline justify-between">
        <span className="eyebrow">Feed — Solo sueños verificados</span>
        <span className="font-mono text-[10px] text-muted">{posts.length} sueños</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {posts.map((p) => {
          const [sk, sv] = topSentiment(p);
          return (
            <article key={p.id} className="rounded-2xl border border-line bg-panel overflow-hidden group">
              <div className="relative aspect-[3/4]" style={{ background: thumbGradient(p) }}>
                <div className="absolute inset-0 bg-gradient-to-t from-night/80 via-transparent to-night/20" />
                <div className="absolute left-3 top-3">
                  <VerifiedBadge compact />
                </div>
                <p className="absolute inset-x-4 bottom-4 font-display text-[15px] leading-snug text-ivory clamp-2">
                  {p.scenes[0]?.text ?? p.caption}
                </p>
              </div>
              <div className="flex flex-col gap-2 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-[11px] text-violet">{p.handle}</span>
                  <span className="font-mono text-[10px] text-muted">{fmtDate(p.created_at)}</span>
                </div>
                <p className="text-xs text-muted leading-relaxed clamp-2">{p.caption}</p>
                <span className="self-start rounded-full border border-line px-2.5 py-1 font-mono text-[9px] uppercase tracking-[0.14em] text-muted">
                  {SENT_LABELS[sk] ?? sk} {Math.round(sv * 100)}%
                </span>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
