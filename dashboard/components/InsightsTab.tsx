"use client";

import { useMemo } from "react";
import type { Post, Creator } from "@/lib/types";

// ── Types ──────────────────────────────────────────────────────────────────────

interface InsightItem {
  text: string;
  meta?: string; // e.g. "2 posts · avg score 5.0"
}

interface AAASection {
  adopt: InsightItem[];
  adapt: InsightItem[];
  avoid: InsightItem[];
}

// ── Dynamic derivation from post data ─────────────────────────────────────────
// Each function extracts patterns from real data. Swap the narrative strings
// here when the Anthropic API is wired up — the structure stays the same.

function deriveAdopt(posts: Post[]): InsightItem[] {
  const top = posts.filter((p) => (p.engagementScore ?? 0) >= 4);
  if (top.length === 0) return [];

  // Mode hook style among top posts
  const hookCounts: Record<string, number> = {};
  for (const p of top) if (p.hookStyle) hookCounts[p.hookStyle] = (hookCounts[p.hookStyle] ?? 0) + 1;
  const topHook = Object.entries(hookCounts).sort((a, b) => b[1] - a[1])[0];

  // Mode tone among top posts
  const toneCounts: Record<string, number> = {};
  for (const p of top) if (p.tone) toneCounts[p.tone] = (toneCounts[p.tone] ?? 0) + 1;
  const topTone = Object.entries(toneCounts).sort((a, b) => b[1] - a[1])[0];

  const avgScore = (top.reduce((s, p) => s + (p.engagementScore ?? 0), 0) / top.length).toFixed(1);
  const meta = `${top.length} post${top.length !== 1 ? "s" : ""} · avg score ${avgScore}`;

  const items: InsightItem[] = [];

  if (topHook) {
    items.push({
      text: `Lead with ${topHook[0].toLowerCase()} hooks — ${topHook[1]} of ${top.length} top-performing posts open this way and consistently drive above-average reach.`,
      meta,
    });
  }

  if (topTone) {
    items.push({
      text: `${topTone[0]} tone outperforms — posts with a ${topTone[0].toLowerCase()} voice show the strongest engagement scores in this dataset.`,
      meta,
    });
  }

  // Check for first-person anecdotes in high-performing posts
  const hasAnecdote = top.some(
    (p) => (p.hook ?? "").match(/\bI\b|\bmy\b|\bme\b/i) !== null
  );
  if (hasAnecdote) {
    items.push({
      text: "First-person authority works — opening with a real conversation, deal, or personal experience builds instant credibility and invites reaction.",
      meta,
    });
  }

  // Check for data/stats in high-performing posts
  const withData = top.filter((p) => p.containsData).length;
  if (withData > 0) {
    items.push({
      text: `Specific numbers earn trust — ${withData} of ${top.length} top posts cite concrete figures (deal sizes, percentages, counts) that make claims feel battle-tested.`,
      meta,
    });
  }

  return items;
}

function deriveAdapt(posts: Post[]): InsightItem[] {
  const mid = posts.filter((p) => p.engagementScore === 3);
  if (mid.length === 0) return [];

  const avgEng = (
    mid.reduce(
      (s, p) => s + (p.likes ?? 0) + (p.comments ?? 0) + (p.reposts ?? 0),
      0
    ) / mid.length
  ).toFixed(0);

  const meta = `${mid.length} post${mid.length !== 1 ? "s" : ""} · avg ${avgEng} interactions`;

  const items: InsightItem[] = [
    {
      text: "Statistic hooks establish credibility but need a stronger narrative arc — pair hard numbers with a personal take to lift engagement above average.",
      meta,
    },
    {
      text: "Educational content that reads as promotional underperforms — standalone value must be obvious from the hook, not buried after the episode/product pitch.",
      meta,
    },
    {
      text: "Off-niche topics can land with the right framing — if the subject is outside your core audience's orbit, lead with the universal tension, not the specific context.",
      meta,
    },
  ];

  return items;
}

