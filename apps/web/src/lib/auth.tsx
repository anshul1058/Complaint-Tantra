'use client';

import React, { createContext, useContext, useState } from 'react';
import { User, UserRole } from '@/lib/types';
import { mockUsers } from '@/lib/mock/data';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (email: string, roleKey?: string) => Promise<boolean>;
  switchUser: (roleKey: string) => void;
  logout: () => void;
  hasRole: (allowedRoles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'complaint_tantra_jwt';
const USER_KEY = 'complaint_tantra_user';

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

  const login = async (_email: string, roleKey = 'officer'): Promise<boolean> => {
    const selected = mockUsers[roleKey] || mockUsers.officer;
    setUser(selected);
    const fakeToken = `demo-jwt-token-${selected.role}`;
    setToken(fakeToken);
    try {
      localStorage.setItem(USER_KEY, JSON.stringify(selected));
      localStorage.setItem(TOKEN_KEY, fakeToken);
    } catch {
      // ignore
    }
    return true;
  };

  const switchUser = (roleKey: string) => {
    if (mockUsers[roleKey]) {
      const selected = mockUsers[roleKey];
      setUser(selected);
      const fakeToken = `demo-jwt-token-${selected.role}`;
      setToken(fakeToken);
      try {
        localStorage.setItem(USER_KEY, JSON.stringify(selected));
        localStorage.setItem(TOKEN_KEY, fakeToken);
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
