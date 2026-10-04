"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { fetchApi } from "../utils/api";

const AuthContext = createContext(null);

export const AUTH_TOKEN_KEY = "smartcity_auth_token";

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Restore authenticated session from localStorage on initial load
  useEffect(() => {
    const initAuth = async () => {
      try {
        const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
        if (!storedToken) {
          setLoading(false);
          return;
        }

        setToken(storedToken);
        // Verify token with backend /api/auth/me
        const profile = await fetchApi("/auth/me");
        setUser(profile);
      } catch (err) {
        console.warn("Session verification expired or invalid. Clearing token.", err.message);
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setToken(null);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();
  }, []);

  const login = useCallback(async (email, password) => {
    const response = await fetchApi("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    localStorage.setItem(AUTH_TOKEN_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  }, []);

  const register = useCallback(async (registrationData) => {
    const response = await fetchApi("/auth/register", {
      method: "POST",
      body: JSON.stringify(registrationData),
    });

    localStorage.setItem(AUTH_TOKEN_KEY, response.access_token);
    setToken(response.access_token);
    setUser(response.user);
    return response.user;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  const isSuperAdmin = Boolean(
    user && (
      user.is_super_admin === true ||
      user.role === "SUPER_ADMIN" ||
      (user.role === "ADMIN" && (
        user.email === "admin@smartcity.gov" ||
        user.department === "General Grievance Cell" ||
        !user.department
      ))
    )
  );

  const value = {
    user,
    token,
    loading,
    isAuthenticated: Boolean(user && token),
    role: user?.role || null,
    isCitizen: user?.role === "CITIZEN",
    isAdmin: user?.role === "ADMIN",
    isSuperAdmin,
    login,
    register,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
