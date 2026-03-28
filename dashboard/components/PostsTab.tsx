"use client";

import { useState } from "react";
import type { Post } from "@/lib/types";

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtDate(d: string | null): string {
  if (!d) return "—";
  const dt = new Date(d);
  if (isNaN(dt.getTime())) return d;
  return dt.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function fmtEngRate(total: number, followers: number): string {
  if (followers === 0) return "—";
  return ((total / followers) * 100).toFixed(2) + "%";
}

function isViral(post: Post): boolean {
  return post.postPerformance === "Above Average Engagement";
}

function isAntiPattern(post: Post): boolean {
  return post.engagementScore !== null && post.engagementScore <= 2;
}

// "Swipe file" = high-quality posts worth saving (hookStrength ≥ 4 and engagementScore ≥ 4)
function isSwipeFile(post: Post): boolean {
  return (post.hookStrength ?? 0) >= 4 && (post.engagementScore ?? 0) >= 4;
}

type FormatFilter = "All" | "Text" | "Carousel" | "Video" | "Viral" | "Swipe";

function matchesFormat(post: Post, filter: FormatFilter): boolean {
  if (filter === "All") return true;
  const fmt = post.postFormat ?? "";
  if (filter === "Text") return fmt.includes("Text");
  if (filter === "Carousel") return fmt.includes("Image") || fmt === "Long Text + Image";
  if (filter === "Video") return fmt === "Video";
  if (filter === "Viral") return isViral(post);
  if (filter === "Swipe") return isSwipeFile(post);
  return true;
}

// ── Format + topic badge colors ────────────────────────────────────────────────

const FORMAT_COLORS: Record<string, string> = {
  "Long Text":       "bg-slate-100 text-slate-600",
  "Short Text":      "bg-gray-100 text-gray-600",
  "Long Text + Image": "bg-violet-50 text-violet-700",
  "Image":           "bg-violet-50 text-violet-600",
  "Video":           "bg-blue-50 text-blue-700",
};

const TONE_COLORS: Record<string, string> = {
  Personal:      "bg-pink-50 text-pink-700",
  Educational:   "bg-sky-50 text-sky-700",
  Inspirational: "bg-amber-50 text-amber-700",
  Contrarian:    "bg-red-50 text-red-700",
  Tactical:      "bg-green-50 text-green-700",
};

const HOOK_STYLE_COLORS: Record<string, string> = {
  Personal:       "bg-pink-50 text-pink-600",
  Inspirational:  "bg-amber-50 text-amber-600",
  "Story Telling":"bg-purple-50 text-purple-600",
  "Bold Statement":"bg-orange-50 text-orange-600",
  Question:       "bg-cyan-50 text-cyan-600",
  Statistic:      "bg-teal-50 text-teal-700",
  Tactical:       "bg-green-50 text-green-700",
};

// ── Hook strength dots ─────────────────────────────────────────────────────────

function HookDots({ strength }: { strength: number | null }) {
  const filled = strength ?? 0;
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: 5 }, (_, i) => (
        <span
          key={i}
          className={`w-2 h-2 rounded-full ${i < filled ? "bg-emerald-500" : "bg-gray-200"}`}
        />
      ))}
    </div>
  );
}

// ── Small tag pill ─────────────────────────────────────────────────────────────

