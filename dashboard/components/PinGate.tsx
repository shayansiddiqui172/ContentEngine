"use client";

import { useState, useEffect, useRef } from "react";

const CORRECT_PIN = "1145";
const STORAGE_KEY = "wc_unlocked";

export default function PinGate({ children }: { children: React.ReactNode }) {
  const [unlocked, setUnlocked] = useState(false);
  const [checked, setChecked]   = useState(false);
  const [pin, setPin]           = useState(["", "", "", ""]);
  const [error, setError]       = useState(false);
  const [shake, setShake]       = useState(false);
  const [success, setSuccess]   = useState(false);
  const inputs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (localStorage.getItem(STORAGE_KEY) === "true") setUnlocked(true);
    setChecked(true);
  }, []);

  function handleInput(i: number, val: string) {
    if (!/^\d?$/.test(val)) return;
    const next = [...pin];
    next[i] = val;
    setPin(next);
    setError(false);

    // Auto-advance
    if (val && i < 3) inputs.current[i + 1]?.focus();

    // Check when last digit entered
    if (val && next.every((d) => d !== "")) {
      if (next.join("") === CORRECT_PIN) {
        setSuccess(true);
        localStorage.setItem(STORAGE_KEY, "true");
        setTimeout(() => setUnlocked(true), 500);
      } else {
        setError(true);
        setShake(true);
        setTimeout(() => {
          setShake(false);
          setError(false);
          setPin(["", "", "", ""]);
          inputs.current[0]?.focus();
        }, 650);
      }
    }
  }

  function handleKeyDown(i: number, e: React.KeyboardEvent) {
    if (e.key === "Backspace" && !pin[i] && i > 0) {
      const next = [...pin];
      next[i - 1] = "";
      setPin(next);
      inputs.current[i - 1]?.focus();
    }
  }

  // Don't flash anything until localStorage is read
  if (!checked) return null;
  if (unlocked) return <>{children}</>;

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-[#0d0d1a]">

      {/* Gradient backdrop */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#0f0c29] via-[#1a1a2e] to-[#0d1f3c]" />

      {/* Ambient glow blobs */}
      <div className="absolute -top-48 -left-48 w-[500px] h-[500px] rounded-full bg-indigo-600/20 blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-48 -right-48 w-[500px] h-[500px] rounded-full bg-[#4EB8C8]/15 blur-[120px] pointer-events-none" />
      <div className="absolute top-1/3 left-1/3 w-72 h-72 rounded-full bg-violet-600/10 blur-[80px] pointer-events-none" />

      {/* Card */}
      <div className="relative z-10 flex flex-col items-center gap-7 bg-white/[0.04] backdrop-blur-2xl border border-white/10 rounded-2xl px-14 py-12 shadow-[0_32px_64px_rgba(0,0,0,0.5)]">

        {/* Logo */}
        <div className="flex flex-col items-center gap-1.5">
          <p className="text-[26px] font-bold tracking-tight leading-none">
            <span className="text-white">Wealth</span>
            <span className="text-[#4EB8C8]">Capital</span>
          </p>
          <p className="text-white/30 text-xs tracking-wide uppercase">Creator Intelligence</p>
        </div>

        {/* Lock icon */}
        <div
          className={`w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
            success
              ? "bg-emerald-500/20 ring-2 ring-emerald-400/40"
              : error
              ? "bg-red-500/20 ring-2 ring-red-400/30"
              : "bg-white/8 ring-1 ring-white/15"
          }`}
        >
          {success ? (
            <svg className="w-6 h-6 text-emerald-400" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
            </svg>
          ) : (
            <svg className="w-6 h-6 text-white/50" fill="none" stroke="currentColor" strokeWidth={1.5} viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
            </svg>
          )}
        </div>

        {/* Prompt */}
        <div className="flex flex-col items-center gap-1 -mt-1">
          <p className="text-white/80 text-sm font-medium">Enter your PIN</p>
          <p className="text-white/25 text-xs">Restricted to authorised team members</p>
        </div>

        {/* PIN boxes */}
        <div
          className="flex gap-3"
          style={{ animation: shake ? "shake 0.55s ease" : undefined }}
        >
          {pin.map((digit, i) => (
            <input
              key={i}
              ref={(el) => { inputs.current[i] = el; }}
              type="password"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              autoFocus={i === 0}
              onChange={(e) => handleInput(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              className={[
                "w-14 h-14 text-center text-2xl font-bold rounded-xl border-2 bg-transparent text-white outline-none transition-all duration-150 caret-transparent",
                success
                  ? "border-emerald-400/60 bg-emerald-500/10"
                  : error
                  ? "border-red-400/60 bg-red-500/10"
                  : digit
                  ? "border-[#4EB8C8]/70 bg-white/10"
                  : "border-white/15 hover:border-white/30 focus:border-white/50 bg-white/5",
              ].join(" ")}
            />
          ))}
        </div>

        {/* Error message */}
        <p
          className="text-red-400 text-xs -mt-3 h-4 transition-opacity duration-200"
          style={{ opacity: error ? 1 : 0 }}
        >
          Incorrect PIN — try again
        </p>

        {/* Divider + footer */}
        <div className="w-full border-t border-white/8 pt-4 text-center">
          <p className="text-white/15 text-[11px]">
            Contact your team lead if you need access
          </p>
        </div>
      </div>
    </div>
  );
}
