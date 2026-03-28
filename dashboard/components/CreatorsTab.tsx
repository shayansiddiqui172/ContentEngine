"use client";

import { useState } from "react";
import type { Creator, CreatorStats } from "@/lib/types";

// ── Role normalization ─────────────────────────────────────────────────────────

type DisplayRole = "VC" | "Founder" | "Operator" | "Ecosystem Partner" | "Unknown";

function normalizeRole(raw: string | null): DisplayRole {
  if (!raw) return "Unknown";
  const r = raw.toUpperCase();
  if (r === "VC" || r === "VC / INVESTOR") return "VC";
  if (r === "FOUNDER" || r === "STARTUP") return "Founder";
  if (r === "OPERATOR" || r === "AI") return "Operator";
  if (r === "ECOSYSTEM PARTNER") return "Ecosystem Partner";
  return "Unknown";
}

const ROLE_COLORS: Record<DisplayRole, { avatar: string; badge: string; dot: string }> = {
  VC:                 { avatar: "bg-blue-100 text-blue-700",   badge: "bg-blue-50 text-blue-700 border-blue-200",   dot: "bg-blue-400" },
  Founder:            { avatar: "bg-rose-100 text-rose-700",   badge: "bg-rose-50 text-rose-700 border-rose-200",   dot: "bg-rose-400" },
  Operator:           { avatar: "bg-teal-100 text-teal-700",   badge: "bg-teal-50 text-teal-700 border-teal-200",   dot: "bg-teal-400" },
  "Ecosystem Partner":{ avatar: "bg-amber-100 text-amber-700", badge: "bg-amber-50 text-amber-700 border-amber-200", dot: "bg-amber-400" },
  Unknown:            { avatar: "bg-gray-100 text-gray-600",   badge: "bg-gray-50 text-gray-600 border-gray-200",   dot: "bg-gray-400" },
};

const FILTER_CHIPS: Array<{ label: string; role: DisplayRole | "All" }> = [
  { label: "All",              role: "All" },
  { label: "VC",               role: "VC" },
  { label: "Founder",          role: "Founder" },
  { label: "Operator",         role: "Operator" },
  { label: "Ecosystem Partner",role: "Ecosystem Partner" },
];

// ── Formatters ─────────────────────────────────────────────────────────────────

function fmtFollowers(n: number | null): string {
  if (n === null) return "—";
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1).replace(/\.0$/, "") + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
  return String(n);
}

function fmtEngRate(rate: number): string {
  if (rate === 0) return "—";
  return (rate * 100).toFixed(2) + "%";
}

function fmtInfluence(n: number): string {
  if (n === 0) return "—";
  if (n >= 1_000) return (n / 1_000).toFixed(1).replace(/\.0$/, "") + "K";
  return String(n);
}

function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0][0]?.toUpperCase() ?? "?";
  return ((parts[0][0] ?? "") + (parts[parts.length - 1][0] ?? "")).toUpperCase();
}

// ── Tag pill ──────────────────────────────────────────────────────────────────

const TAG_PRESETS: Record<string, string> = {
  "Data Driven":          "bg-sky-50 text-sky-700",
  "Story Telling":        "bg-purple-50 text-purple-700",
  "Tactical":             "bg-green-50 text-green-700",
  "Contrarian":           "bg-orange-50 text-orange-700",
  "Established Creator":  "bg-emerald-50 text-emerald-700",
  "Emerging Creator":     "bg-yellow-50 text-yellow-700",
  "Daily":                "bg-indigo-50 text-indigo-700",
  "3-4/week":             "bg-indigo-50 text-indigo-700",
  "1-2/week":             "bg-indigo-50 text-indigo-700",
  "< a month":            "bg-gray-50 text-gray-600",
};

function TagPill({ label }: { label: string }) {
  const cls = TAG_PRESETS[label] ?? "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border border-transparent ${cls}`}>
      {label}
    </span>
  );
}

// ── Creator card ───────────────────────────────────────────────────────────────