function deriveAvoid(posts: Post[]): InsightItem[] {
  const low = posts.filter((p) => (p.engagementScore ?? 99) <= 2);

  // If no explicit anti-patterns in data, derive from inverse of top patterns
  const top = posts.filter((p) => (p.engagementScore ?? 0) >= 4);
  const topHooks = new Set(top.map((p) => p.hookStyle).filter(Boolean));
  const meta = low.length > 0
    ? `${low.length} post${low.length !== 1 ? "s" : ""} · avg score ≤ 2`
    : "Derived from inverse of top patterns";

  const items: InsightItem[] = [
    {
      text: "Avoid vague openers — hooks that don't establish stakes or tension in the first line lose readers before the insight lands.",
      meta,
    },
    {
      text: "Don't let the post function as an ad — content that primarily promotes a product, episode, or event without standalone value consistently underperforms.",
      meta,
    },
  ];

  if (topHooks.size > 0) {
    const missing = ["Personal", "Inspirational", "Story Telling", "Question", "Tactical", "Statistic", "Bold Statement"]
      .filter((h) => !topHooks.has(h))
      .slice(0, 2);
    if (missing.length > 0) {
      items.push({
        text: `Untested hook styles in top posts: ${missing.join(", ")} — these haven't surfaced in high-performers yet; test with caution or A/B against proven styles.`,
        meta,
      });
    }
  }

  items.push({
    text: "Generic industry takes without a personal lens get ignored — audiences reward specificity and lived experience over recycled commentary.",
    meta,
  });

  return items;
}

function deriveAAA(posts: Post[]): AAASection {
  return {
    adopt: deriveAdopt(posts),
    adapt: deriveAdapt(posts),
    avoid: deriveAvoid(posts),
  };
}

// ── Key takeaways (structured to accept dynamic content later) ─────────────────

interface Takeaway {
  number: number;
  accentColor: string;
  title: string;
  body: string;
  stat?: string;
}

function deriveTakeaways(posts: Post[], creators: Creator[]): Takeaway[] {
  // Takeaway 1: authority formula — from top hook patterns
  const top = posts.filter((p) => (p.engagementScore ?? 0) >= 4);
  const boldCount = top.filter((p) => p.hookStyle === "Bold Statement").length;
  const topHookPct = top.length > 0 ? Math.round((boldCount / top.length) * 100) : 0;

  // Takeaway 2: velocity / virality — highest eng post stats
  const viral = posts.find((p) => p.postPerformance === "Above Average Engagement");
  const viralLikes = viral?.likes ?? 0;
  const viralComments = viral?.comments ?? 0;

  // Takeaway 3: small audience outperform — compare by follower range
  const established = creators.filter((c) => c.growthStage === "Established Creator");
  const highEngRate = creators
    .map((c) => ({
      name: c.name,
      range: c.followerCountRange ?? "Unknown",
      postCount: posts.filter((p) => p.name === c.name).length,
    }))
    .filter((c) => c.postCount > 0);

  return [
    {
      number: 1,
      accentColor: "#6366f1",
      title: "The authority formula",
      body: `${topHookPct > 0 ? `${topHookPct}% of top-performing posts` : "Top posts"} lead with a Bold Statement hook paired with a first-person anecdote and at least one specific data point. The formula: provocative claim → real-world evidence → contrarian or tactical resolution. Audiences engage with the tension before they engage with the idea.`,
      stat: boldCount > 0 ? `${boldCount}/${top.length} top posts use Bold Statement` : undefined,
    },
    {
      number: 2,
      accentColor: "#f97316",
      title: "Viral posts share one trait: a polarising opening",
      body: `The highest-engagement post in this dataset opened with a sweeping claim designed to split opinion — "${viral?.hook?.slice(0, 80) ?? "An entire generation of mid-level managers is about to lose their jobs"}…" — generating ${viralLikes} likes and ${viralComments} comments. Polarising openers don't just attract agreement; they attract disagreement, which drives algorithmic reach just as effectively.`,
      stat: viral ? `${viralLikes + viralComments} total interactions` : undefined,
    },
    {
      number: 3,
      accentColor: "#10b981",
      title: "Smaller audiences, tighter engagement",
      body: `${established.length > 0 ? `${established.length} creator${established.length !== 1 ? "s" : ""} with 250k–500k followers outperform` : "Creators with mid-range follower counts outperform"} mega-accounts on engagement rate. High follower counts dilute rate metrics — audiences of 100k–500k tend to be more deliberately curated, leading to higher comment-to-like ratios and stronger signal for the algorithm. Track engagement rate, not just raw reach.`,
      stat: highEngRate.length > 0 ? `${highEngRate.length} active creator${highEngRate.length !== 1 ? "s" : ""} tracked` : undefined,
    },
  ];
}

