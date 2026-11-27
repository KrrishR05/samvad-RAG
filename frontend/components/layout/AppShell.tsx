"use client";

import React, { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { getPipelineStatus, healthCheck } from "@/lib/api/client";
import type { PipelineStatusResponse } from "@/types/api";
import { useTheme } from "@/components/layout/ThemeProvider";
import { UserAccountMenu } from "@/components/layout/UserAccountMenu";
import { AuthModal } from "@/components/auth/AuthModal";
import { useAuth } from "@/context/AuthContext";
import { useKnowledgeBase } from "@/context/KnowledgeBaseContext";
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
  pinned?: boolean;
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
  onTogglePinSession?: (id: string) => void;
  onRenameSession?: (id: string, newTitle: string) => void;
  onShareSession?: (id: string) => Promise<boolean> | boolean | void;
  pipelineStatus?: PipelineStatusResponse | null;
}

function PinIcon({ className = "w-3.5 h-3.5", filled = false }: { className?: string; filled?: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M12 17v5" />
      <path d="M9 10.76a2 2 0 0 1-1.11 1.79l-1.78.9A2 2 0 0 0 5 15.24V16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-.76a2 2 0 0 0-1.11-1.79l-1.78-.9A2 2 0 0 1 15 10.76V7a1 1 0 0 1 1-1 2 2 0 0 0 0-4H8a2 2 0 0 0 0 4 1 1 0 0 1 1 1z" />
    </svg>
  );
}

function MoreDotsIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
      <circle cx="5" cy="12" r="1.75" />
      <circle cx="12" cy="12" r="1.75" />
      <circle cx="19" cy="12" r="1.75" />
    </svg>
  );
}

function PencilIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}

