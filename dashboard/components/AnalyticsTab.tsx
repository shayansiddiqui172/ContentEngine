"use client";

import { useMemo, useState } from "react";
import type { Post } from "@/lib/types";

// ── Palette ────────────────────────────────────────────────────────────────────

const CHART_COLORS = ["#6366f1","#10b981","#f97316","#f59e0b","#8b5cf6","#ec4899","#14b8a6","#64748b"];

function formatFill(fmt: string): string {
  const f = fmt.toLowerCase();
  if (f.includes("text"))  return "#10b981";
  if (f.includes("image") || f.includes("carousel")) return "#8b5cf6";
  if (f === "video")       return "#f97316";
  return "#f59e0b";
}

// ── Data transforms ────────────────────────────────────────────────────────────

function avgEngByFormat(posts: Post[], followerMap: Record<string, number>) {
  const groups: Record<string, number[]> = {};
  for (const p of posts) {
    const fmt = p.postFormat ?? "Unknown";
    const fc = followerMap[p.name] ?? 0;
    if (fc === 0) continue;
    const total = (p.likes ?? 0) + (p.comments ?? 0) + (p.reposts ?? 0);
    groups[fmt] = groups[fmt] ?? [];
    groups[fmt].push((total / fc) * 100);
  }
  return Object.entries(groups)
    .map(([format, rates]) => ({
      label: format,
      value: rates.reduce((a, b) => a + b, 0) / rates.length,
      color: formatFill(format),
    }))
    .sort((a, b) => b.value - a.value);
}

function avgScoreByHookStyle(posts: Post[]) {
  const groups: Record<string, number[]> = {};
  for (const p of posts) {
    if (!p.hookStyle || p.engagementScore === null) continue;
    groups[p.hookStyle] = groups[p.hookStyle] ?? [];
    groups[p.hookStyle].push(p.engagementScore);
  }
  return Object.entries(groups)
    .map(([style, scores], i) => ({
      label: style,
      value: scores.reduce((a, b) => a + b, 0) / scores.length,
      color: CHART_COLORS[i % CHART_COLORS.length],
    }))
    .sort((a, b) => b.value - a.value);
}

function topicDist(posts: Post[]) {
  const counts: Record<string, number> = {};
  for (const p of posts) {
    const t = p.primaryTopic ?? "Unknown";
    counts[t] = (counts[t] ?? 0) + 1;
  }
  const total = posts.length || 1;
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 7)
    .map(([name, value], i) => ({
      name,
      value,
      pct: Math.round((value / total) * 100),
      color: CHART_COLORS[i % CHART_COLORS.length],
    }));
}

interface ScatterPoint {
  x: number; y: number; viral: boolean; topic: string; name: string;
}

function scatterPoints(posts: Post[]): ScatterPoint[] {
  return posts
    .filter((p) => p.hookStrength !== null && p.engagementScore !== null)
    .map((p) => ({
      x: p.hookStrength as number,
      y: p.engagementScore as number,
      viral: p.postPerformance === "Above Average Engagement",
      topic: p.primaryTopic ?? "—",
      name: p.name,
    }));
}

// ── Chart card wrapper ─────────────────────────────────────────────────────────

