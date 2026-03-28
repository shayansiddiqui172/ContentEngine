"use client";

import { useState } from "react";
import type { Creator, Post } from "@/lib/types";

// ── Creator columns ────────────────────────────────────────────────────────────

const CREATOR_COLS: { label: string; key: keyof Creator; width?: string }[] = [
  { label: "Name",                 key: "name",                  width: "min-w-[140px]" },
  { label: "Followers",            key: "followerCount",          width: "min-w-[90px]" },
  { label: "Range",                key: "followerCountRange",     width: "min-w-[110px]" },
  { label: "Role",                 key: "primaryRole",            width: "min-w-[120px]" },
  { label: "Niche",                key: "contentNiche",           width: "min-w-[120px]" },
  { label: "Growth Stage",         key: "growthStage",            width: "min-w-[130px]" },
  { label: "Voice Style",          key: "topVoiceStyle",          width: "min-w-[120px]" },
  { label: "Posting Freq",         key: "postingFrequency",       width: "min-w-[110px]" },
  { label: "Credibility",          key: "credibility",            width: "min-w-[90px]" },
  { label: "Collab Potential",     key: "collaborationPotential", width: "min-w-[120px]" },
  { label: "Firm",                 key: "firmAffiliation",        width: "min-w-[120px]" },
  { label: "Location",             key: "location",               width: "min-w-[110px]" },
  { label: "Geography Focus",      key: "geographyFocus",         width: "min-w-[120px]" },
  { label: "Cross-Platform",       key: "crossPlatformCount",     width: "min-w-[100px]" },
  { label: "Connection",           key: "connectionStatus",       width: "min-w-[110px]" },
  { label: "Interacted",           key: "haveInteracted",         width: "min-w-[90px]" },
  { label: "DM'd",                 key: "haveDMed",               width: "min-w-[80px]" },
  { label: "Relationship Notes",   key: "relationshipNotes",      width: "min-w-[180px]" },
  { label: "Bio",                  key: "bio",                    width: "min-w-[220px]" },
  { label: "Notes",                key: "overallNotes",           width: "min-w-[180px]" },
  { label: "Date Added",           key: "dateAdded",              width: "min-w-[100px]" },
  { label: "LinkedIn URL",         key: "linkedinUrl",            width: "min-w-[180px]" },
];

// ── Post columns ───────────────────────────────────────────────────────────────

const POST_COLS: { label: string; key: keyof Post; width?: string }[] = [
  { label: "Creator",          key: "name",             width: "min-w-[130px]" },
  { label: "Date",             key: "postDate",          width: "min-w-[100px]" },
  { label: "Format",           key: "postFormat",        width: "min-w-[120px]" },
  { label: "Primary Topic",    key: "primaryTopic",      width: "min-w-[120px]" },
  { label: "Subject",          key: "topicSubject",      width: "min-w-[200px]" },
  { label: "Has Data",         key: "containsData",      width: "min-w-[80px]" },
  { label: "Relevance",        key: "relevance",         width: "min-w-[140px]" },
  { label: "Hook",             key: "hook",              width: "min-w-[220px]" },
  { label: "Hook Style",       key: "hookStyle",         width: "min-w-[120px]" },
  { label: "Hook Strength",    key: "hookStrength",      width: "min-w-[100px]" },
  { label: "Tone",             key: "tone",              width: "min-w-[110px]" },
  { label: "Has CTA",          key: "containsCTA",       width: "min-w-[80px]" },
  { label: "CTA Text",         key: "ctaText",           width: "min-w-[130px]" },
  { label: "Likes",            key: "likes",             width: "min-w-[70px]" },
  { label: "Comments",         key: "comments",          width: "min-w-[80px]" },
  { label: "Reposts",          key: "reposts",           width: "min-w-[80px]" },
  { label: "Shareability",     key: "shareability",      width: "min-w-[100px]" },
  { label: "Eng. Score",       key: "engagementScore",   width: "min-w-[90px]" },
  { label: "Performance",      key: "postPerformance",   width: "min-w-[170px]" },
  { label: "Topic Popularity", key: "topicPopularity",   width: "min-w-[130px]" },
  { label: "Post Frequency",   key: "postFrequency",     width: "min-w-[110px]" },
  { label: "Analysis",         key: "postWorkAnalysis",  width: "min-w-[240px]" },
  { label: "Post URL",         key: "postUrl",           width: "min-w-[180px]" },
];

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmtCell(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "boolean") return v ? "Y" : "N";
  if (typeof v === "number") return v.toLocaleString();
  return String(v);
}