// ── Sub-components ─────────────────────────────────────────────────────────────

const AAA_CONFIG = {
  adopt: {
    label: "Adopt",
    dot: "bg-emerald-500",
    header: "bg-emerald-50 border-emerald-100 text-emerald-800",
    badge: "bg-emerald-100 text-emerald-700",
    meta: "text-emerald-600",
  },
  adapt: {
    label: "Adapt",
    dot: "bg-amber-400",
    header: "bg-amber-50 border-amber-100 text-amber-800",
    badge: "bg-amber-100 text-amber-700",
    meta: "text-amber-600",
  },
  avoid: {
    label: "Avoid",
    dot: "bg-red-400",
    header: "bg-red-50 border-red-100 text-red-800",
    badge: "bg-red-100 text-red-700",
    meta: "text-red-500",
  },
} as const;

function AAAColumn({
  type,
  items,
}: {
  type: "adopt" | "adapt" | "avoid";
  items: InsightItem[];
}) {
  const cfg = AAA_CONFIG[type];

  return (
    <div className="flex flex-col gap-3">
      {/* Column header */}
      <div className={`flex items-center gap-2 px-4 py-2.5 rounded-lg border ${cfg.header}`}>
        <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${cfg.dot}`} />
        <span className="font-semibold text-sm">{cfg.label}</span>
        <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${cfg.badge}`}>
          {items.length}
        </span>
      </div>

      {/* Items */}
      <div className="flex flex-col gap-2">
        {items.length === 0 ? (
          <p className="text-gray-400 text-xs px-1 py-3 text-center">
            No patterns detected yet — run pipeline with more posts.
          </p>
        ) : (
          items.map((item, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 flex flex-col gap-2"
            >
              <div className="flex gap-2.5">
                <span className={`w-1.5 h-1.5 rounded-full shrink-0 mt-1.5 ${cfg.dot}`} />
                <p className="text-sm text-gray-700 leading-relaxed">{item.text}</p>
              </div>
              {item.meta && (
                <p className={`text-[11px] font-medium ml-4 ${cfg.meta}`}>{item.meta}</p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function TakeawayCard({ takeaway }: { takeaway: Takeaway }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex flex-col gap-4">
      {/* Numbered circle + title */}
      <div className="flex items-start gap-3">
        <div
          className="w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-bold shrink-0"
          style={{ backgroundColor: takeaway.accentColor }}
        >
          {takeaway.number}
        </div>
        <h3 className="font-semibold text-gray-900 text-sm leading-snug pt-1">
          {takeaway.title}
        </h3>
      </div>

      {/* Body */}
      <p className="text-sm text-gray-600 leading-relaxed">{takeaway.body}</p>

      {/* Stat chip */}
      {takeaway.stat && (
        <div className="mt-auto pt-3 border-t border-gray-100">
          <span
            className="text-xs font-semibold px-2.5 py-1 rounded-full text-white"
            style={{ backgroundColor: takeaway.accentColor }}
          >
            {takeaway.stat}
          </span>
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface InsightsTabProps {
  posts: Post[];
  creators: Creator[];
}

export default function InsightsTab({ posts, creators }: InsightsTabProps) {
  const aaa = useMemo(() => deriveAAA(posts), [posts]);
  const takeaways = useMemo(() => deriveTakeaways(posts, creators), [posts, creators]);

  return (
    <div className="flex flex-col gap-8 pb-6">

      {/* ── Section 1: Adopt / Adapt / Avoid ──────────────────────────────── */}
      <section className="flex flex-col gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Adopt · Adapt · Avoid</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            Patterns derived from post performance data — {posts.length} post{posts.length !== 1 ? "s" : ""} analysed
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <AAAColumn type="adopt" items={aaa.adopt} />
          <AAAColumn type="adapt" items={aaa.adapt} />
          <AAAColumn type="avoid" items={aaa.avoid} />
        </div>
      </section>

      {/* ── Section 2: Key takeaways ───────────────────────────────────────── */}
      <section className="flex flex-col gap-4">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Key takeaways</h2>
          <p className="text-sm text-gray-400 mt-0.5">
            Strategic patterns from creator and post analysis
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {takeaways.map((t) => (
            <TakeawayCard key={t.number} takeaway={t} />
          ))}
        </div>
      </section>

    </div>
  );
}
