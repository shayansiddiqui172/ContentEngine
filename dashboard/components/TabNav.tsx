"use client";

import { useState } from "react";
import type { Creator, Post, DashboardStats, CreatorStats } from "@/lib/types";
// DashboardStats kept for KPI cards passed from page.tsx
import CreatorsTab from "./CreatorsTab";
import PostsTab from "./PostsTab";
import AnalyticsTab from "./AnalyticsTab";
import InsightsTab from "./InsightsTab";

const TABS = ["Creators", "Posts", "Analytics", "Insights"] as const;
type Tab = (typeof TABS)[number];

interface TabNavProps {
  creators: Creator[];
  posts: Post[];
  stats: DashboardStats;
  creatorStatsMap: Record<string, CreatorStats>;
  followerMap: Record<string, number>;
}

export default function TabNav({ creators, posts, stats, creatorStatsMap, followerMap }: TabNavProps) {
  const [active, setActive] = useState<Tab>("Creators");

  return (
    <div className="px-6">
      {/* Tab strip */}
      <div className="flex gap-0 border-b border-gray-200 mb-6">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={[
              "px-4 py-2.5 text-sm font-medium transition-colors relative",
              active === tab
                ? "text-gray-900 after:absolute after:bottom-0 after:left-0 after:right-0 after:h-0.5 after:bg-gray-900"
                : "text-gray-400 hover:text-gray-600",
            ].join(" ")}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {active === "Creators" && (
        <CreatorsTab creators={creators} statsMap={creatorStatsMap} />
      )}
      {active === "Posts" && <PostsTab posts={posts} followerMap={followerMap} />}
      {active === "Analytics" && <AnalyticsTab posts={posts} followerMap={followerMap} />}
      {active === "Insights" && <InsightsTab posts={posts} creators={creators} />}
    </div>
  );
}



