export type UserPlan = "free" | "pro";

export interface User {
  id: string;
  email: string;
  name: string;
  provider: "email" | "google";
  google_id?: string | null;
  avatar_url?: string | null;
  plan: UserPlan;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  token: string;
  user: User;
  message: string;
}

export interface UserResponse {
  user: User;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface SignupPayload {
  name: string;
  email: string;
  password: string;
}

export interface GoogleAuthPayload {
  credential?: string;
  google_id?: string;
  email?: string;
  name?: string;
  avatar_url?: string;
}

export interface ProfileUpdatePayload {
  name?: string;
  plan?: UserPlan;
  avatar_url?: string;
}

export interface WaitlistResponse {
  status: "joined" | "already_joined";
  email: string;
  position: number;
  email_sent: boolean;
  message: string;
}

export interface WaitlistStatusResponse {
  on_waitlist: boolean;
  email: string;
  position?: number | null;
}

