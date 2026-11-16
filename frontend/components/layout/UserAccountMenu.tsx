"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/components/layout/ThemeProvider";
import { MoonIcon, SunIcon } from "@/components/ui/Icons";

export function UserAccountMenu() {
  const { user, isAuthenticated, openAuthModal, logout, updateProfile } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);
  const [upgradedNotice, setUpgradedNotice] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false);
      }
    }
    if (menuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [menuOpen]);

  // Derive user initials (e.g. "KR" for "Krrish Raj" or "Krrish")
  const getInitials = (name: string) => {
    const parts = name.trim().split(" ");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  const handleUpgradeClick = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!user) {
      openAuthModal("signup");
      return;
    }
    if (user.plan === "free") {
      await updateProfile({ plan: "pro" });
      setUpgradedNotice(true);
      setTimeout(() => setUpgradedNotice(false), 2500);
    }
  };

  return (
    <div className="relative w-full" ref={menuRef}>
      {/* Popover Menu (ChatGPT style) */}
      {menuOpen && (
        <div className="absolute bottom-[calc(100%+8px)] left-0 w-full min-w-[240px] max-w-[280px] rounded-2xl border border-[var(--border-strong)] bg-[var(--bg-panel)] shadow-2xl p-2 z-50 animate-in fade-in slide-in-from-bottom-2 duration-150 text-[var(--text-primary)]">
          {/* User Header */}
          {user ? (
            <div className="px-3 py-2.5 border-b border-[var(--border-subtle)] mb-1">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-[#EA4335] via-[#FBBC05] to-[#8b5cf6] flex items-center justify-center text-white font-bold text-xs shadow-sm shrink-0">
                  {getInitials(user.name)}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold text-[var(--text-primary)] truncate">
                    {user.name}
                  </div>
                  <div className="text-[11px] text-[var(--text-muted)] truncate">
                    {user.email}
                  </div>
                </div>
              </div>
              <div className="mt-2 flex items-center justify-between text-[10px] font-mono-tech">
                <span className="text-[var(--text-muted)]">Current Plan</span>
                <span className="px-1.5 py-0.5 rounded bg-[var(--accent-soft)] text-[var(--accent)] font-semibold border border-[var(--accent-border)] uppercase tracking-wider">
                  {user.plan === "pro" ? "Pro Researcher" : "Free Tier"}
                </span>
              </div>
            </div>
          ) : (
            <div className="px-3 py-2 border-b border-[var(--border-subtle)] mb-1">
              <span className="text-xs text-[var(--text-secondary)]">Not logged in</span>
            </div>
          )}

          {/* Action Links */}
          <div className="space-y-0.5 text-xs font-medium">
            <Link
              href="/settings?tab=account"
              onClick={() => setMenuOpen(false)}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-colors"
            >
              <UserIcon className="w-4 h-4 text-[var(--text-muted)]" />
              <span>Account Settings</span>
            </Link>

            <Link
              href="/settings?tab=plan"
              onClick={() => setMenuOpen(false)}
              className="w-full flex items-center justify-between px-3 py-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-colors"
            >
              <div className="flex items-center gap-2.5">
                <SparklesIcon className="w-4 h-4 text-[var(--accent)]" />
                <span>My Plan & Upgrades</span>
              </div>
              {user?.plan === "pro" ? (
                <span className="text-[10px] font-mono-tech text-[var(--status-success)]">Active</span>
              ) : (
                <span className="text-[10px] font-mono-tech text-[var(--accent)] font-semibold">Pro $20</span>
              )}
            </Link>

            <Link
              href="/documents"
              onClick={() => setMenuOpen(false)}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-colors"
            >
              <FolderIcon className="w-4 h-4 text-[var(--text-muted)]" />
              <span>Knowledge Base Documents</span>
            </Link>

            <div className="my-1 border-t border-[var(--border-subtle)]" />

            {isAuthenticated ? (
              <button
                type="button"
                onClick={() => {
                  logout();
                  setMenuOpen(false);
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[var(--status-error)] hover:bg-[var(--status-error)]/10 transition-colors text-left cursor-pointer"
              >
                <LogOutIcon className="w-4 h-4" />
                <span>Log out</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  openAuthModal("login");
                }}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-[var(--accent)] hover:bg-[var(--accent-soft)] transition-colors text-left cursor-pointer font-semibold"
              >
                <LogInIcon className="w-4 h-4" />
                <span>Sign in or Register</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Main Account Trigger Row (ChatGPT Style) */}
      <div
        onClick={() => setMenuOpen(!menuOpen)}
        className="w-full flex items-center justify-between p-2 rounded-xl hover:bg-[var(--bg-surface)] border border-transparent hover:border-[var(--border-subtle)] transition-all cursor-pointer group select-none"
        title="Open user account menu"
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1 mr-2">
          {/* Avatar Circle with Initials (coral/gradient style from screenshot) */}
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#EA4335] to-[#FBBC05] flex items-center justify-center text-white font-bold text-xs shadow-sm shrink-0">
            {user ? getInitials(user.name) : "G"}
          </div>

          <div className="min-w-0 flex-1 leading-tight text-left">
            <div className="font-semibold text-xs text-[var(--text-primary)] group-hover:text-[var(--accent)] truncate">
              {user ? user.name : "Sign In"}
            </div>
            <div className="text-[11px] text-[var(--text-muted)] font-normal capitalize">
              {user?.plan === "pro" ? "Pro" : user ? "Free" : "Guest"}
            </div>
          </div>
        </div>

        {/* Upgrade Pill Button (Right side, identical to ChatGPT screenshot) */}
        <button
          type="button"
          onClick={handleUpgradeClick}
          className={`px-3 py-1 rounded-full text-[11px] font-semibold border transition-all cursor-pointer shrink-0 ${
            user?.plan === "pro"
              ? "bg-[var(--accent-soft)] text-[var(--accent)] border-[var(--accent-border)]"
              : "bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] text-[var(--text-primary)] border-[var(--border-strong)] hover:border-[var(--accent)] shadow-sm"
          }`}
          title={user?.plan === "pro" ? "Pro Plan Active" : "Upgrade to Pro"}
        >
          {upgradedNotice ? "Upgraded! ✓" : user?.plan === "pro" ? "Pro" : "Upgrade"}
        </button>
      </div>

      {/* Standalone Dark / Light Mode Toggle Button (Below User Account, Icon Only) */}
      <div className="mt-1 pt-1.5 border-t border-[var(--border-subtle)]/50 flex items-center justify-between px-1">
        <span className="text-[10px] font-mono-tech text-[var(--text-muted)] tracking-wider">
          THEME
        </span>
        <button
          type="button"
          onClick={toggleTheme}
          className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] border border-transparent hover:border-[var(--border-subtle)] transition-colors cursor-pointer"
          title={`Switch to ${theme === "dark" ? "Light" : "Dark"} mode`}
          aria-label="Toggle theme"
        >
          {theme === "dark" ? (
            <MoonIcon className="w-3.5 h-3.5" />
          ) : (
            <SunIcon className="w-3.5 h-3.5" />
          )}
        </button>
      </div>
    </div>
  );
}

function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2l2.4 7.2L22 12l-7.6 2.8L12 22l-2.4-7.2L2 12l7.6-2.8z" />
    </svg>
  );
}

function FolderIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
    </svg>
  );
}

function LogOutIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

function LogInIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
      <polyline points="10 17 15 12 10 7" />
      <line x1="15" y1="12" x2="3" y2="12" />
    </svg>
  );
}

