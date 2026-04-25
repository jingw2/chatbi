import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: number;
  email: string;
  role: "superadmin" | "admin" | "analyst" | "viewer";
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  setAuth: (user: User, accessToken: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      setAuth: (user, accessToken) => {
        localStorage.setItem("access_token", accessToken);
        set({ user, accessToken });
      },
      clearAuth: () => {
        localStorage.removeItem("access_token");
        set({ user: null, accessToken: null });
      },
    }),
    { name: "chatbi-auth" }
  )
);
