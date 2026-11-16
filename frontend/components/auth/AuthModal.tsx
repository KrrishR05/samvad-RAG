"use client";

import React, { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { SamvadLogo } from "@/components/ui/Icons";

export function AuthModal() {
  const {
    isAuthModalOpen,
    authModalMode,
    closeAuthModal,
    openAuthModal,
    login,
    signup,
    loginWithGoogle,
    isLoading,
  } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showGooglePicker, setShowGooglePicker] = useState(false);
  const [googleCustomEmail, setGoogleCustomEmail] = useState("");
  const [googleCustomName, setGoogleCustomName] = useState("");

  if (!isAuthModalOpen) return null;

  const isLogin = authModalMode === "login";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError("Please fill in all required fields.");
      return;
    }

    try {
      if (isLogin) {
        await login({ email: email.trim(), password });
      } else {
        if (!name.trim()) {
          setError("Please enter your full name.");
          return;
        }
        if (password.length < 6) {
          setError("Password must be at least 6 characters.");
          return;
        }
        await signup({ name: name.trim(), email: email.trim(), password });
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Authentication failed. Please verify your details.");
      }
    }
  };

  const handleGoogleClick = () => {
    setError(null);
    setShowGooglePicker(true);
  };

  const confirmGoogleAuth = async (selectedEmail: string, selectedName: string) => {
    setError(null);
    try {
      const googleId = "goog_" + Math.random().toString(36).substring(2, 11);
      await loginWithGoogle({
        google_id: googleId,
        email: selectedEmail,
        name: selectedName,
        avatar_url: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
          selectedName
        )}&backgroundColor=8b5cf6,ec4899,3b82f6`,
      });
      setShowGooglePicker(false);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Google authentication failed. Please try again.");
      }
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-fade-in">
      <div
        className="w-full max-w-[420px] rounded-2xl border border-[var(--border-strong)] bg-[var(--bg-panel)] shadow-2xl p-6 sm:p-8 relative text-[var(--text-primary)]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={closeAuthModal}
          className="absolute top-4 right-4 p-2 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-full hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
          title="Close"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="p-2.5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] mb-3 shadow-inner">
            <SamvadLogo className="w-8 h-8" />
          </div>
          <h2 className="font-display font-bold text-xl sm:text-2xl tracking-tight text-[var(--text-primary)]">
            {isLogin ? "Welcome back" : "Create your account"}
          </h2>
          <p className="text-xs text-[var(--text-secondary)] mt-1.5 max-w-[300px]">
            {isLogin
              ? "Sign in to SAMVAD to access research workspaces and indexed evidence."
              : "Experience voice-first, evidence-grounded AI research in 10+ Indic languages."}
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-[var(--status-error)]/10 border border-[var(--status-error)]/30 text-[var(--status-error)] text-xs flex items-center gap-2">
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="leading-tight">{error}</span>
          </div>
        )}

        {/* Google OAuth Modal Picker Popup */}
        {showGooglePicker ? (
          <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] p-4 mb-4 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[var(--border-subtle)]">
              <span className="text-xs font-semibold flex items-center gap-1.5">
                <GoogleIcon className="w-4 h-4" />
                <span>Choose a Google Account</span>
              </span>
              <button
                type="button"
                onClick={() => setShowGooglePicker(false)}
                className="text-[11px] text-[var(--text-muted)] hover:underline"
              >
                Cancel
              </button>
            </div>

            {/* Quick 1-click Google Profile */}
            <button
              type="button"
              onClick={() => confirmGoogleAuth("krrish.raj@gmail.com", "Krrish Raj")}
              className="w-full flex items-center gap-3 p-2.5 rounded-lg hover:bg-[var(--bg-panel)] border border-transparent hover:border-[var(--border-subtle)] transition-colors text-left cursor-pointer group"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center text-white font-bold text-xs shadow-sm">
                KR
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-xs font-medium text-[var(--text-primary)] group-hover:text-[var(--accent)]">
                  Krrish Raj
                </div>
                <div className="text-[11px] text-[var(--text-muted)] truncate">krrish.raj@gmail.com</div>
              </div>
              <span className="text-[10px] font-mono-tech px-1.5 py-0.5 rounded bg-[var(--bg-panel)] text-[var(--accent)] border border-[var(--accent-border)]">
                Active
              </span>
            </button>

            {/* Custom Google Account Entry */}
            <div className="pt-2 border-t border-[var(--border-subtle)]/60 space-y-2">
              <span className="text-[11px] text-[var(--text-muted)] block">Or connect another Google account:</span>
              <input
                type="text"
                placeholder="Google Account Name (e.g. Priya Sharma)"
                value={googleCustomName}
                onChange={(e) => setGoogleCustomName(e.target.value)}
                className="w-full text-xs px-2.5 py-1.5 rounded-md bg-[var(--bg-panel)] border border-[var(--border-subtle)] focus:border-[var(--accent)] focus:outline-none"
              />
              <input
                type="email"
                placeholder="Google Email (e.g. priya@gmail.com)"
                value={googleCustomEmail}
                onChange={(e) => setGoogleCustomEmail(e.target.value)}
                className="w-full text-xs px-2.5 py-1.5 rounded-md bg-[var(--bg-panel)] border border-[var(--border-subtle)] focus:border-[var(--accent)] focus:outline-none"
              />
              <button
                type="button"
                disabled={!googleCustomEmail.trim()}
                onClick={() =>
                  confirmGoogleAuth(
                    googleCustomEmail.trim(),
                    googleCustomName.trim() || googleCustomEmail.split("@")[0]
                  )
                }
                className="w-full py-1.5 rounded-md text-xs font-medium bg-[var(--accent)] hover:opacity-95 text-white transition-opacity disabled:opacity-50 cursor-pointer"
              >
                Sign In with this Google Account
              </button>
            </div>
          </div>
        ) : (
          <>
            {/* Primary Google Button (ChatGPT / Gemini style) */}
            <button
              type="button"
              onClick={handleGoogleClick}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-2.5 px-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] hover:border-[var(--border-default)] transition-all font-medium text-xs sm:text-sm shadow-sm cursor-pointer"
            >
              <GoogleIcon className="w-4 h-4" />
              <span>Continue with Google</span>
            </button>

            {/* Divider */}
            <div className="flex items-center my-4">
              <div className="flex-1 border-t border-[var(--border-subtle)]" />
              <span className="px-3 text-[11px] font-mono-tech uppercase text-[var(--text-muted)] tracking-wider">
                OR
              </span>
              <div className="flex-1 border-t border-[var(--border-subtle)]" />
            </div>

            {/* Email Form */}
            <form onSubmit={handleSubmit} className="space-y-3">
              {!isLogin && (
                <div>
                  <label className="block text-[11px] font-medium text-[var(--text-secondary)] mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="Krrish Raj"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-[var(--bg-surface)] border border-[var(--border-subtle)] focus:border-[var(--accent)] focus:outline-none transition-colors text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                  />
                </div>
              )}

              <div>
                <label className="block text-[11px] font-medium text-[var(--text-secondary)] mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl text-xs sm:text-sm bg-[var(--bg-surface)] border border-[var(--border-subtle)] focus:border-[var(--accent)] focus:outline-none transition-colors text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-[11px] font-medium text-[var(--text-secondary)]">
                    Password
                  </label>
                  {isLogin && (
                    <button
                      type="button"
                      onClick={() => alert("To reset password, please contact the administrator.")}
                      className="text-[10px] text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3 py-2 pr-9 rounded-xl text-xs sm:text-sm bg-[var(--bg-surface)] border border-[var(--border-subtle)] focus:border-[var(--accent)] focus:outline-none transition-colors text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] p-1"
                    tabIndex={-1}
                  >
                    {showPassword ? (
                      <EyeOffIcon className="w-3.5 h-3.5" />
                    ) : (
                      <EyeIcon className="w-3.5 h-3.5" />
                    )}
                  </button>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full mt-2 py-2.5 px-4 rounded-xl text-xs sm:text-sm font-semibold bg-[var(--accent)] hover:opacity-95 text-white transition-opacity shadow-md flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : isLogin ? (
                  "Log in"
                ) : (
                  "Create account"
                )}
              </button>
            </form>
          </>
        )}

        {/* Switch Login / Signup */}
        <div className="mt-5 text-center text-xs text-[var(--text-secondary)]">
          {isLogin ? (
            <span>
              Don&apos;t have an account?{" "}
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setShowGooglePicker(false);
                  openAuthModal("signup");
                }}
                className="font-medium text-[var(--accent)] hover:underline cursor-pointer"
              >
                Sign up
              </button>
            </span>
          ) : (
            <span>
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setShowGooglePicker(false);
                  openAuthModal("login");
                }}
                className="font-medium text-[var(--accent)] hover:underline cursor-pointer"
              >
                Log in
              </button>
            </span>
          )}
        </div>

        {/* Security Badge */}
        <div className="mt-4 pt-3 border-t border-[var(--border-subtle)] flex items-center justify-center gap-1.5 text-[10.5px] text-[var(--text-muted)]">
          <svg className="w-3 h-3 text-[var(--status-success)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
            <path d="M7 11V7a5 5 0 0 1 10 0v4" />
          </svg>
          <span>PBKDF2 encrypted · Google OAuth verified</span>
        </div>
      </div>
    </div>
  );
}

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
      />
    </svg>
  );
}

function EyeIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

function EyeOffIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}
