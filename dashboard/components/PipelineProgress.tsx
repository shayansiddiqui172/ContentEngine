const STEPS = [
  { label: "Creators", color: "#22c55e" },   // green
  { label: "Scrape",   color: "#818cf8" },   // indigo
  { label: "Ingest",   color: "#f87171" },   // red
  { label: "Gemini",   color: "#d97706" },   // amber
  { label: "Metrics",  color: "#60a5fa" },   // blue
  { label: "Dashboard",color: "#9f1239" },   // rose-dark
];

export default function PipelineProgress() {
  return (
    <div className="px-6 py-4 bg-[#F0EDE8]">
      <div className="flex items-center gap-1">
        {STEPS.map((step, i) => (
          <div key={step.label} className="flex items-center gap-1">
            <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-gray-200 shadow-sm text-sm font-medium text-gray-700">
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: step.color }}
              />
              {step.label}
            </div>
            {i < STEPS.length - 1 && (
              <span className="text-gray-400 text-xs px-0.5">→</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
