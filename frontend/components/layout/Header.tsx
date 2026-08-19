"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { healthCheck } from "@/lib/api/client";

const NAV_LINKS = [
  { href: "/", label: "Query" },
  { href: "/analytics", label: "Analytics" },
  { href: "/architecture", label: "Architecture" },
];

export default function Header() {
  const pathname = usePathname();
  const [systemStatus, setSystemStatus] = useState<
    "checking" | "online" | "offline"
  >("checking");

  useEffect(() => {
    healthCheck()
      .then(() => setSystemStatus("online"))
      .catch(() => setSystemStatus("offline"));
  }, []);

  return (
    <header className="border-b border-border-subtle bg-bg-secondary/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="w-8 h-8 rounded-lg bg-accent/10 border border-accent/20 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-accent"
              >
                <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" x2="12" y1="19" y2="22" />
              </svg>
            </div>
            <div>
              <span className="text-sm font-semibold tracking-wider text-text-primary">
                SAMVAD
              </span>
              <span className="hidden sm:block text-[10px] text-text-muted tracking-wide">
                Speak. Retrieve. Ground.
              </span>
            </div>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-1 ml-4">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  pathname === link.href
                    ? "text-accent bg-accent-soft"
                    : "text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>

        {/* System Status */}
        <div className="flex items-center gap-2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${
              systemStatus === "online"
                ? "bg-success"
                : systemStatus === "offline"
                ? "bg-error"
                : "bg-warning animate-pulse"
            }`}
          />
          <span className="text-[10px] font-mono text-text-muted uppercase tracking-widest">
            {systemStatus === "online"
              ? "System Online"
              : systemStatus === "offline"
              ? "Backend Offline"
              : "Checking..."}
          </span>
        </div>
      </div>
    </header>
  );
}