function CreatorCard({
  creator,
  stats,
}: {
  creator: Creator;
  stats: CreatorStats | undefined;
}) {
  const [notes, setNotes] = useState(creator.overallNotes ?? "");
  const role = normalizeRole(creator.primaryRole);
  const colors = ROLE_COLORS[role];

  const tags = [
    creator.topVoiceStyle,
    creator.growthStage,
    creator.postingFrequency,
    creator.contentNiche,
  ].filter((t): t is string => !!t);

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col gap-4 p-5 hover:shadow-md transition-shadow">
      {/* Top row: avatar + name + badge */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${colors.avatar}`}
          >
            {initials(creator.name)}
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 text-sm leading-tight truncate">
              {creator.name}
            </p>
            {creator.firmAffiliation && (
              <p className="text-xs text-gray-400 truncate mt-0.5">{creator.firmAffiliation}</p>
            )}
          </div>
        </div>
        <span
          className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full border ${colors.badge}`}
        >
          {role === "Unknown" ? (creator.primaryRole ?? "—") : role}
        </span>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 divide-x divide-gray-100 text-center">
        <div className="pr-3">
          <p className="text-base font-bold text-gray-900 leading-tight">
            {fmtFollowers(creator.followerCount)}
          </p>
          <p className="text-[11px] text-gray-400 mt-0.5">Followers</p>
        </div>
        <div className="px-3">
          <p className="text-base font-bold text-emerald-500 leading-tight">
            {fmtEngRate(stats?.engagementRate ?? 0)}
          </p>
          <p className="text-[11px] text-gray-400 mt-0.5">Eng. rate</p>
        </div>
        <div className="pl-3">
          <p className="text-base font-bold text-gray-900 leading-tight">
            {fmtInfluence(stats?.avgEngagement ?? 0)}
          </p>
          <p className="text-[11px] text-gray-400 mt-0.5">Avg. eng.</p>
        </div>
      </div>

      {/* Tag pills */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tags.map((t) => (
            <TagPill key={t} label={t} />
          ))}
        </div>
      )}

      {/* Notes textarea */}
      <textarea
        className="w-full text-xs text-gray-500 bg-gray-50 border border-gray-100 rounded-lg px-3 py-2 resize-none focus:outline-none focus:ring-1 focus:ring-gray-300 placeholder:text-gray-300"
        rows={2}
        placeholder="Add notes…"
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
      />
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface CreatorsTabProps {
  creators: Creator[];
  statsMap: Record<string, CreatorStats>;
}

export default function CreatorsTab({ creators, statsMap }: CreatorsTabProps) {
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState<DisplayRole | "All">("All");

  const filtered = creators.filter((c) => {
    const matchesSearch =
      search.trim() === "" ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.firmAffiliation ?? "").toLowerCase().includes(search.toLowerCase());

    const matchesRole =
      roleFilter === "All" || normalizeRole(c.primaryRole) === roleFilter;

    return matchesSearch && matchesRole;
  });

  // Count per role for chip labels
  const roleCounts = creators.reduce<Record<string, number>>((acc, c) => {
    const r = normalizeRole(c.primaryRole);
    acc[r] = (acc[r] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex flex-col gap-5">
      {/* Search + filter row */}
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
            placeholder="Search creators…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 pr-4 py-2 text-sm rounded-full border border-gray-200 bg-white focus:outline-none focus:ring-2 focus:ring-gray-200 w-56 placeholder:text-gray-400"
          />
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {FILTER_CHIPS.map(({ label, role }) => {
            const count = role === "All" ? creators.length : (roleCounts[role] ?? 0);
            if (role !== "All" && count === 0) return null;
            const active = roleFilter === role;
            return (
              <button
                key={label}
                onClick={() => setRoleFilter(role)}
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
          <p className="text-gray-400 text-sm">No creators match your filters.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((creator) => (
            <CreatorCard
              key={creator.linkedinUrl ?? creator.name}
              creator={creator}
              stats={statsMap[creator.name]}
            />
          ))}
        </div>
      )}
    </div>
  );
}
