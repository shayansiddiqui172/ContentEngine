import type { DashboardStats, Creator } from "@/lib/types";

interface KPICardsProps {
  stats: DashboardStats;
  creators: Creator[];
}

function formatEngagement(rate: number): string {
  return (rate * 100).toFixed(2) + "%";
}

function roleBreakdown(creators: Creator[]): string {
  const counts: Record<string, number> = {};
  for (const c of creators) {
    const role = c.primaryRole ?? "Unknown";
    // Normalise display labels
    const label =
      role === "VC" || role === "VC / Investor" ? "VC"
      : role === "FOUNDER" || role === "Startup" ? "founder"
      : role === "OPERATOR" || role === "Ecosystem Partner" || role === "AI" ? "operator"
      : role.toLowerCase();
    counts[label] = (counts[label] ?? 0) + 1;
  }
  return Object.entries(counts)
    .map(([k, v]) => `${v} ${k}${v > 1 ? "s" : ""}`)
    .join(" · ");
}

export default function KPICards({ stats, creators }: KPICardsProps) {
  return (
    <div className="grid grid-cols-4 gap-4 px-6 py-4">
      {/* Creators tracked */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <p className="text-sm text-gray-500 font-medium mb-1">Creators tracked</p>
        <p className="text-4xl font-bold text-gray-900 mb-1">{stats.totalCreators}</p>
        <p className="text-xs text-gray-400">{roleBreakdown(creators)}</p>
      </div>

      {/* Posts analyzed */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <p className="text-sm text-gray-500 font-medium mb-1">Posts analyzed</p>
        <p className="text-4xl font-bold text-gray-900 mb-1">{stats.totalPosts}</p>
        <p className="text-xs text-gray-400">Last 30 days</p>
      </div>

      {/* Avg engagement */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <p className="text-sm text-gray-500 font-medium mb-1">Avg. engagement</p>
        <p className="text-4xl font-bold text-emerald-500 mb-1">
          {formatEngagement(stats.avgEngagementRate)}
        </p>
        <p className="text-xs text-gray-400">Normalized across all creators</p>
      </div>

      {/* Viral posts */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
        <p className="text-sm text-gray-500 font-medium mb-1">Viral posts</p>
        <p className="text-4xl font-bold text-orange-500 mb-1">{stats.viralPostCount}</p>
        <p className="text-xs text-gray-400">Above 2x creator average</p>
      </div>
    </div>
  );
}