function ShareIcon({ className = "w-3.5 h-3.5" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8" />
      <polyline points="16 6 12 2 8 6" />
      <line x1="12" y1="2" x2="12" y2="15" />
    </svg>
  );
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
  onTogglePinSession,
  onRenameSession,
  onShareSession,
  pipelineStatus: externalStatus,
}: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { theme, toggleTheme } = useTheme();
  const { user, openAuthModal } = useAuth();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(true);
  const [pinnedCollapsed, setPinnedCollapsed] = useState(false);
  const [menuSessionId, setMenuSessionId] = useState<string | null>(null);
  const [menuPos, setMenuPos] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [renameDraft, setRenameDraft] = useState("");
  const [shareToast, setShareToast] = useState<string | null>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!menuSessionId) return;
    const handleOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuSessionId(null);
      }
    };
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuSessionId(null);
    };
    document.addEventListener("mousedown", handleOutside);
    document.addEventListener("keydown", handleEsc);
    return () => {
      document.removeEventListener("mousedown", handleOutside);
      document.removeEventListener("keydown", handleEsc);
    };
  }, [menuSessionId]);

  const { totalDocuments, pipelineStatus: kbPipelineStatus } =
    useKnowledgeBase();

  const status = externalStatus ?? kbPipelineStatus;

  // Single health check on mount
  useEffect(() => {
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
  }, []);

  const navItems = [
    { href: "/", label: "Workspace", icon: WorkspaceIcon },
    {
      href: "/documents",
      label: "Knowledge Base",
      icon: DocumentsIcon,
      badge: totalDocuments > 0 ? `${totalDocuments}` : undefined,
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

      {/* Local Session History (Pinned + Recent Sessions) */}
      <div className="mt-5 flex-1 min-h-0 flex flex-col px-2.5 overflow-hidden">
        {sessions && sessions.length > 0 && (() => {
          const pinnedSessions = sessions.filter((s) => s.pinned);
          const recentSessions = sessions.filter((s) => !s.pinned);

          const renderSessionRow = (s: SidebarSessionItem) => {
            const selected = s.id === activeSessionId;
            const menuOpen = menuSessionId === s.id;
            const isRenaming = renamingId === s.id;

            return (
              <div
                key={s.id}
                className={`group relative flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs transition-colors ${
                  selected || menuOpen
                    ? "bg-[var(--bg-surface)] text-[var(--text-primary)] border border-[var(--border-subtle)]"
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] border border-transparent"
                }`}
              >
                {isRenaming ? (
                  <input
                    type="text"
                    autoFocus
                    value={renameDraft}
                    onChange={(e) => setRenameDraft(e.target.value)}
                    onBlur={() => {
                      const trimmed = renameDraft.trim();
                      if (trimmed && trimmed !== s.title) {
                        onRenameSession?.(s.id, trimmed);
                      }
                      setRenamingId(null);
                    }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") {
                        const trimmed = renameDraft.trim();
                        if (trimmed && trimmed !== s.title) {
                          onRenameSession?.(s.id, trimmed);
                        }
                        setRenamingId(null);
                      } else if (e.key === "Escape") {
                        setRenamingId(null);
                      }
                    }}
                    className="flex-1 min-w-0 bg-[var(--bg-canvas)] text-[var(--text-primary)] px-1.5 py-0.5 rounded border border-[var(--accent-border)] text-xs focus:outline-none"
                  />
                ) : (
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
                )}

                {!isRenaming && (
                  <div className="flex items-center gap-0.5 shrink-0">
                    {onTogglePinSession && (
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onTogglePinSession(s.id);
                        }}
                        title={s.pinned ? "Unpin chat" : "Pin chat"}
                        className={`p-1 rounded transition-opacity cursor-pointer ${
                          s.pinned
                            ? "opacity-90 text-[var(--accent)] hover:opacity-100"
                            : menuOpen
                            ? "opacity-100 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                            : "opacity-0 group-hover:opacity-100 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                        }`}
                      >
                        <PinIcon className="w-3 h-3" filled={Boolean(s.pinned)} />
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (menuOpen) {
                          setMenuSessionId(null);
                          return;
                        }
                        const rect = e.currentTarget.getBoundingClientRect();
                        const top = Math.min(rect.bottom + 4, window.innerHeight - 190);
                        const left = Math.min(rect.left, window.innerWidth - 185);
                        setMenuPos({ top, left });
                        setMenuSessionId(s.id);
                      }}
                      title="Session options"
                      className={`p-1 rounded transition-opacity cursor-pointer ${
                        menuOpen
                          ? "opacity-100 text-[var(--text-primary)] bg-[var(--bg-hover)]"
                          : "opacity-0 group-hover:opacity-100 text-[var(--text-muted)] hover:text-[var(--text-primary)]"
                      }`}
                    >
                      <MoreDotsIcon className="w-3.5 h-3.5" />
                    </button>
                  </div>
                )}
              </div>
            );
          };

          const activeMenuSession = sessions.find((s) => s.id === menuSessionId) ?? null;

          return (
            <div className="flex-1 overflow-y-auto space-y-4 pr-1">
              {pinnedSessions.length > 0 && (
                <div>
                  <button
                    type="button"
                    onClick={() => setPinnedCollapsed((p) => !p)}
                    className="w-full px-2.5 pb-1.5 flex items-center gap-1 text-[10px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)] hover:text-[var(--text-secondary)] cursor-pointer"
                  >
                    <span>Pinned</span>
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className={`w-3 h-3 transition-transform ${pinnedCollapsed ? "-rotate-90" : ""}`}
                    >
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </button>
                  {!pinnedCollapsed && (
                    <div className="space-y-0.5">{pinnedSessions.map(renderSessionRow)}</div>
                  )}
                </div>
              )}

              <div>
                <div className="px-2.5 pb-1.5 flex items-center justify-between">
                  <span className="text-[10px] font-mono-tech uppercase tracking-wider text-[var(--text-muted)]">
                    Recent Sessions
                  </span>
                  <span className="text-[10px] font-mono-tech text-[var(--text-muted)]">
                    local
                  </span>
                </div>
                <div className="space-y-0.5">
                  {recentSessions.length > 0 ? (
                    recentSessions.map(renderSessionRow)
                  ) : (
                    <p className="px-2.5 py-1 text-[11px] text-[var(--text-muted)]">
                      All sessions pinned above
                    </p>
                  )}
                </div>
              </div>

              {/* Floating Session Action Menu (ChatGPT-style) */}
              {activeMenuSession && (
                <div
                  ref={menuRef}
                  style={{ top: menuPos.top, left: menuPos.left }}
                  className="fixed z-50 w-44 rounded-xl border border-[var(--border-strong)] bg-[var(--bg-panel)] shadow-2xl p-1.5 text-xs text-[var(--text-primary)]"
                >
                  {onTogglePinSession && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onTogglePinSession(activeMenuSession.id);
                        setMenuSessionId(null);
                      }}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors cursor-pointer text-left"
                    >
                      <PinIcon className="w-3.5 h-3.5 text-[var(--text-secondary)]" filled={Boolean(activeMenuSession.pinned)} />
                      <span>{activeMenuSession.pinned ? "Unpin" : "Pin"}</span>
                    </button>
                  )}

                  {onRenameSession && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setRenamingId(activeMenuSession.id);
                        setRenameDraft(activeMenuSession.title);
                        setMenuSessionId(null);
                      }}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors cursor-pointer text-left"
                    >
                      <PencilIcon className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
                      <span>Rename</span>
                    </button>
                  )}

                  {onShareSession && (
                    <button
                      type="button"
                      onClick={async (e) => {
                        e.stopPropagation();
                        const sid = activeMenuSession.id;
                        setMenuSessionId(null);
                        const ok = await onShareSession(sid);
                        setShareToast(
                          ok !== false ? "Share link copied!" : "Failed to create share link"
                        );
                        setTimeout(() => setShareToast(null), 2400);
                      }}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-[var(--bg-hover)] transition-colors cursor-pointer text-left"
                    >
                      <ShareIcon className="w-3.5 h-3.5 text-[var(--text-secondary)]" />
                      <span>Share</span>
                    </button>
                  )}

                  {onDeleteSession && (
                    <>
                      <div className="my-1 border-t border-[var(--border-subtle)]" />
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteSession(activeMenuSession.id);
                          setMenuSessionId(null);
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg hover:bg-[var(--status-error-soft)] text-[var(--status-error)] transition-colors cursor-pointer text-left"
                      >
                        <TrashIcon className="w-3.5 h-3.5" />
                        <span>Delete</span>
                      </button>
                    </>
                  )}
                </div>
              )}

              {shareToast && (
                <div className="fixed bottom-4 left-4 z-50 px-3 py-1.5 rounded-lg bg-[var(--bg-panel)] border border-[var(--accent-border)] text-[11px] font-mono-tech text-[var(--accent)] shadow-lg">
                  {shareToast}
                </div>
              )}
            </div>
          );
        })()}
      </div>

      {/* Live Capability Footer + User Account (ChatGPT Style) & Theme Toggle */}
      <div className="shrink-0 px-3 py-2 border-t border-[var(--border-subtle)] flex flex-col gap-2 bg-[var(--bg-panel)]">
        <div className="rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)] px-2.5 py-1.5 space-y-0.5">
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
              <span className="font-medium">
                {backendOnline === null
                  ? "Checking API..."
                  : backendOnline
                  ? "API Connected"
                  : "API Offline"}
              </span>
            </span>
            {status && (
              <span suppressHydrationWarning className="font-mono-tech text-[10px] text-[var(--text-muted)]">
                {status.indexed_chunks} chks
              </span>
            )}
          </div>
          {status && (
            <div suppressHydrationWarning className="flex items-center justify-between text-[10px] font-mono-tech">
              <div className="flex items-center gap-1.5 min-w-0 truncate">
                <span
                  className={
                    status.llm_configured
                      ? "text-[var(--status-success)] font-medium"
                      : "text-[var(--status-warning)]"
                  }
                  title={`LLM Generator: ${status.llm_provider || "unknown"} (${status.llm_model || "unknown"})`}
                >
                  {status.llm_configured
                    ? status.llm_provider === "gemini"
                      ? "gemini-flash"
                      : `${status.llm_provider}`
                    : "llm:off"}
                </span>
                {status.stt_configured && (
                  <>
                    <span className="text-[var(--text-muted)] opacity-60">·</span>
                    <span
                      className="text-[var(--accent)] font-medium"
                      title="Voice Engine: Sarvam AI (Saaras STT + Bulbul TTS)"
                    >
                      sarvam-voice
                    </span>
                  </>
                )}
              </div>
              <span className="text-[var(--text-muted)] shrink-0 ml-1.5">
                {status.embedding_dimension}d
              </span>
            </div>
          )}
        </div>

        {/* User Account Menu with popover + small theme toggle */}
        <UserAccountMenu />
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
                <span className="text-[10px] font-sans text-[var(--accent)] font-medium">
                  | संवाद
                </span>
              </Link>
            )}
            <h1 className="font-display font-medium text-sm text-[var(--text-primary)] truncate">
              {pageTitle || "Research Workspace"}
            </h1>
          </div>

          <div className="flex items-center gap-2">
            {headerActions}
            {!user && (
              <div suppressHydrationWarning className="flex items-center gap-2 ml-1">
                <button
                  type="button"
                  onClick={() => openAuthModal("login")}
                  className="px-3.5 py-1.5 rounded-full text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-hover)] border border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-all cursor-pointer"
                >
                  Log in
                </button>
                <button
                  type="button"
                  onClick={() => openAuthModal("signup")}
                  className="px-3.5 py-1.5 rounded-full text-xs font-semibold bg-[var(--text-primary)] text-[var(--bg-canvas)] hover:opacity-90 transition-opacity cursor-pointer shadow-xs"
                >
                  Sign up for free
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Body */}
        <div className="flex-1 min-h-0 flex overflow-hidden">{children}</div>
      </div>

      {/* Global Authentication Modal */}
      <AuthModal />
    </div>
  );
}