function ChartCard({
  title, subtitle, children, legend,
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
  legend?: { color: string; label: string }[];
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-4">
      <div>
        <p className="text-sm font-semibold text-gray-900">{title}</p>
        {subtitle && <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex-1">{children}</div>
      {legend && legend.length > 0 && (
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 pt-2 border-t border-gray-100">
          {legend.map((l) => (
            <div key={l.label} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: l.color }} />
              <span className="text-[11px] text-gray-500">{l.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="h-44 flex items-center justify-center">
      <p className="text-gray-400 text-xs text-center px-4">{message}</p>
    </div>
  );
}

// ── Tooltip state ──────────────────────────────────────────────────────────────

function Tooltip({ children, tip }: { children: React.ReactNode; tip: string }) {
  const [show, setShow] = useState(false);
  return (
    <div
      className="relative"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div className="absolute z-10 bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2.5 py-1.5 bg-gray-900 text-white text-[11px] rounded-lg whitespace-nowrap shadow-lg pointer-events-none">
          {tip}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-gray-900" />
        </div>
      )}
    </div>
  );
}

// ── Chart 1: Vertical bar chart ────────────────────────────────────────────────

function VerticalBarChart({ data }: { data: { label: string; value: number; color: string }[] }) {
  if (data.length === 0) return <EmptyChart message="No data available" />;
  const max = Math.max(...data.map((d) => d.value));
  return (
    <div className="flex items-end gap-3 h-44 pt-4">
      {data.map((d) => {
        const heightPct = max > 0 ? (d.value / max) * 100 : 0;
        return (
          <Tooltip key={d.label} tip={`${d.label}: ${d.value.toFixed(3)}%`}>
            <div className="flex-1 flex flex-col items-center gap-1.5 cursor-default">
              <span className="text-[10px] text-gray-500 font-medium">{d.value.toFixed(2)}%</span>
              <div className="w-full flex items-end" style={{ height: 120 }}>
                <div
                  className="w-full rounded-t-md transition-all"
                  style={{ height: `${heightPct}%`, backgroundColor: d.color }}
                />
              </div>
              <span className="text-[10px] text-gray-400 text-center leading-tight max-w-[60px] break-words">
                {d.label}
              </span>
            </div>
          </Tooltip>
        );
      })}
    </div>
  );
}

// ── Chart 2: Horizontal bar chart ─────────────────────────────────────────────

function HorizontalBarChart({ data }: { data: { label: string; value: number; color: string }[] }) {
  if (data.length === 0) return <EmptyChart message="No data available" />;
  const max = 5; // scores are 1-5
  return (
    <div className="flex flex-col gap-2.5 py-1">
      {data.map((d) => (
        <Tooltip key={d.label} tip={`${d.label}: ${d.value.toFixed(2)} / 5`}>
          <div className="flex items-center gap-2 cursor-default">
            <span className="text-[11px] text-gray-600 w-28 shrink-0 truncate">{d.label}</span>
            <div className="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${(d.value / max) * 100}%`, backgroundColor: d.color }}
              />
            </div>
            <span className="text-[11px] text-gray-500 font-medium w-6 text-right shrink-0">
              {d.value.toFixed(1)}
            </span>
          </div>
        </Tooltip>
      ))}
    </div>
  );
}

// ── Chart 3: Donut chart (pure SVG) ───────────────────────────────────────────

function DonutChart({ data }: { data: { name: string; value: number; pct: number; color: string }[] }) {
  if (data.length === 0) return <EmptyChart message="No topic data available" />;

  const r = 60;
  const cx = 90;
  const cy = 75;
  const circ = 2 * Math.PI * r;
  const total = data.reduce((s, d) => s + d.value, 0);

  // Build segments
  let cumulative = 0;
  const segments = data.map((d) => {
    const pct = d.value / total;
    const dashLen = pct * circ;
    const offset = -(cumulative * circ);
    cumulative += pct;
    return { ...d, dashLen, offset };
  });

  return (
    <div className="flex items-center justify-center">
      <svg width="180" height="150" viewBox="0 0 180 150">
        {/* Rotate -90 so first segment starts at top */}
        <g transform={`rotate(-90 ${cx} ${cy})`}>
          {segments.map((s) => (
            <circle
              key={s.name}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth="24"
              strokeDasharray={`${s.dashLen} ${circ}`}
              strokeDashoffset={s.offset}
            />
          ))}
        </g>
        {/* Center label */}
        <text x={cx} y={cy - 6} textAnchor="middle" fontSize="20" fontWeight="700" fill="#1a1a1a">
          {total}
        </text>
        <text x={cx} y={cy + 10} textAnchor="middle" fontSize="10" fill="#9ca3af">
          posts
        </text>
      </svg>
    </div>
  );
}

// ── Chart 4: Scatter plot (pure SVG) ──────────────────────────────────────────

function ScatterPlot({ points }: { points: ScatterPoint[] }) {
  if (points.length === 0) {
    return <EmptyChart message="No enriched posts yet — run pipeline with AI key set" />;
  }

  const W = 280;
  const H = 160;
  const pad = { top: 10, right: 16, bottom: 28, left: 28 };
  const iW = W - pad.left - pad.right;
  const iH = H - pad.top - pad.bottom;

  // Scale 1-5 → pixel coords
  const sx = (v: number) => ((v - 1) / 4) * iW;
  const sy = (v: number) => iH - ((v - 1) / 4) * iH;

  const ticks = [1, 2, 3, 4, 5];

  return (
    <div className="flex justify-center">
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
        <g transform={`translate(${pad.left} ${pad.top})`}>
          {/* Grid */}
          {ticks.map((t) => (
            <g key={t}>
              <line x1={sx(t)} y1={0} x2={sx(t)} y2={iH} stroke="#f3f4f6" strokeWidth="1" />
              <line x1={0} y1={sy(t)} x2={iW} y2={sy(t)} stroke="#f3f4f6" strokeWidth="1" />
            </g>
          ))}
          {/* Axis labels */}
          {ticks.map((t) => (
            <g key={`lbl-${t}`}>
              <text x={sx(t)} y={iH + 14} textAnchor="middle" fontSize="9" fill="#9ca3af">{t}</text>
              <text x={-10} y={sy(t) + 3} textAnchor="end" fontSize="9" fill="#9ca3af">{t}</text>
            </g>
          ))}
          {/* Axis titles */}
          <text x={iW / 2} y={iH + 26} textAnchor="middle" fontSize="9" fill="#9ca3af">
            Hook strength
          </text>
          <text
            x={-iH / 2} y={-20} textAnchor="middle" fontSize="9" fill="#9ca3af"
            transform="rotate(-90)"
          >
            Eng. score
          </text>
          {/* Dots */}
          {points.map((p, i) => (
            <g key={i}>
              <title>{`${p.name} — ${p.topic}\nHook: ${p.x}/5  Score: ${p.y}/5${p.viral ? " ⚡ Viral" : ""}`}</title>
              <circle
                cx={sx(p.x)}
                cy={sy(p.y)}
                r={p.viral ? 8 : 6}
                fill={p.viral ? "#f97316" : "#6366f1"}
                fillOpacity={p.viral ? 0.9 : 0.75}
                stroke="white"
                strokeWidth="1.5"
              />
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface AnalyticsTabProps {
  posts: Post[];
  followerMap: Record<string, number>;
}

export default function AnalyticsTab({ posts, followerMap }: AnalyticsTabProps) {
  const formatData = useMemo(() => avgEngByFormat(posts, followerMap), [posts, followerMap]);
  const hookData   = useMemo(() => avgScoreByHookStyle(posts), [posts]);
  const topics     = useMemo(() => topicDist(posts), [posts]);
  const scatter    = useMemo(() => scatterPoints(posts), [posts]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pb-6">

      {/* Chart 1 */}
      <ChartCard
        title="Avg. engagement rate by format"
        subtitle="Avg (likes + comments + reposts) ÷ followers per post"
        legend={formatData.map((d) => ({ color: d.color, label: d.label }))}
      >
        <VerticalBarChart data={formatData} />
      </ChartCard>

      {/* Chart 2 */}
      <ChartCard
        title="Hook style vs. engagement score"
        subtitle="Avg engagement score (1–5) per hook style, sorted descending"
        legend={hookData.map((d) => ({ color: d.color, label: d.label }))}
      >
        <HorizontalBarChart data={hookData} />
      </ChartCard>

      {/* Chart 3 */}
      <ChartCard
        title="Post topic distribution"
        subtitle="Breakdown of posts by primary topic"
        legend={topics.map((d) => ({ color: d.color, label: `${d.name} (${d.pct}%)` }))}
      >
        <DonutChart data={topics} />
      </ChartCard>

      {/* Chart 4 */}
      <ChartCard
        title="Engagement score vs. hook strength"
        subtitle="Each dot is one post — hover for details · orange = viral"
        legend={[
          { color: "#6366f1", label: "Normal post" },
          { color: "#f97316", label: "Viral post"  },
        ]}
      >
        <ScatterPlot points={scatter} />
      </ChartCard>

    </div>
  );
}
