"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getPipelineStatus, healthCheck } from "@/lib/api/client";
import type { PipelineStatusResponse } from "@/types/api";
import { useTheme } from "@/components/layout/ThemeProvider";
import {
  AnalyticsIcon,
  DocumentsIcon,
  MoonIcon,
  PipelineIcon,
  PlusIcon,
  SamvadLogo,
  SettingsIcon,
  SidebarToggleIcon,
  SunIcon,
  TrashIcon,
  WorkspaceIcon,
} from "@/components/ui/Icons";

export interface SidebarSessionItem {
  id: string;
  title: string;
  updatedAt: string;
  messageCount: number;
}

interface AppShellProps {
  children: React.ReactNode;
  pageTitle?: string;
  headerActions?: React.ReactNode;
  sessions?: SidebarSessionItem[];
  activeSessionId?: string | null;
  onNewSession?: () => void;
  onSelectSession?: (id: string) => void;
  onDeleteSession?: (id: string) => void;
  pipelineStatus?: PipelineStatusResponse | null;
}

export function AppShell({
  children,
  pageTitle,
  headerActions,
  sessions,
  activeSessionId,
  onNewSession,
  onSelectSession,
  onDeleteSession,
  pipelineStatus: externalStatus,
}: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [fetchedStatus, setFetchedStatus] =
    useState<PipelineStatusResponse | null>(null);

  const status =
    externalStatus !== undefined ? externalStatus : fetchedStatus;

  useEffect(() => {
    if (externalStatus !== undefined) {
      return;
    }
    let mounted = true;
    Promise.allSettled([healthCheck(), getPipelineStatus()]).then(
      ([healthRes, pipeRes]) => {
        if (!mounted) return;
        setBackendOnline(
          healthRes.status === "fulfilled" && healthRes.value.status === "healthy"
        );
        if (pipeRes.status === "fulfilled") {
          setFetchedStatus(pipeRes.value);
        }
      }
    );
    return () => {
      mounted = false;
    };
  }, [externalStatus, pathname]);

  // Also check /health once even if externalStatus was passed
  useEffect(() => {
    if (externalStatus === undefined) return;
    let mounted = true;
    healthCheck()
      .then((res) => {
        if (mounted) setBackendOnline(res.status === "healthy");
      })
      .catch(() => {
        if (mounted) setBackendOnline(false);
      });
    return () => {
      mounted = false;
    };
  }, [externalStatus]);

  const navItems = [
    { href: "/", label: "Workspace", icon: WorkspaceIcon },
    {
      href: "/documents",
      label: "Knowledge Base",
      icon: DocumentsIcon,
      badge: status ? `${status.indexed_documents}` : undefined,
    },
    { href: "/architecture", label: "Pipeline Explorer", icon: PipelineIcon },
    { href: "/analytics", label: "Analytics", icon: AnalyticsIcon },
    { href: "/settings", label: "Settings", icon: SettingsIcon },
  ];

  const handleNewChat = () => {
    if (onNewSession) {
      onNewSession();
    } else {
      router.push("/");
    }
    setMobileOpen(false);
  };

  const renderSidebarBody = () => (
    <div className="flex flex-col h-full bg-[var(--bg-panel)] border-r border-[var(--border-subtle)] select-none">
      {/* Brand header */}
      <div className="h-14 px-4 flex items-center justify-between border-b border-[var(--border-subtle)]">
        <Link
          href="/"
          className="flex items-center gap-2.5 group focus:outline-none"
        >
          <SamvadLogo className="w-8 h-8 shrink-0" />
          <div className="leading-none">
            <div className="flex items-center gap-1.5">
              <span className="font-display font-bold text-sm tracking-tight text-[var(--text-primary)] block">
                SAMVAD
              </span>
              <span className="text-[11px] font-sans text-[var(--accent)] font-medium">
                | संवाद
              </span>
            </div>
            <div className="text-[7.5px] font-mono-tech tracking-wider uppercase mt-1 flex items-center gap-1">
              <span className="text-[var(--text-secondary)] font-semibold">INTELLIGENCE</span>
              <span className="text-[var(--accent)] font-bold">THROUGH</span>
              <span className="text-[var(--brand-mint)] font-semibold">EVIDENCE</span>
            </div>
          </div>
        </Link>
        <button
          type="button"
          onClick={() => {
            setSidebarOpen(false);
            setMobileOpen(false);
          }}
          title="Collapse sidebar"
          className="p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
        >
          <SidebarToggleIcon className="w-4 h-4" />
        </button>
      </div>

      {/* Primary Action */}
      <div className="p-3">
        <button
          type="button"
          onClick={handleNewChat}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs font-semibold bg-[var(--accent)] text-[#0C1412] hover:bg-[var(--accent-hover)] transition-all cursor-pointer shadow-xs active:scale-[0.99]"
        >
          <PlusIcon className="w-3.5 h-3.5" />
          <span>New Research Session</span>
        </button>
      </div>

      {/* Navigation */}
      <nav className="px-2.5 space-y-0.5" aria-label="Main navigation">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center justify-between px-2.5 py-2 rounded-md text-[13px] transition-colors ${
                isActive
                  ? "bg-[var(--accent-soft)] text-[var(--text-primary)] font-medium border border-[var(--accent-border)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-transparent"
              }`}
            >
              <span className="flex items-center gap-2.5">
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? "text-[var(--accent)]" : "text-[var(--text-muted)]"
                  }`}
                />
                <span>{item.label}</span>
              </span>
              {item.badge !== undefined && (
                <span className="font-mono-tech text-[11px] px-1.5 py-0.5 rounded bg-[var(--bg-surface)] text-[var(--text-muted)] border border-[var(--border-subtle)]">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Local Session History */}
      <div className="mt-5 flex-1 min-h-0 flex flex-col px-2.5">
        {sessions && sessions.length > 0 && (
          <>
            <div className="px-2.5 pb-1.5 flex items-center justify-between">
              <span className="text-[10px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                Recent Sessions
              </span>
              <span className="text-[10px] font-mono-tech text-[var(--text-muted)]">
                local
              </span>
            </div>
            <div className="flex-1 overflow-y-auto space-y-0.5 pr-1">
              {sessions.map((s) => {
                const selected = s.id === activeSessionId;
                return (
                  <div
                    key={s.id}
                    className={`group flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs transition-colors ${
                      selected
                        ? "bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)]"
                        : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] border border-transparent"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => {
                        onSelectSession?.(s.id);
                        setMobileOpen(false);
                      }}
                      className="flex-1 text-left truncate cursor-pointer"
                      title={s.title}
                    >
                      {s.title}
                    </button>
                    {onDeleteSession && (
                      <button
                        type="button"
                        onClick={() => onDeleteSession(s.id)}
                        title="Delete session"
                        className="opacity-0 group-hover:opacity-100 p-1 rounded text-[var(--text-muted)] hover:text-[var(--status-error)] transition-opacity cursor-pointer"
                      >
                        <TrashIcon className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>

      {/* Live Capability Footer + Theme Toggle */}
      <div className="p-3 border-t border-[var(--border-subtle)] space-y-2.5">
        <div className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] px-2.5 py-2 space-y-1">
          <div className="flex items-center justify-between text-[11px]">
            <span className="flex items-center gap-1.5 text-[var(--text-secondary)]">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  backendOnline === null
                    ? "bg-[var(--text-muted)]"
                    : backendOnline
                    ? "bg-[var(--status-success)]"
                    : "bg-[var(--status-error)]"
                }`}
              />
              <span>
                {backendOnline === null
                  ? "Checking API..."
                  : backendOnline
                  ? "API Connected"
                  : "API Offline"}
              </span>
            </span>
            {status && (
              <span className="font-mono-tech text-[10px] text-[var(--text-muted)]">
                {status.indexed_chunks} chks
              </span>
            )}
          </div>
          {status && (
            <div className="flex items-center justify-between text-[10px] font-mono-tech">
              <span
                className={
                  status.llm_configured
                    ? "text-[var(--status-success)]"
                    : "text-[var(--status-warning)]"
                }
              >
                {status.llm_configured
                  ? `${status.llm_provider || "llm"}:${status.llm_model}`
                  : "LLM unconfigured"}
              </span>
              <span className="text-[var(--text-muted)]">
                {status.embedding_dimension}d
              </span>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={toggleTheme}
          className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] transition-colors cursor-pointer"
        >
          <span>{theme === "dark" ? "Dark Mode" : "Light Mode"}</span>
          {theme === "dark" ? (
            <MoonIcon className="w-3.5 h-3.5" />
          ) : (
            <SunIcon className="w-3.5 h-3.5" />
          )}
        </button>
      </div>
    </div>
  );

  return (
    <div className="h-screen w-full flex overflow-hidden bg-[var(--bg-canvas)] text-[var(--text-primary)]">
      {/* Desktop Sidebar */}
      {sidebarOpen && (
        <aside className="hidden md:block w-[260px] shrink-0 h-full">
          {renderSidebarBody()}
        </aside>
      )}

      {/* Mobile Drawer Overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div className="w-[270px] h-full shadow-2xl">{renderSidebarBody()}</div>
          <div
            className="flex-1 bg-black/50"
            onClick={() => setMobileOpen(false)}
          />
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 min-w-0 flex flex-col h-full">
        {/* Top Utility Strip */}
        <header className="h-14 shrink-0 px-4 border-b border-[var(--border-subtle)] bg-[var(--bg-canvas)]/90 backdrop-blur-sm flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            <button
              type="button"
              onClick={() => {
                if (window.innerWidth < 768) {
                  setMobileOpen(true);
                } else {
                  setSidebarOpen((prev) => !prev);
                }
              }}
              title="Toggle navigation sidebar"
              className={`p-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors cursor-pointer ${
                sidebarOpen ? "md:hidden" : ""
              }`}
            >
              <SidebarToggleIcon className="w-4 h-4" />
            </button>
            {!sidebarOpen && (
              <Link href="/" className="hidden md:flex items-center gap-1.5 mr-1 group">
                <SamvadLogo className="w-5 h-5 shrink-0" />
                <span className="font-display font-bold text-xs tracking-tight text-[var(--text-primary)]">
                  SAMVAD
                </span>
                <span className="text-[10px] text-[var(--text-muted)]">
                  | संवाद
                </span>
              </Link>
            )}
            <h1 className="font-display font-medium text-sm text-[var(--text-primary)] truncate">
              {pageTitle || "Research Workspace"}
            </h1>
          </div>

          <div className="flex items-center gap-2">{headerActions}</div>
        </header>

        {/* Body */}
        <div className="flex-1 min-h-0 flex overflow-hidden">{children}</div>
      </div>
    </div>
  );
}