function isUrl(v: unknown): boolean {
  if (typeof v !== "string") return false;
  return v.startsWith("http://") || v.startsWith("https://");
}

// ── Component ──────────────────────────────────────────────────────────────────

type Sheet = "creators" | "posts";

interface DataTabProps {
  creators: Creator[];
  posts: Post[];
}

export default function DataTab({ creators, posts }: DataTabProps) {
  const [sheet, setSheet] = useState<Sheet>("creators");

  return (
    <div className="flex flex-col gap-4">
      {/* Sheet switcher */}
      <div className="flex gap-2">
        <button
          onClick={() => setSheet("creators")}
          className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
            sheet === "creators"
              ? "bg-gray-900 text-white border-gray-900"
              : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
          }`}
        >
          DB1 — Creator Profiles
          <span className="ml-1.5 text-xs opacity-70">{creators.length}</span>
        </button>
        <button
          onClick={() => setSheet("posts")}
          className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors ${
            sheet === "posts"
              ? "bg-gray-900 text-white border-gray-900"
              : "bg-white text-gray-600 border-gray-200 hover:border-gray-400"
          }`}
        >
          DB2 — Post Analysis
          <span className="ml-1.5 text-xs opacity-70">{posts.length}</span>
        </button>
      </div>

      {/* Spreadsheet table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 shadow-sm">
        {sheet === "creators" ? (
          <table className="text-xs border-collapse w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="sticky left-0 z-10 bg-gray-50 px-3 py-2 text-left font-semibold text-gray-500 border-r border-gray-200 min-w-[28px] text-center">
                  #
                </th>
                {CREATOR_COLS.map((col) => (
                  <th
                    key={col.key}
                    className={`px-3 py-2 text-left font-semibold text-gray-500 whitespace-nowrap border-r border-gray-100 ${col.width ?? ""}`}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {creators.map((c, i) => (
                <tr
                  key={i}
                  className={`border-b border-gray-100 hover:bg-blue-50/40 transition-colors ${
                    i % 2 === 0 ? "bg-white" : "bg-gray-50/40"
                  }`}
                >
                  <td className="sticky left-0 z-10 px-3 py-1.5 text-center text-gray-400 border-r border-gray-200 bg-inherit">
                    {i + 1}
                  </td>
                  {CREATOR_COLS.map((col) => {
                    const val = c[col.key];
                    const text = fmtCell(val);
                    return (
                      <td
                        key={col.key}
                        className="px-3 py-1.5 text-gray-700 border-r border-gray-100 max-w-[300px] truncate"
                        title={text !== "—" ? text : undefined}
                      >
                        {isUrl(val) ? (
                          <a
                            href={val as string}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline truncate block"
                          >
                            {text}
                          </a>
                        ) : (
                          text
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <table className="text-xs border-collapse w-full">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="sticky left-0 z-10 bg-gray-50 px-3 py-2 text-left font-semibold text-gray-500 border-r border-gray-200 min-w-[28px] text-center">
                  #
                </th>
                {POST_COLS.map((col) => (
                  <th
                    key={col.key}
                    className={`px-3 py-2 text-left font-semibold text-gray-500 whitespace-nowrap border-r border-gray-100 ${col.width ?? ""}`}
                  >
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {posts.map((p, i) => (
                <tr
                  key={i}
                  className={`border-b border-gray-100 hover:bg-blue-50/40 transition-colors ${
                    i % 2 === 0 ? "bg-white" : "bg-gray-50/40"
                  }`}
                >
                  <td className="sticky left-0 z-10 px-3 py-1.5 text-center text-gray-400 border-r border-gray-200 bg-inherit">
                    {i + 1}
                  </td>
                  {POST_COLS.map((col) => {
                    const val = p[col.key];
                    const text = fmtCell(val);
                    return (
                      <td
                        key={col.key}
                        className="px-3 py-1.5 text-gray-700 border-r border-gray-100 max-w-[300px] truncate"
                        title={text !== "—" ? text : undefined}
                      >
                        {isUrl(val) ? (
                          <a
                            href={val as string}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:underline truncate block"
                          >
                            {text}
                          </a>
                        ) : (
                          text
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <p className="text-xs text-gray-400">
        {sheet === "creators"
          ? `${creators.length} creator${creators.length !== 1 ? "s" : ""} · hover a cell to see full text · scroll right for all columns`
          : `${posts.length} post${posts.length !== 1 ? "s" : ""} · hover a cell to see full text · scroll right for all columns`}
      </p>
    </div>
  );
}
