"use client";

import React from "react";

/**
 * ChatCanvasGrid
 *
 * Confined strictly to the central conversation canvas viewport.
 * Fully responsive to both Dark Mode and Light Mode:
 *   - Dark Mode: Obsidian depth (#0C1412) with forest-green & teal atmospheric glow and glowing diamond stars
 *   - Light Mode: Clean sage-tinted canvas (#F5F9F8) with subtle 1px engineering grid and elegant jewel diamond particles
 *   - Fully GPU-accelerated, zero JS state/re-render overhead, pointer-events: none
 */
export function ChatCanvasGrid() {
  return (
    <div
      className="absolute inset-0 pointer-events-none select-none overflow-hidden z-0"
      aria-hidden="true"
    >
      {/* 1. Base Canvas (Adaptive: #0C1412 in dark mode, #F5F9F8 in light mode) */}
      <div className="absolute inset-0 bg-[var(--bg-canvas)]" />

      {/* 2. Atmospheric Depth & Horizon Glow (Adaptive) */}
      <div className="absolute inset-0 samvad-canvas-glow" />

      {/* 3. Geometric 1px Technical Grid (Adaptive 64px x 64px) */}
      <div className="absolute inset-0 samvad-canvas-grid-lines" />

      {/* 4. Soft Illuminated Grid Intersections */}
      {/* Intersection Node 1 (Teal) */}
      <div
        className="absolute w-2 h-2 rounded-full -translate-x-1/2 -translate-y-1/2 samvad-intersection-pulse samvad-node-teal"
        style={{
          left: "22%",
          top: "38%",
          animationDelay: "0s",
        }}
      />

      {/* Intersection Node 2 (Teal) */}
      <div
        className="absolute w-2 h-2 rounded-full -translate-x-1/2 -translate-y-1/2 samvad-intersection-pulse samvad-node-teal"
        style={{
          left: "78%",
          top: "62%",
          animationDelay: "3s",
        }}
      />

      {/* Intersection Node 3 (Subtle Lavender) */}
      <div
        className="absolute w-1.5 h-1.5 rounded-full -translate-x-1/2 -translate-y-1/2 samvad-intersection-pulse samvad-node-lavender"
        style={{
          left: "48%",
          top: "24%",
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
          className="samvad-diamond-teal"
        >
          <path d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z" />
          <circle cx="10" cy="10" r="1.5" fill="#FFFFFF" opacity="0.95" />
        </svg>
      </div>

      {/* Diamond 2: Teal with Vertical Beam Trace, Mid-Right */}
      <div
        className="absolute -translate-x-1/2 -translate-y-1/2 samvad-diamond-anim-2"
        style={{ left: "84%", top: "42%" }}
      >
        {/* Vertical grid light trace */}
        <div className="absolute left-1/2 -top-8 w-[1px] h-20 -translate-x-1/2 pointer-events-none samvad-vertical-beam" />
        <svg
          width="22"
          height="22"
          viewBox="0 0 20 20"
          className="samvad-diamond-teal"
        >
          <path d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z" />
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
          className="samvad-diamond-lavender"
        >
          <path d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z" />
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
          className="samvad-diamond-teal"
        >
          <path d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z" />
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
          className="samvad-diamond-teal"
        >
          <path d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z" />
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
          className="samvad-diamond-lavender"
        >
          <path d="M 10 0 Q 10 10 0 10 Q 10 10 10 20 Q 10 10 20 10 Q 10 10 10 0 Z" />
          <circle cx="10" cy="10" r="1.25" fill="#FFFFFF" opacity="0.85" />
        </svg>
      </div>
    </div>
  );
}
