"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";

export function AuthModal() {
  const {
    isAuthModalOpen,
    closeAuthModal,
    login,
    signup,
    loginWithGoogle,
    isLoading,
  } = useAuth();

  const [step, setStep] = useState<"email" | "password">("email");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isNewUser, setIsNewUser] = useState(false);
  const [phoneStep, setPhoneStep] = useState(false);
  const [phoneNumber, setPhoneNumber] = useState("");

  // Listen for Google Auth Popup postMessage
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.data?.type === "GOOGLE_AUTH_SUCCESS" && event.data?.payload) {
        setError(null);
        loginWithGoogle(event.data.payload).catch((err: unknown) => {
          if (err instanceof Error) setError(err.message);
          else setError("Google sign-in failed. Please try again.");
        });
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [loginWithGoogle]);

  if (!isAuthModalOpen) return null;

  // Open native Google Account Chooser popup centered on screen
  const handleGoogleClick = () => {
    setError(null);
    const width = 500;
    const height = 630;
    const left = Math.max(0, window.screenX + (window.outerWidth - width) / 2);
    const top = Math.max(0, window.screenY + (window.outerHeight - height) / 2);

    window.open(
      "/auth/google-chooser",
      "google_signin_popup",
      `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no,location=no,status=no,resizable=yes`
    );
  };

  const handleAppleClick = () => {
    setError("Apple authentication is coming soon. Please continue with Google or Email.");
  };

  const handlePhoneClick = () => {
    setError(null);
    setPhoneStep(true);
  };

  const handleEmailContinue = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmed = email.trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!trimmed || !emailRegex.test(trimmed)) {
      setError("Please enter a valid email address.");
      return;
    }

    // Default known demo user is krrish@samvad.ai
    if (trimmed === "krrish@samvad.ai") {
      setIsNewUser(false);
    } else {
      // Allow user to login or auto-register seamlessly
      setIsNewUser(true);
    }

    setStep("password");
  };

  const handleFinalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!password.trim()) {
      setError("Please enter your password.");
      return;
    }

    try {
      if (isNewUser) {
        if (!name.trim()) {
          setError("Please enter your full name.");
          return;
        }
        if (password.length < 6) {
          setError("Password must be at least 6 characters.");
          return;
        }
        await signup({
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
        });
      } else {
        await login({
          email: email.trim().toLowerCase(),
          password,
        });
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Authentication failed. Please verify your credentials.");
      }
    }
  };

  const handlePhoneSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!phoneNumber.trim()) {
      setError("Please enter a valid phone number.");
      return;
    }
    setError("SMS verification service is in private beta. Please continue with Google or Email.");
  };

  const resetModal = () => {
    setStep("email");
    setPhoneStep(false);
    setError(null);
    setPassword("");
    closeAuthModal();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div
        className="w-full max-w-[420px] rounded-[28px] border border-[var(--border-default)] bg-[var(--bg-panel)] shadow-2xl p-7 sm:p-9 relative text-[var(--text-primary)] animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button ('×' in top right, exactly like ChatGPT) */}
        <button
          type="button"
          onClick={resetModal}
          className="absolute top-5 right-5 w-8 h-8 flex items-center justify-center text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-full hover:bg-[var(--bg-hover)] transition-colors cursor-pointer"
          title="Close"
          aria-label="Close"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>

        {/* Title & Subtitle (Exact ChatGPT styling from screenshot) */}
        <div className="text-center mb-6 pt-1">
          <h2 className="font-display font-bold text-2xl tracking-tight text-[var(--text-primary)]">
            Log in or sign up
          </h2>
          <p className="text-[13px] text-[var(--text-secondary)] mt-1.5 leading-relaxed max-w-[320px] mx-auto">
            You&apos;ll get smarter responses and can upload files, images, and more.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-4 p-3 rounded-xl bg-[var(--status-error)]/10 border border-[var(--status-error)]/30 text-[var(--status-error)] text-xs flex items-center gap-2 animate-in fade-in">
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span className="leading-tight">{error}</span>
          </div>
        )}

        {/* STEP 1: Main ChatGPT-style Socials + Single Email Input */}
        {step === "email" && !phoneStep && (
          <div className="space-y-3">
            {/* 1. Continue with Google (Exact Pill Button from screenshot) */}
            <button
              type="button"
              onClick={handleGoogleClick}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-full border border-[var(--border-strong)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] transition-all font-medium text-xs sm:text-sm text-[var(--text-primary)] shadow-xs cursor-pointer active:scale-[0.99]"
            >
              <GoogleIcon className="w-4 h-4 shrink-0" />
              <span>Continue with Google</span>
            </button>

            {/* 2. Continue with Apple */}
            <button
              type="button"
              onClick={handleAppleClick}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-full border border-[var(--border-strong)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] transition-all font-medium text-xs sm:text-sm text-[var(--text-primary)] shadow-xs cursor-pointer active:scale-[0.99]"
            >
              <AppleIcon className="w-4 h-4 shrink-0" />
              <span>Continue with Apple</span>
            </button>

            {/* 3. Continue with phone */}
            <button
              type="button"
              onClick={handlePhoneClick}
              disabled={isLoading}
              className="w-full flex items-center justify-center gap-3 py-3 px-4 rounded-full border border-[var(--border-strong)] bg-[var(--bg-surface)] hover:bg-[var(--bg-hover)] transition-all font-medium text-xs sm:text-sm text-[var(--text-primary)] shadow-xs cursor-pointer active:scale-[0.99]"
            >
              <PhoneIcon className="w-4 h-4 shrink-0" />
              <span>Continue with phone</span>
            </button>

            {/* Divider: OR */}
            <div className="flex items-center my-4">
              <div className="flex-1 border-t border-[var(--border-subtle)]" />
              <span className="px-3 text-[11px] font-mono-tech uppercase text-[var(--text-muted)] tracking-wider">
                OR
              </span>
              <div className="flex-1 border-t border-[var(--border-subtle)]" />
            </div>

            {/* Email Input + Continue */}
            <form onSubmit={handleEmailContinue} className="space-y-3">
              <div>
                <input
                  type="email"
                  required
                  placeholder="Email address"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 rounded-2xl text-xs sm:text-sm bg-[var(--bg-surface)] border border-[var(--border-strong)] focus:border-[var(--accent)] focus:outline-none transition-colors text-[var(--text-primary)] placeholder-[var(--text-muted)] shadow-xs"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 rounded-full text-xs sm:text-sm font-semibold bg-[var(--text-primary)] text-[var(--bg-canvas)] hover:opacity-90 transition-opacity shadow-md flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99]"
              >
                Continue
              </button>
            </form>
          </div>
        )}

        {/* STEP 2: Password & Account Completion */}
        {step === "password" && !phoneStep && (
          <form onSubmit={handleFinalSubmit} className="space-y-4">
            {/* Email pill with edit button */}
            <div className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs">
              <span className="font-medium text-[var(--text-primary)] truncate mr-2">
                {email}
              </span>
              <button
                type="button"
                onClick={() => {
                  setStep("email");
                  setError(null);
                }}
                className="text-[11px] font-semibold text-[var(--accent)] hover:underline cursor-pointer shrink-0"
              >
                Edit
              </button>
            </div>

            {isNewUser && (
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
                  className="w-full px-4 py-2.5 rounded-xl text-xs sm:text-sm bg-[var(--bg-surface)] border border-[var(--border-strong)] focus:border-[var(--accent)] focus:outline-none transition-colors text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                />
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-[11px] font-medium text-[var(--text-secondary)]">
                  {isNewUser ? "Create Password" : "Password"}
                </label>
                {!isNewUser && (
                  <button
                    type="button"
                    onClick={() => alert("To reset password, contact administrator or test with Samvad@2026.")}
                    className="text-[11px] text-[var(--text-muted)] hover:text-[var(--accent)] transition-colors"
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
                  className="w-full px-4 py-2.5 pr-10 rounded-xl text-xs sm:text-sm bg-[var(--bg-surface)] border border-[var(--border-strong)] focus:border-[var(--accent)] focus:outline-none transition-colors text-[var(--text-primary)] placeholder-[var(--text-muted)]"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)] hover:text-[var(--text-primary)] p-1 cursor-pointer"
                  tabIndex={-1}
                >
                  {showPassword ? (
                    <EyeOffIcon className="w-4 h-4" />
                  ) : (
                    <EyeIcon className="w-4 h-4" />
                  )}
                </button>
              </div>
              {isNewUser && (
                <p className="text-[10px] text-[var(--text-muted)] mt-1">
                  Must be at least 6 characters.
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 rounded-full text-xs sm:text-sm font-semibold bg-[var(--text-primary)] text-[var(--bg-canvas)] hover:opacity-90 transition-opacity shadow-md flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99] disabled:opacity-50"
            >
              {isLoading ? (
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : isNewUser ? (
                "Create account"
              ) : (
                "Continue"
              )}
            </button>

            <button
              type="button"
              onClick={() => {
                setStep("email");
                setError(null);
              }}
              className="w-full text-center text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] pt-1 cursor-pointer"
            >
              ← Back to all sign in options
            </button>
          </form>
        )}

        {/* STEP PHONE */}
        {phoneStep && (
          <form onSubmit={handlePhoneSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-medium text-[var(--text-secondary)] mb-1">
                Phone Number
              </label>
              <input
                type="tel"
                required
                placeholder="+91 98765 43210"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl text-xs sm:text-sm bg-[var(--bg-surface)] border border-[var(--border-strong)] focus:border-[var(--accent)] focus:outline-none transition-colors text-[var(--text-primary)] placeholder-[var(--text-muted)]"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 px-4 rounded-full text-xs sm:text-sm font-semibold bg-[var(--text-primary)] text-[var(--bg-canvas)] hover:opacity-90 transition-opacity shadow-md flex items-center justify-center gap-2 cursor-pointer"
            >
              Send SMS Code
            </button>

            <button
              type="button"
              onClick={() => {
                setPhoneStep(false);
                setError(null);
              }}
              className="w-full text-center text-xs text-[var(--text-muted)] hover:text-[var(--text-primary)] pt-1 cursor-pointer"
            >
              ← Back to all sign in options
            </button>
          </form>
        )}

        {/* Footer Terms */}
        <p className="mt-6 text-center text-[10.5px] text-[var(--text-muted)] leading-relaxed">
          By continuing, you agree to SAMVAD&apos;s{" "}
          <span className="underline hover:text-[var(--text-secondary)] cursor-pointer">
            Terms of Use
          </span>{" "}
          and{" "}
          <span className="underline hover:text-[var(--text-secondary)] cursor-pointer">
            Privacy Policy
          </span>
          .
        </p>
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

function AppleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.84c.66-.82 1.11-1.96.99-3.1-.96.04-2.14.64-2.82 1.44-.61.71-1.15 1.87-1.01 2.98 1.07.08 2.18-.5 2.84-1.32z" />
    </svg>
  );
}

function PhoneIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
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
