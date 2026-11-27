"use client";

import React, {
  createContext,
  startTransition,
  useContext,
  useEffect,
  useState,
} from "react";
import type {
  GoogleAuthPayload,
  LoginPayload,
  ProfileUpdatePayload,
  SignupPayload,
  User,
} from "@/types/auth";
import {
  getCurrentUser,
  loginUser,
  loginWithGoogle as apiLoginWithGoogle,
  logoutUser,
  signupUser,
  updateUserProfile,
} from "@/lib/api/auth";

const TOKEN_KEY = "samvad_auth_token";
const USER_KEY = "samvad_auth_user";
const LOGGED_OUT_KEY = "samvad_explicit_logout";

// Default standard user matching user's ChatGPT profile screenshot
export const DEFAULT_USER: User = {
  id: "usr_krrish_default",
  email: "krrish@samvad.ai",
  name: "Krrish",
  provider: "email",
  plan: "free",
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
};

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  isAuthModalOpen: boolean;
  authModalMode: "login" | "signup";
  openAuthModal: (mode?: "login" | "signup") => void;
  closeAuthModal: () => void;
  login: (credentials: LoginPayload) => Promise<void>;
  signup: (credentials: SignupPayload) => Promise<void>;
  loginWithGoogle: (payload: GoogleAuthPayload) => Promise<void>;
  logout: () => void;
  updateProfile: (data: ProfileUpdatePayload) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(DEFAULT_USER);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<"login" | "signup">("login");

  useEffect(() => {
    // Restore session from localStorage on mount
    try {
      if (localStorage.getItem(LOGGED_OUT_KEY) === "true") {
        // The logged-out marker is client-only state restored after mount.
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setUser(null);
        setIsLoading(false);
        return;
      }

      const storedToken = localStorage.getItem(TOKEN_KEY);
      const storedUser = localStorage.getItem(USER_KEY);

      if (storedUser) {
        const parsedUser = JSON.parse(storedUser);
        setUser(parsedUser);
        if (storedToken) {
          setToken(storedToken);
          // Validate token against live backend
          getCurrentUser(storedToken)
            .then((verified) => {
              setUser(verified);
              localStorage.setItem(USER_KEY, JSON.stringify(verified));
            })
            .catch(() => {
              // Keep cached user if offline
            });
        }
      } else {
        // Persist default user session so it stays solid across all pages and refreshes
        setUser(DEFAULT_USER);
        localStorage.setItem(USER_KEY, JSON.stringify(DEFAULT_USER));
      }
    } catch {
      setUser(DEFAULT_USER);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const openAuthModal = (mode: "login" | "signup" = "login") => {
    setAuthModalMode(mode);
    setIsAuthModalOpen(true);
  };

  const closeAuthModal = () => {
    setIsAuthModalOpen(false);
  };

  const login = async (credentials: LoginPayload) => {
    setIsLoading(true);
    try {
      localStorage.removeItem(LOGGED_OUT_KEY);
      const resp = await loginUser(credentials);
      setUser(resp.user);
      setToken(resp.token);
      localStorage.setItem(TOKEN_KEY, resp.token);
      localStorage.setItem(USER_KEY, JSON.stringify(resp.user));
      closeAuthModal();
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (credentials: SignupPayload) => {
    setIsLoading(true);
    try {
      localStorage.removeItem(LOGGED_OUT_KEY);
      const resp = await signupUser(credentials);
      setUser(resp.user);
      setToken(resp.token);
      localStorage.setItem(TOKEN_KEY, resp.token);
      localStorage.setItem(USER_KEY, JSON.stringify(resp.user));
      closeAuthModal();
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogle = async (payload: GoogleAuthPayload) => {
    setIsLoading(true);
    try {
      localStorage.removeItem(LOGGED_OUT_KEY);
      const resp = await apiLoginWithGoogle(payload);
      setUser(resp.user);
      setToken(resp.token);
      localStorage.setItem(TOKEN_KEY, resp.token);
      localStorage.setItem(USER_KEY, JSON.stringify(resp.user));
      closeAuthModal();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    if (token) {
      logoutUser(token);
    }
    setToken(null);
    setUser(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.setItem(LOGGED_OUT_KEY, "true");
  };

  const updateProfile = async (data: ProfileUpdatePayload) => {
    if (!token && user) {
      // Local demo mode update
      const updated = { ...user, ...data, updated_at: new Date().toISOString() };
      setUser(updated);
      localStorage.setItem(USER_KEY, JSON.stringify(updated));
      return;
    }
    if (!token) return;

    setIsLoading(true);
    try {
      const updated = await updateUserProfile(token, data);
      setUser(updated);
      localStorage.setItem(USER_KEY, JSON.stringify(updated));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user,
        isAuthModalOpen,
        authModalMode,
        openAuthModal,
        closeAuthModal,
        login,
        signup,
        loginWithGoogle,
        logout,
        updateProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
