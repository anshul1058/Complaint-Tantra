'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { AuthProvider, useAuth } from '@/lib/auth';
import { mockUsers } from '@/lib/mock/data';
import {
  Building2,
  Lock,
  Mail,
  ShieldCheck,
  ArrowRight,
  Sparkles,
} from 'lucide-react';

function LoginContent() {
  const router = useRouter();
  const { login } = useAuth();
  const [email, setEmail] = useState('rakesh.rb@aicte-india.org');
  const [selectedRoleKey, setSelectedRoleKey] = useState('officer');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    await login(email, selectedRoleKey);
    setTimeout(() => {
      router.push('/');
    }, 400);
  };

  const handleRolePreset = (key: string) => {
    setSelectedRoleKey(key);
    const userPreset = mockUsers[key];
    if (userPreset) {
      setEmail(userPreset.email);
    }
  };

  return (
    <div className="min-h-screen bg-[#f4f6fa] flex flex-col justify-between">
      {/* 1. Indian National Flag Tricolor Ribbon */}
      <div className="w-full h-1.5 flex">
        <div className="w-1/3 h-full bg-[#FF9933]" />
        <div className="w-1/3 h-full bg-white relative flex items-center justify-center">
          <div className="w-1.5 h-1.5 rounded-full border border-[#000080]" />
        </div>
        <div className="w-1/3 h-full bg-[#138808]" />
      </div>

      {/* 2. Top Govt Bar */}
      <div className="bg-[#0b132b] text-slate-300 text-xs px-6 py-2 flex items-center justify-between border-b border-white/10">
        <div className="flex items-center gap-2">
          <span className="text-amber-400 font-bold">भारत सरकार | GOVERNMENT OF INDIA</span>
          <span className="text-slate-500">•</span>
          <span className="text-slate-300">शिक्षा मंत्रालय | Ministry of Education</span>
        </div>
        <div className="flex items-center gap-2 text-amber-300 text-xs font-semibold">
          <span>विकसित भारत @2047</span>
        </div>
      </div>

      {/* 3. Main Login Card Container */}
      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-white rounded-xl shadow-xl border border-slate-200 overflow-hidden">
          {/* Header of Login Card */}
          <div className="bg-gradient-to-r from-[#0f172a] via-[#1E3A8A] to-[#0f172a] text-white p-6 text-center">
            <div className="w-14 h-14 mx-auto mb-3 rounded-full bg-gradient-to-tr from-amber-500 to-amber-300 p-0.5 shadow-md flex items-center justify-center">
              <div className="w-full h-full bg-[#1E3A8A] rounded-full flex flex-col items-center justify-center text-amber-300">
                <Building2 className="w-7 h-7 text-amber-300" />
              </div>
            </div>

            <h2 className="text-xl font-bold font-serif tracking-wide text-white">
              शिकायत-तंत्र
            </h2>
            <p className="text-xs font-sans text-amber-300 font-bold uppercase tracking-wider mt-0.5">
              Complaint-Tantra Portal
            </p>
            <p className="text-[11px] text-slate-200 mt-1">
              अखिल भारतीय तकनीकी शिक्षा परिषद (AICTE)
            </p>
            <p className="text-[10px] text-slate-300">
              Integrated Complaint Monitoring & Inter-Bureau Overlap Tracking
            </p>
          </div>

          {/* Form Area */}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Official Email ID / शासकीय ईमेल
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="officer@aicte-india.org"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent font-medium"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                Password / गुप्त कूट
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="password"
                  required
                  defaultValue="••••••••••••"
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-[#1E3A8A] focus:border-transparent font-medium"
                />
              </div>
            </div>

            {/* Quick SIH Evaluator Role Presets */}
            <div className="pt-2 border-t border-slate-200">
              <label className="block text-[11px] font-bold text-amber-800 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                SIH Evaluator Demo Roles (Select to auto-fill):
              </label>

              <div className="grid grid-cols-2 gap-1.5 text-xs">
                {[
                  { key: 'officer', label: 'RB Officer', name: 'Rakesh Sharma' },
                  { key: 'pgrcOfficer', label: 'PGRC Officer', name: 'Meera Deshmukh' },
                  { key: 'senior', label: 'Senior Mgmt', name: 'Dr. Abhay Jere' },
                  { key: 'authority', label: 'Chairman AICTE', name: 'Prof. T. G. Sitharam' },
                ].map((item) => (
                  <button
                    type="button"
                    key={item.key}
                    onClick={() => handleRolePreset(item.key)}
                    className={`p-2 rounded border text-left transition cursor-pointer ${
                      selectedRoleKey === item.key
                        ? 'border-[#1E3A8A] bg-indigo-50 font-bold text-[#1E3A8A]'
                        : 'border-slate-200 hover:bg-slate-50 text-slate-700'
                    }`}
                  >
                    <div className="text-[11px] font-bold leading-tight">{item.label}</div>
                    <div className="text-[10px] text-slate-500 truncate">{item.name}</div>
                  </button>
                ))}
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-2.5 px-4 bg-[#1E3A8A] hover:bg-[#1e40af] text-white font-bold rounded-md text-sm transition-all shadow-md flex items-center justify-center gap-2 cursor-pointer"
            >
              <ShieldCheck className="w-4 h-4 text-amber-400" />
              {isLoading ? 'Authenticating with AICTE SSO...' : 'Sign In to Portal / प्रवेश करें'}
              <ArrowRight className="w-4 h-4" />
            </button>

            <p className="text-[10px] text-slate-500 text-center pt-2">
              Authorized access only. All activities are monitored and cryptographically audited under IT Act 2000.
            </p>
          </form>
        </div>
      </div>

      {/* 4. Footer */}
      <footer className="bg-[#0b132b] text-slate-400 text-xs py-3 px-6 text-center border-t border-slate-800">
        All India Council for Technical Education • Nelson Mandela Marg, Vasant Kunj, New Delhi-110070
      </footer>
    </div>
  );
}

export default function LoginPage() {
  return <LoginContent />;
}
