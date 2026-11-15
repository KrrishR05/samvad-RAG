"use client";

import React from "react";

/**
 * ChatCanvasGrid
 *
 * Confined strictly to the central conversation canvas viewport.
 * Inspired by RAGFlow's technical grid background:
 *   - Thin 1px geometric grid (64px spacing) in muted forest-green (#29443B)
 *   - Soft atmospheric forest-green / deep teal lighting (#123C32, #173B32)
 *   - 4-point diamond sparkle stars with soft teal (#70B8A4) and pale lavender (#D8C9FF) glows
 *   - Vertical intersection light trace
 *   - Fully GPU-accelerated, zero JS state/re-render overhead, pointer-events: none
 */
export function ChatCanvasGrid() {
  return (
    <div
      className="absolute inset-0 pointer-events-none select-none overflow-hidden z-0"
      aria-hidden="true"
    >
      {/* 1. Base Obsidian Depth Canvas */}
      <div className="absolute inset-0 bg-[#0C1412]" />

      {/* 2. Atmospheric Depth & Horizon Glow */}
      <div
        className="absolute inset-0"
        style={{
          background:
            "radial-gradient(ellipse 70% 45% at 50% 100%, rgba(18, 60, 50, 0.45) 0%, rgba(23, 59, 50, 0.18) 45%, rgba(12, 20, 18, 0) 75%), " +
            "radial-gradient(ellipse 55% 30% at 50% 0%, rgba(23, 59, 50, 0.22) 0%, rgba(12, 20, 18, 0) 65%)",
        }}
      />

      {/* 3. Geometric 1px Technical Grid (64px x 64px) */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            "linear-gradient(to right, rgba(41, 68, 59, 0.32) 1px, transparent 1px), " +
            "linear-gradient(to bottom, rgba(41, 68, 59, 0.32) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          backgroundPosition: "center top",
          maskImage:
            "radial-gradient(ellipse 95% 90% at 50% 50%, #000 65%, rgba(0,0,0,0.4) 88%, transparent 100%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 95% 90% at 50% 50%, #000 65%, rgba(0,0,0,0.4) 88%, transparent 100%)",
        }}
      />

      {/* 4. Soft Illuminated Grid Intersections */}
      {/* Intersection Node 1 (Teal) */}
      <div
        className="absolute w-2 h-2 rounded-full -translate-x-1/2 -translate-y-1/2 samvad-intersection-pulse"
        style={{
          left: "22%",
          top: "38%",
          background: "#70B8A4",
          boxShadow: "0 0 10px 2px rgba(112, 184, 164, 0.55)",
          animationDelay: "0s",
        }}
      />

      {/* Intersection Node 2 (Teal) */}
      <div
        className="absolute w-2 h-2 rounded-full -translate-x-1/2 -translate-y-1/2 samvad-intersection-pulse"
        style={{
          left: "78%",
          top: "62%",
          background: "#70B8A4",
          boxShadow: "0 0 10px 2px rgba(112, 184, 164, 0.5)",
          animationDelay: "3s",
        }}
      />

      {/* Intersection Node 3 (Subtle Lavender) */}
      <div
        className="absolute w-1.5 h-1.5 rounded-full -translate-x-1/2 -translate-y-1/2 samvad-intersection-pulse"
        style={{
          left: "48%",
          top: "24%",
          background: "#D8C9FF",
          boxShadow: "0 0 8px 2px rgba(167, 139, 250, 0.45)",
          animationDelay: "6s",
        }}
      />

      {/* 5. Animated Diamond Particles (Floating 4-Point Sparkle Stars) */}

      {/* Diamond 1: Teal, Top-Left - Slow horizontal drift along grid line */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 samvad-diamond-anim-1"
        style={{ left: "14%", top: "20%" }}
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          className="drop-shadow-[0_0_7px_rgba(112,184,164,0.85)]"
        >
          <path
            d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z"
            fill="#70B8A4"
          />
          <circle cx="10" cy="10" r="1.5" fill="#FFFFFF" opacity="0.95" />
        </svg>
      </div>

      {/* Diamond 2: Teal with Vertical Beam Trace, Mid-Right (like RAGFlow hero) */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 samvad-diamond-anim-2"
        style={{ left: "84%", top: "42%" }}
      >
        {/* Faint vertical grid light trace */}
        <div
          className="absolute left-1/2 -top-8 w-[1px] h-20 -translate-x-1/2 pointer-events-none"
          style={{
            background:
              "linear-gradient(180deg, transparent 0%, rgba(112,184,164,0.6) 50%, transparent 100%)",
          }}
        />
        <svg
          width="22"
          height="22"
          viewBox="0 0 20 20"
          className="drop-shadow-[0_0_8px_rgba(112,184,164,0.9)]"
        >
          <path
            d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z"
            fill="#70B8A4"
          />
          <circle cx="10" cy="10" r="1.75" fill="#FFFFFF" opacity="0.95" />
        </svg>
      </div>

      {/* Diamond 3: Pale Lavender, Bottom-Left - Gentle floating drift */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 samvad-diamond-anim-3"
        style={{ left: "26%", top: "74%" }}
      >
        <svg
          width="18"
          height="18"
          viewBox="0 0 20 20"
          className="drop-shadow-[0_0_7px_rgba(167,139,250,0.8)]"
        >
          <path
            d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z"
            fill="#D8C9FF"
          />
          <circle cx="10" cy="10" r="1.5" fill="#FFFFFF" opacity="0.9" />
        </svg>
      </div>

      {/* Diamond 4: Subtle Teal, Bottom-Center - Ambient slow pulse */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 samvad-diamond-anim-4"
        style={{ left: "54%", top: "82%" }}
      >
        <svg
          width="17"
          height="17"
          viewBox="0 0 20 20"
          className="drop-shadow-[0_0_6px_rgba(112,184,164,0.7)]"
        >
          <path
            d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z"
            fill="#70B8A4"
          />
          <circle cx="10" cy="10" r="1.25" fill="#FFFFFF" opacity="0.9" />
        </svg>
      </div>

      {/* Diamond 5: Sage Teal, Top-Right - Slow diagonal drift */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 samvad-diamond-anim-5"
        style={{ left: "68%", top: "18%" }}
      >
        <svg
          width="19"
          height="19"
          viewBox="0 0 20 20"
          className="drop-shadow-[0_0_7px_rgba(112,184,164,0.8)]"
        >
          <path
            d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z"
            fill="#70B8A4"
          />
          <circle cx="10" cy="10" r="1.5" fill="#FFFFFF" opacity="0.9" />
        </svg>
      </div>

      {/* Diamond 6: Pale Lavender, Mid-Left - Very slow fade twinkle */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 samvad-diamond-anim-6"
        style={{ left: "36%", top: "52%" }}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 20 20"
          className="drop-shadow-[0_0_6px_rgba(167,139,250,0.7)]"
        >
          <path
            d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z"
            fill="#D8C9FF"
          />
          <circle cx="10" cy="10" r="1.25" fill="#FFFFFF" opacity="0.85" />
        </svg>
      </div>
    </div>
  );
}