function MiniTag({ label, colorClass }: { label: string; colorClass: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${colorClass}`}>
      {label}
    </span>
  );
}

// ── Post card ──────────────────────────────────────────────────────────────────

function PostCard({ post, followers }: { post: Post; followers: number }) {
  const [notes, setNotes] = useState("");
  const viral = isViral(post);
  const antiPattern = isAntiPattern(post);

  const total = (post.likes ?? 0) + (post.comments ?? 0) + (post.reposts ?? 0);
  const fmt = post.postFormat ?? "—";
  const fmtColor = FORMAT_COLORS[fmt] ?? "bg-gray-100 text-gray-600";

  // Left border + dim logic
  const borderClass = viral
    ? "border-l-4 border-l-orange-400"
    : antiPattern
    ? "border-l-4 border-l-red-400"
    : "";
  const dimClass = antiPattern ? "opacity-60" : "";

  return (
    <div
      className={`bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col gap-3.5 p-5 hover:shadow-md transition-shadow ${borderClass} ${dimClass}`}
    >
      {/* Header: creator + date */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-[11px] font-bold text-gray-600 shrink-0">
            {post.name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase()}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900 leading-tight truncate">{post.name}</p>
            <p className="text-[11px] text-gray-400">{fmtDate(post.postDate)}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          {viral && (
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-orange-50 text-orange-600 border border-orange-200">
              Viral
            </span>
          )}
          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${fmtColor}`}>
            {fmt}
          </span>
        </div>
      </div>

      {/* Topic badge */}
      {post.primaryTopic && (
        <span className="self-start text-[11px] font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700">
          {post.primaryTopic}
        </span>
      )}

      {/* Hook text */}
      <p className="text-sm text-gray-800 leading-snug font-medium line-clamp-4">
        {post.hook ?? post.topicSubject ?? "—"}
      </p>

      {/* Stats row */}
      <div className="grid grid-cols-4 text-center divide-x divide-gray-100">
        <div className="pr-2">
          <p className="text-sm font-bold text-emerald-500">{fmtEngRate(total, followers)}</p>
          <p className="text-[10px] text-gray-400">Eng. rate</p>
        </div>
        <div className="px-2">
          <p className="text-sm font-bold text-gray-900">{post.likes ?? 0}</p>
          <p className="text-[10px] text-gray-400">Likes</p>
        </div>
        <div className="px-2">
          <p className="text-sm font-bold text-gray-900">{post.comments ?? 0}</p>
          <p className="text-[10px] text-gray-400">Comments</p>
        </div>
        <div className="pl-2">
          <p className="text-sm font-bold text-gray-900">{post.reposts ?? 0}</p>
          <p className="text-[10px] text-gray-400">Reposts</p>
        </div>
      </div>

      {/* Hook strength + tags */}
      <div className="flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <span className="text-[11px] text-gray-400 font-medium">Hook</span>
          <HookDots strength={post.hookStrength} />
        </div>
        <div className="flex items-center gap-1.5 flex-wrap">
          {post.hookStyle && (
            <MiniTag
              label={post.hookStyle}
              colorClass={HOOK_STYLE_COLORS[post.hookStyle] ?? "bg-gray-100 text-gray-600"}
            />
          )}
          {post.tone && (
            <MiniTag
              label={post.tone}
              colorClass={TONE_COLORS[post.tone] ?? "bg-gray-100 text-gray-600"}
            />
          )}
        </div>
      </div>

      {/* Notes textarea */}
      <textarea
        className="w-full text-xs text-gray-500 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-gray-300 placeholder:text-gray-300"
        rows={2}
        placeholder="Add notes…"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />

      {/* Post link */}
      {post.postUrl && (
        <a
          href={post.postUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[11px] text-indigo-500 hover:text-indigo-700 truncate"
        >
          View post →
        </a>
      )}
    </div>
  );
}

// ── Filter chips ───────────────────────────────────────────────────────────────

const CHIPS: { label: string; value: FormatFilter }[] = [
  { label: "All",        value: "All" },
  { label: "Text",       value: "Text" },
  { label: "Carousel",   value: "Carousel" },
  { label: "Video",      value: "Video" },
  { label: "Viral only", value: "Viral" },
  { label: "Swipe file", value: "Swipe" },
];

// ── Main component ─────────────────────────────────────────────────────────────

interface PostsTabProps {
  posts: Post[];
  followerMap: Record<string, number>;
}

export default function PostsTab({ posts, followerMap }: PostsTabProps) {
  const [search, setSearch] = useState("");
  const [formatFilter, setFormatFilter] = useState<FormatFilter>("All");

  // Sort by engagement score descending (nulls last)
  const sorted = [...posts].sort(
    (a, b) => (b.engagementScore ?? -1) - (a.engagementScore ?? -1)
  );

  const filtered = sorted.filter((p) => {
    const q = search.toLowerCase();
    const matchesSearch =
      q === "" ||
      (p.hook ?? "").toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      (p.primaryTopic ?? "").toLowerCase().includes(q);
    return matchesSearch && matchesFormat(p, formatFilter);
  });

  // Per-chip counts (after search only, not format filter — shows real distribution)
  const chipCounts = (chip: FormatFilter) =>
    sorted.filter(
      (p) =>
        (search === "" ||
          (p.hook ?? "").toLowerCase().includes(search.toLowerCase()) ||
          p.name.toLowerCase().includes(search.toLowerCase()) ||
          (p.primaryTopic ?? "").toLowerCase().includes(search.toLowerCase())) &&
        matchesFormat(p, chip)
    ).length;

  return (
    <div className="flex flex-col gap-5">
      {/* Search + filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
            fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"
          >
            <circle cx="11" cy="11" r="8" />
            <path d="m21 21-4.35-4.35" />
          </svg>
          <input
            type="text"
            placeholder="Search posts…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 text-sm rounded-full border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-gray-200 w-56 placeholder:text-gray-400"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {CHIPS.map(({ label, value }) => {
            const count = chipCounts(value);
            if (value !== "All" && count === 0) return null;
            const active = formatFilter === value;
            return (
              <button
                key={value}
                onClick={() => setFormatFilter(value)}
                className={[
                  "px-3.5 py-1.5 rounded-full text-sm font-medium transition-colors border",
                  active
                    ? "bg-gray-900 text-white border-gray-900"
                    : "bg-white text-gray-600 border-gray-200 hover:border-gray-400",
                ].join(" ")}
              >
                {label}
                <span className={`ml-1.5 text-xs ${active ? "text-white/70" : "text-gray-400"}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="rounded-xl border border-dashed border-gray-300 bg-white/50 py-12 text-center">
          <p className="text-gray-400 text-sm">No posts match your filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((post) => (
            <PostCard
              key={post.postUrl ?? `${post.name}-${post.postDate}`}
              post={post}
              followers={followerMap[post.name] ?? 0}
            />
          ))}
        </div>
      )}
    </div>
  );
}
