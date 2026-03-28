"use client";

import { useState, useRef, useEffect } from "react";

interface TopBarProps {
  lastRun: string;
  creatorCount: number;
  postCount: number;
}

type Mode = "csv" | "profile";

export default function TopBar({ lastRun, creatorCount, postCount }: TopBarProps) {
  const [showModal, setShowModal] = useState(false);
  const [mode, setMode] = useState<Mode>("csv");
  const [url, setUrl] = useState("");
  const [skipEnrich, setSkipEnrich] = useState(false);
  const [running, setRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [done, setDone] = useState(false);
  const [exitCode, setExitCode] = useState<number | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  function openModal() {
    setLogs([]);
    setDone(false);
    setExitCode(null);
    setRunning(false);
    setShowModal(true);
  }

  function closeModal() {
    if (running) return;
    setShowModal(false);
  }

  async function runPipeline() {
    if (mode === "profile" && !url.trim()) return;
    setLogs([]);
    setDone(false);
    setExitCode(null);
    setRunning(true);

    const res = await fetch("/api/pipeline/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode,
        url: url.trim(),
        skipEnrich,
      }),
    });

    if (!res.body) {
      setLogs(["Error: no response stream"]);
      setRunning(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done: streamDone } = await reader.read();
      if (streamDone) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.replace(/^data: /, "").trim();
        if (!line) continue;
        try {
          const msg = JSON.parse(line);
          if (msg.log) {
            setLogs((prev) => [...prev, msg.log]);
          }
          if (msg.done) {
            setDone(true);
            setExitCode(msg.code ?? 0);
            setRunning(false);
          }
          if (msg.error) {
            setLogs((prev) => [...prev, `ERROR: ${msg.error}`]);
            setRunning(false);
            setDone(true);
            setExitCode(1);
          }
        } catch {
          // ignore parse errors
        }
      }
    }
  }

  const succeeded = done && exitCode === 0;
  const failed = done && exitCode !== 0;

  return (
    <>
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
        <button
          onClick={openModal}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 transition-colors text-white text-sm font-semibold"
        >
          <svg className="w-3.5 h-3.5" viewBox="0 0 12 12" fill="currentColor">
            <path d="M2 1.5l8 4.5-8 4.5V1.5z" />
          </svg>
          Run pipeline
        </button>
      </header>

      {showModal && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl w-[560px] shadow-2xl flex flex-col max-h-[90vh]">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-base font-semibold text-gray-900">Run Pipeline</h2>
              {!running && (
                <button
                  onClick={closeModal}
                  className="text-gray-400 hover:text-gray-600 text-xl leading-none"
                >
                  ×
                </button>
              )}
            </div>

            {/* Body */}
            <div className="px-6 py-5 flex flex-col gap-4 overflow-y-auto">
              {/* Mode toggle */}
              <div className="flex rounded-lg overflow-hidden border border-gray-200 text-sm font-medium">
                <button
                  onClick={() => setMode("csv")}
                  disabled={running}
                  className={`flex-1 py-2 transition-colors ${
                    mode === "csv"
                      ? "bg-emerald-500 text-white"
                      : "bg-white text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  Import from PB CSVs
                </button>
                <button
                  onClick={() => setMode("profile")}
                  disabled={running}
                  className={`flex-1 py-2 transition-colors ${
                    mode === "profile"
                      ? "bg-emerald-500 text-white"
                      : "bg-white text-gray-600 hover:bg-gray-50"
                  }`}
                >
                  Scrape LinkedIn Profile
                </button>
              </div>

              {/* Mode description */}
              <p className="text-xs text-gray-500">
                {mode === "csv" ? (
                  <span>
                    <span className="font-semibold text-amber-600">⚠ PhantomBuster must already be scraped/run with your creators</span>
                    {" "}before using this option. Once it has finished, this reads /PB/profileres.csv and /PB/postres.csv and runs enrichment + display — no PhantomBuster trigger.
                  </span>
                ) : (
                  "Automatically launches PhantomBuster agents for the given LinkedIn URL, waits for completion, then enriches."
                )}
              </p>

              {/* URL input for profile mode */}
              {mode === "profile" && (
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={running}
                  placeholder="https://linkedin.com/in/username"
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-400 disabled:opacity-50"
                />
              )}

              {/* Skip enrich toggle */}
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={skipEnrich}
                  onChange={(e) => setSkipEnrich(e.target.checked)}
                  disabled={running}
                  className="rounded"
                />
                Skip Claude enrichment (faster, no AI analysis)
              </label>

              {/* Log output */}
              {logs.length > 0 && (
                <div
                  ref={logRef}
                  className="bg-[#111] text-[#d4d4d4] text-xs font-mono rounded-lg p-3 h-52 overflow-y-auto whitespace-pre-wrap"
                >
                  {logs.join("")}
                  {running && <span className="animate-pulse">▌</span>}
                </div>
              )}

              {/* Status banner */}
              {succeeded && (
                <div className="flex items-center gap-2 px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-700 text-sm font-medium">
                  <span>✓</span> Pipeline completed successfully. Refresh the page to see updated data.
                </div>
              )}
              {failed && (
                <div className="flex items-center gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm font-medium">
                  <span>✗</span> Pipeline exited with errors (code {exitCode}). Check logs above.
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-100">
              {!running && (
                <button
                  onClick={closeModal}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 transition-colors"
                >
                  {done ? "Close" : "Cancel"}
                </button>
              )}
              {!done && (
                <button
                  onClick={runPipeline}
                  disabled={running || (mode === "profile" && !url.trim())}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-white text-sm font-semibold"
                >
                  {running ? (
                    <>
                      <svg className="w-3.5 h-3.5 animate-spin" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="6" cy="6" r="4" strokeOpacity="0.3" />
                        <path d="M6 2a4 4 0 0 1 4 4" />
                      </svg>
                      Running…
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" viewBox="0 0 12 12" fill="currentColor">
                        <path d="M2 1.5l8 4.5-8 4.5V1.5z" />
                      </svg>
                      Run
                    </>
                  )}
                </button>
              )}
              {done && succeeded && (
                <button
                  onClick={() => window.location.reload()}
                  className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 transition-colors text-white text-sm font-semibold"
                >
                  Refresh dashboard
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
