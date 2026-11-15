"use client";

import React from "react";

/**
 * ChatCanvasGrid
 *
 * Confined strictly to the central conversation canvas viewport.
 * Features:
 *   - Clean, professional technical geometric grid (64px x 64px)
 *   - Atmospheric forest green & emerald depth glow
 *   - Ambient breathing effect: grid smoothly and simultaneously dims
 *     and returns to normal visibility
 *   - Zero particles / zero floating diamonds (clean minimal aesthetic)
 *   - Pure GPU-accelerated opacity animation, zero JS overhead
 */
export function ChatCanvasGrid() {
  return (
    <div
      className="absolute inset-0 pointer-events-none select-none overflow-hidden z-0"
      aria-hidden="true"
    >
      {/* 1. Base Canvas (Adaptive: #0C1412 in dark mode, #F5F9F8 in light mode) */}
      <div className="absolute inset-0 bg-[var(--bg-canvas)]" />

      {/* 2. Atmospheric Depth & Horizon Glow */}
      <div className="absolute inset-0 samvad-canvas-glow" />

      {/* 3. Geometric 1px Technical Grid with Ambient Breathing Animation */}
      <div className="absolute inset-0 samvad-canvas-grid-lines samvad-grid-breathing" />
    </div>
  );
}
