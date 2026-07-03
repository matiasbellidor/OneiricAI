import { useMemo } from "react";
import type { SleepSession } from "../types";
import { computeFeatures } from "../lib/demoEngine";

const W = 640;
const H = 240;
const PAD = { top: 18, right: 14, bottom: 30, left: 40 };
const HR_MIN = 42;
const HR_MAX = 80;

const y = (hr: number) =>
  PAD.top + (1 - (hr - HR_MIN) / (HR_MAX - HR_MIN)) * (H - PAD.top - PAD.bottom);

export default function NightPanel({ session }: { session: SleepSession | null }) {
  const view = useMemo(() => {
    if (!session || !session.samples.length) return null;
    const n = session.samples.length;
    const x = (i: number) => PAD.left + (i / (n - 1)) * (W - PAD.left - PAD.right);

    const points = session.samples.map((s, i) => `${x(i).toFixed(1)},${y(s.heart_rate).toFixed(1)}`).join(" ");

    // Contiguous REM bands + awake ticks
    const remBands: Array<{ x0: number; x1: number }> = [];
    const awakeTicks: number[] = [];
    let bandStart: number | null = null;
    session.samples.forEach((s, i) => {
      if (s.sleep_stage === "rem") {
        if (bandStart === null) bandStart = i;
      } else {
        if (bandStart !== null) {
          remBands.push({ x0: x(bandStart), x1: x(i) });
          bandStart = null;
        }
        if (s.sleep_stage === "awake") awakeTicks.push(x(i));
      }
    });
    if (bandStart !== null) remBands.push({ x0: x(bandStart), x1: x(n - 1) });

    // X labels every 2 h
    const start = new Date(session.start_ts).getTime();
    const end = new Date(session.end_ts).getTime();
    const labels: Array<{ x: number; t: string }> = [];
    for (let t = Math.ceil(start / 7_200_000) * 7_200_000; t <= end; t += 7_200_000) {
      const frac = (t - start) / (end - start);
      const d = new Date(t);
      labels.push({
        x: PAD.left + frac * (W - PAD.left - PAD.right),
        t: `${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`,
      });
    }

    const f = computeFeatures(session);
    return { points, remBands, awakeTicks, labels, baseline: f.baseline_hr };
  }, [session]);

  const st = session?.stats ?? null;

  return (
    <section className="rounded-2xl border border-line bg-panel p-6 flex flex-col gap-4">
      <div className="flex items-baseline justify-between">
        <span className="eyebrow">02 — Tu noche, según tu cuerpo</span>
        <span className="font-mono text-[10px] text-muted">
          {session ? `fuente: ${session.source}` : "cargando…"}
        </span>
      </div>

      {view ? (
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Frecuencia cardíaca y fases REM de la noche">
          {/* REM bands */}
          {view.remBands.map((b, i) => (
            <rect key={i} x={b.x0} y={PAD.top} width={b.x1 - b.x0} height={H - PAD.top - PAD.bottom}
              fill="#8A79D6" opacity="0.14" />
          ))}
          {/* Awake ticks */}
          {view.awakeTicks.map((tx, i) => (
            <line key={i} x1={tx} x2={tx} y1={PAD.top} y2={H - PAD.bottom} stroke="#E0684B" opacity="0.28" strokeWidth="1" />
          ))}
          {/* Baseline (median non-REM HR) */}
          <line x1={PAD.left} x2={W - PAD.right} y1={y(view.baseline)} y2={y(view.baseline)}
            stroke="#8E8798" strokeWidth="1" strokeDasharray="4 5" opacity="0.55" />
          <text x={W - PAD.right} y={y(view.baseline) - 5} textAnchor="end" fill="#8E8798"
            fontSize="9" fontFamily="JetBrains Mono, monospace">base {view.baseline.toFixed(0)}</text>
          {/* Y axis labels */}
          {[45, 60, 75].map((hr) => (
            <g key={hr}>
              <text x={PAD.left - 8} y={y(hr) + 3} textAnchor="end" fill="#8E8798" fontSize="9"
                fontFamily="JetBrains Mono, monospace">{hr}</text>
              <line x1={PAD.left} x2={W - PAD.right} y1={y(hr)} y2={y(hr)} stroke="#262230" strokeWidth="1" />
            </g>
          ))}
          {/* X labels */}
          {view.labels.map((l, i) => (
            <text key={i} x={l.x} y={H - 10} textAnchor="middle" fill="#8E8798" fontSize="9"
              fontFamily="JetBrains Mono, monospace">{l.t}</text>
          ))}
          {/* HR line */}
          <polyline points={view.points} fill="none" stroke="#E0684B" strokeWidth="1.8"
            strokeLinejoin="round" strokeLinecap="round" />
        </svg>
      ) : (
        <div className="h-[200px] rounded-xl border border-line bg-night/40 animate-pulse" />
      )}

      {st && (
        <div className="grid grid-cols-4 gap-3">
          {[
            ["FC prom", `${st.avg_hr.toFixed(0)} lpm`],
            ["FC mín", `${st.min_hr.toFixed(0)} lpm`],
            ["REM", `${st.rem_minutes.toFixed(0)} min`],
            ["Eficiencia", `${Math.round(st.efficiency * 100)}%`],
          ].map(([k, v]) => (
            <div key={k} className="rounded-xl border border-line bg-night/40 px-3 py-2.5">
              <div className="font-mono text-[9px] uppercase tracking-[0.14em] text-muted">{k}</div>
              <div className="mt-0.5 font-display text-lg text-ivory">{v}</div>
            </div>
          ))}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-4 font-mono text-[10px] text-muted">
        <span className="inline-flex items-center gap-1.5">
          <i className="inline-block h-2.5 w-2.5 rounded-sm bg-violet/40" /> fase REM
        </span>
        <span className="inline-flex items-center gap-1.5">
          <i className="inline-block h-0.5 w-4 bg-coral" /> frecuencia cardíaca
        </span>
        <span className="inline-flex items-center gap-1.5">
          <i className="inline-block h-2.5 w-px bg-coral/60" /> despertar
        </span>
      </div>
    </section>
  );
}
