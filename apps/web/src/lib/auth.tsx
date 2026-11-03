'use client';

import React, { createContext, useContext, useState } from 'react';
import { User, UserRole } from '@/lib/types';

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

function readStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

function readStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(readStoredUser);
  const [token, setToken] = useState<string | null>(readStoredToken);

  const persist = (authUser: User, accessToken: string) => {
    setUser(authUser);
    setToken(accessToken);
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(authUser));
      localStorage.setItem(TOKEN_KEY, accessToken);
    } catch {
      // ignore storage failures
    }
  };

  const login = async (
    email: string,
    roleKey = 'officer',
    password = 'demo123'
  ): Promise<boolean> => {
    void roleKey;
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      if (!data.access_token || !data.user) return false;
      persist(
        {
          id: String(data.user.id),
          name: data.user.name,
          email: data.user.email,
          role: data.user.role as UserRole,
          bureau: data.user.bureau || '',
          region: data.user.region || '',
          active: true,
        },
        data.access_token
      );
      return true;
    } catch {
      return false;
    }
  };

  const switchUser = async (roleKey: string) => {
    const email = ROLE_EMAIL_MAP[roleKey];
    if (email) await login(email);
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
    if (typeof window !== 'undefined') window.location.href = '/login';
  };

  const hasRole = (allowedRoles: UserRole[]): boolean =>
    !!user && allowedRoles.includes(user.role);

  return (
    <AuthContext.Provider
      value={{ user, token, isAuthenticated: !!user, login, switchUser, logout, hasRole }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
