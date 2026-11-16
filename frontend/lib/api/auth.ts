import type {
  AuthResponse,
  GoogleAuthPayload,
  LoginPayload,
  ProfileUpdatePayload,
  SignupPayload,
  User,
  UserResponse,
  WaitlistResponse,
  WaitlistStatusResponse,
} from "@/types/auth";
import { ApiClientError } from "@/lib/api/client";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function authFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new ApiClientError(
      body?.detail || body?.error?.message || `Request failed (${res.status})`,
      res.status
    );
  }

  return res.json() as Promise<T>;
}

export async function signupUser(payload: SignupPayload): Promise<AuthResponse> {
  return authFetch<AuthResponse>("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginUser(payload: LoginPayload): Promise<AuthResponse> {
  return authFetch<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function loginWithGoogle(payload: GoogleAuthPayload): Promise<AuthResponse> {
  return authFetch<AuthResponse>("/api/v1/auth/google", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getCurrentUser(token: string): Promise<User> {
  const res = await authFetch<UserResponse>("/api/v1/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return res.user;
}

export async function updateUserProfile(
  token: string,
  payload: ProfileUpdatePayload
): Promise<User> {
  const res = await authFetch<UserResponse>("/api/v1/auth/profile", {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  return res.user;
}

export async function logoutUser(token: string): Promise<void> {
  try {
    await authFetch<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  } catch {
    // Ignore cleanup failure
  }
}

export async function joinProWaitlist(
  email: string,
  name?: string
): Promise<WaitlistResponse> {
  return authFetch<WaitlistResponse>("/api/v1/auth/waitlist", {
    method: "POST",
    body: JSON.stringify({ email, name }),
  });
}

export async function getWaitlistStatus(
  email: string
): Promise<WaitlistStatusResponse> {
  return authFetch<WaitlistStatusResponse>(
    `/api/v1/auth/waitlist/status?email=${encodeURIComponent(email)}`
  );
}

