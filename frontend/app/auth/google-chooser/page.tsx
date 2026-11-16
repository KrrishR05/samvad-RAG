"use client";

import React, { useState } from "react";
import { SamvadLogo } from "@/components/ui/Icons";

interface AccountItem {
  id: string;
  name: string;
  email: string;
  avatarColor: string;
  initial: string;
}

const PRESET_ACCOUNTS: AccountItem[] = [
  {
    id: "acc_digitalwill",
    name: "noreply.digitalwill",
    email: "noreply.digitalwill@gmail.com",
    avatarColor: "bg-[#2e7d32]",
    initial: "n",
  },
  {
    id: "acc_krrish",
    name: "Krrish Raj",
    email: "krrish.raj@gmail.com",
    avatarColor: "bg-[#8b5cf6]",
    initial: "K",
  },
];

export default function GoogleChooserPopup() {
  const [showOtherInput, setShowOtherInput] = useState(false);
  const [customEmail, setCustomEmail] = useState("");
  const [customName, setCustomName] = useState("");
  const [isAuthorizing, setIsAuthorizing] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<string | null>(null);

  const handleSelectAccount = (email: string, name: string) => {
    setIsAuthorizing(true);
    setSelectedEmail(email);

    setTimeout(() => {
      const googleId = "goog_" + Math.random().toString(36).substring(2, 11);
      const avatarUrl = `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
        name
      )}&backgroundColor=8b5cf6,ec4899,3b82f6`;

      if (window.opener) {
        window.opener.postMessage(
          {
            type: "GOOGLE_AUTH_SUCCESS",
            payload: {
              google_id: googleId,
              email: email.trim().toLowerCase(),
              name: name.trim(),
              avatar_url: avatarUrl,
            },
          },
          "*"
        );
      }

      window.close();
    }, 600);
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customEmail.trim()) return;
    const derivedName = customName.trim() || customEmail.split("@")[0];
    handleSelectAccount(customEmail.trim(), derivedName);
  };

  return (
    <div className="min-h-screen bg-white text-[#1f1f1f] flex flex-col justify-between p-6 sm:p-10 font-sans select-none">
      {/* Top Google Header */}
      <div className="flex items-center gap-2 mb-6">
        <GoogleIcon className="w-5 h-5" />
        <span className="text-xs font-medium text-[#444746]">
          Sign in with Google
        </span>
      </div>

      {/* Main Content Area (Identical to Google Account Chooser Screenshot) */}
      <div className="max-w-md w-full mx-auto my-auto py-2">
        {/* App Emblem & Heading */}
        <div className="flex items-start gap-4 mb-6">
          <div className="p-2 rounded-xl bg-purple-50 border border-purple-100 shadow-xs shrink-0">
            <SamvadLogo className="w-8 h-8" />
          </div>
          <div>
            <h1 className="text-2xl font-normal text-[#1f1f1f] tracking-tight leading-tight">
              Choose an account
            </h1>
            <p className="text-sm text-[#444746] mt-1">
              to continue to <strong className="font-semibold text-purple-700">SAMVAD</strong>
            </p>
          </div>
        </div>

        {/* Loading Indicator */}
        {isAuthorizing && (
          <div className="mb-4 p-3 rounded-lg bg-purple-50 border border-purple-200 text-purple-800 text-xs flex items-center gap-2 animate-in fade-in">
            <div className="w-4 h-4 border-2 border-purple-600 border-t-transparent rounded-full animate-spin shrink-0" />
            <span>Signing in to SAMVAD as {selectedEmail}...</span>
          </div>
        )}

        {/* Account Chooser List */}
        <div className="border-t border-b border-[#e0e2e0] divide-y divide-[#e0e2e0]">
          {PRESET_ACCOUNTS.map((acc) => (
            <button
              key={acc.id}
              type="button"
              disabled={isAuthorizing}
              onClick={() => handleSelectAccount(acc.email, acc.name)}
              className="w-full flex items-center gap-3.5 py-3.5 px-2 hover:bg-[#f8fafd] transition-colors text-left cursor-pointer group rounded-lg"
            >
              {/* Account Avatar Circle */}
              <div
                className={`w-9 h-9 rounded-full ${acc.avatarColor} text-white flex items-center justify-center font-medium text-sm shadow-xs shrink-0`}
              >
                {acc.initial}
              </div>

              {/* Account Info */}
              <div className="min-w-0 flex-1 leading-snug">
                <div className="text-sm font-medium text-[#1f1f1f] group-hover:text-purple-700 truncate">
                  {acc.name}
                </div>
                <div className="text-xs text-[#5f6368] truncate">
                  {acc.email}
                </div>
              </div>
            </button>
          ))}

          {/* Use another account row */}
          {!showOtherInput ? (
            <button
              type="button"
              disabled={isAuthorizing}
              onClick={() => setShowOtherInput(true)}
              className="w-full flex items-center gap-3.5 py-3.5 px-2 hover:bg-[#f8fafd] transition-colors text-left cursor-pointer group rounded-lg"
            >
              <div className="w-9 h-9 rounded-full bg-transparent border border-[#747775] text-[#444746] flex items-center justify-center shrink-0">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="text-sm font-medium text-[#1f1f1f] group-hover:text-purple-700">
                Use another account
              </div>
            </button>
          ) : (
            <form onSubmit={handleCustomSubmit} className="py-4 px-2 space-y-3">
              <div className="text-xs font-semibold text-[#1f1f1f]">
                Sign in with another Google Account:
              </div>
              <input
                type="text"
                placeholder="Name (e.g. Vikram Sarabhai)"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-[#747775] focus:border-purple-600 focus:outline-none text-[#1f1f1f]"
              />
              <input
                type="email"
                required
                placeholder="Email (e.g. vikram@gmail.com)"
                value={customEmail}
                onChange={(e) => setCustomEmail(e.target.value)}
                className="w-full px-3 py-2 text-xs rounded-lg border border-[#747775] focus:border-purple-600 focus:outline-none text-[#1f1f1f]"
              />
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="submit"
                  disabled={isAuthorizing || !customEmail.trim()}
                  className="px-4 py-2 rounded-full text-xs font-medium bg-[#0b57d0] hover:bg-[#0842a0] text-white transition-colors cursor-pointer"
                >
                  Continue with this Google account
                </button>
                <button
                  type="button"
                  onClick={() => setShowOtherInput(false)}
                  className="px-3 py-2 text-xs text-[#5f6368] hover:text-[#1f1f1f]"
                >
                  Cancel
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Disclaimer Notice */}
        <p className="text-xs text-[#5f6368] mt-6 leading-relaxed">
          Before using this app, you can review SAMVAD&apos;s{" "}
          <span className="text-[#0b57d0] hover:underline cursor-pointer">
            Privacy Policy
          </span>{" "}
          and{" "}
          <span className="text-[#0b57d0] hover:underline cursor-pointer">
            Terms of Service
          </span>
          .
        </p>
      </div>

      {/* Footer Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-[#5f6368] pt-6 border-t border-[#f2f2f2] gap-3">
        <div className="flex items-center gap-2 cursor-pointer hover:text-[#1f1f1f]">
          <span>English (United States)</span>
          <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>

        <div className="flex items-center gap-6">
          <span className="hover:text-[#1f1f1f] cursor-pointer">Help</span>
          <span className="hover:text-[#1f1f1f] cursor-pointer">Privacy</span>
          <span className="hover:text-[#1f1f1f] cursor-pointer">Terms</span>
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

function UserIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

