import { getCreators, getPosts, getStats, getCreatorStatsMap, getCreatorFollowerMap } from "@/lib/data";
import TopBar from "@/components/TopBar";
import PipelineProgress from "@/components/PipelineProgress";
import KPICards from "@/components/KPICards";
import TabNav from "@/components/TabNav";

function formatLastRun(creators: Awaited<ReturnType<typeof getCreators>>): string {
  const dates = creators
    .map((c) => c.dateAdded)
    .filter((d): d is string => d !== null)
    .map((d) => new Date(d))
    .filter((d) => !isNaN(d.getTime()));

  if (dates.length === 0) return "—";

  const latest = new Date(Math.max(...dates.map((d) => d.getTime())));
  return latest.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function Home() {
  const creators = getCreators();
  const posts = getPosts();
  const stats = getStats();
  const creatorStatsMap = getCreatorStatsMap();
  const followerMap = getCreatorFollowerMap();
  const lastRun = formatLastRun(creators);

  return (
    <div className="flex flex-col min-h-screen">
      <TopBar
        lastRun={lastRun}
        creatorCount={stats.totalCreators}
        postCount={stats.totalPosts}
      />
      <PipelineProgress />
      <main className="flex-1 pb-10">
        <KPICards stats={stats} creators={creators} />
        <TabNav
          creators={creators}
          posts={posts}
          stats={stats}
          creatorStatsMap={creatorStatsMap}
          followerMap={followerMap}
        />
      </main>
    </div>
  );
}
