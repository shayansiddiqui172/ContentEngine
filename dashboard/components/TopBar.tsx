"use client";

interface TopBarProps {
  lastRun: string;
  creatorCount: number;
  postCount: number;
}

export default function TopBar({ lastRun, creatorCount, postCount }: TopBarProps) {
  return (
    <header className="flex items-center justify-between px-6 py-3 bg-[#1a1a2e] shrink-0">
      {/* Logo */}
      <div className="flex items-center gap-0.5 text-[17px] font-bold tracking-tight">
        <span className="text-white">Wealth</span>
        <span className="text-[#4EB8C8]">Capital</span>
      </div>

      {/* Status pill */}
      <div className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/10 text-white/80 text-sm font-medium">
        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
        Last run: {lastRun} — {creatorCount} creators · {postCount} posts
      </div>

      {/* Run pipeline button */}
      <button className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 transition-colors text-white text-sm font-semibold">
        <svg className="w-3.5 h-3.5" viewBox="0 0 12 12" fill="currentColor">
          <path d="M2 1.5l8 4.5-8 4.5V1.5z" />
        </svg>
        Run pipeline
      </button>
    </header>
  );
}
