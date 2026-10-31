'use client';

import React, { createContext, useContext, useState } from 'react';
import { User, UserRole } from '@/lib/types';
import { mockUsers } from '@/lib/mock/data';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, roleKey?: string, password?: string) => Promise<boolean>;
  switchUser: (roleKey: string) => Promise<void>;
  logout: () => void;
  hasRole: (allowedRoles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'complaint_tantra_jwt';
const USER_KEY = 'complaint_tantra_user';
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const ROLE_EMAIL_MAP: Record<string, string> = {
  officer: 'asha@rb.gov.in',
  pgrcOfficer: 'ravi@pgrc.gov.in',
  regional: 'meera@rb.gov.in',
  senior: 'sharma@hq.gov.in',
  authority: 'nair@hq.gov.in',
  admin: 'admin@hq.gov.in',
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window === 'undefined') return mockUsers.officer;
    try {
      const storedUser = localStorage.getItem(USER_KEY);
      if (storedUser) return JSON.parse(storedUser);
    } catch {
      // ignore
    }
    return mockUsers.officer;
  });

  const [token, setToken] = useState<string | null>(() => {
    if (typeof window === 'undefined') return 'demo-jwt-token-rb-officer';
    try {
      const storedToken = localStorage.getItem(TOKEN_KEY);
      if (storedToken) return storedToken;
    } catch {
      // ignore
    }
    return 'demo-jwt-token-rb-officer';
  });

  const login = async (
    email: string,
    roleKey = 'officer',
    password = 'demo123'
  ): Promise<boolean> => {
    // 1. Try real backend API login if available
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.access_token && data.user) {
          const authUser: User = {
            id: String(data.user.id),
            name: data.user.name,
            email: data.user.email,
            role: data.user.role as UserRole,
            bureau: data.user.bureau || 'RB',
            region: data.user.region || 'North',
            active: true,
          };
          setUser(authUser);
          setToken(data.access_token);
          try {
            localStorage.setItem(USER_KEY, JSON.stringify(authUser));
            localStorage.setItem(TOKEN_KEY, data.access_token);
          } catch {
            // ignore
          }
          return true;
        }
      }
    } catch {
      // Backend not reached, fall back to mock user
    }

    // 2. Fallback to mock demo user
    const selected = mockUsers[roleKey] || mockUsers.officer;
    setUser(selected);
    const fallbackToken = `demo-jwt-token-${selected.role}`;
    setToken(fallbackToken);
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(selected));
      localStorage.setItem(TOKEN_KEY, fallbackToken);
    } catch {
      // ignore
    }
    return true;
  };

  const switchUser = async (roleKey: string) => {
    const backendEmail = ROLE_EMAIL_MAP[roleKey];
    if (backendEmail) {
      try {
        const res = await fetch(`${API_BASE}/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: backendEmail, password: 'demo123' }),
        });
        if (res.ok) {
          const data = await res.json();
          if (data.access_token && data.user) {
            const authUser: User = {
              id: String(data.user.id),
              name: data.user.name,
              email: data.user.email,
              role: data.user.role as UserRole,
              bureau: data.user.bureau || 'RB',
              region: data.user.region || 'North',
              active: true,
            };
            setUser(authUser);
            setToken(data.access_token);
            try {
              localStorage.setItem(USER_KEY, JSON.stringify(authUser));
              localStorage.setItem(TOKEN_KEY, data.access_token);
            } catch {
              // ignore
            }
            return;
          }
        }
      } catch {
        // Backend not reachable, fall back to mock user
      }
    }

    if (mockUsers[roleKey]) {
      const selected = mockUsers[roleKey];
      setUser(selected);
      const fallbackToken = `demo-jwt-token-${selected.role}`;
      setToken(fallbackToken);
      try {
        localStorage.setItem(USER_KEY, JSON.stringify(selected));
        localStorage.setItem(TOKEN_KEY, fallbackToken);
      } catch {
        // ignore
      }
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    try {
      localStorage.removeItem(USER_KEY);
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      // ignore
    }
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  };

  const hasRole = (allowedRoles: UserRole[]): boolean => {
    if (!user) return false;
    return allowedRoles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        login,
        switchUser,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
