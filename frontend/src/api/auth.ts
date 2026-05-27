import type { User } from "../types/rule";
export type { User };

const API_BASE = "/api";

export interface LoginResponse {
  token: string;
  user_id: number;
  username: string;
  role: string;
}

export const authApi = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "登录失败");
    }
    const data = await res.json();
    localStorage.setItem("token", data.token);
    return data;
  },

  logout: async () => {
    await fetch(`${API_BASE}/auth/logout`, { method: "POST" });
    localStorage.removeItem("token");
  },

  me: async (): Promise<User | null> => {
    const token = localStorage.getItem("token");
    if (!token) return null;
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) return null;
    return res.json();
  },

  getToken: () => localStorage.getItem("token"),

  isAuthenticated: () => !!localStorage.getItem("token"),
};
