'use client';

import React, { useState } from 'react';
import { useAuth } from '@/lib/auth';
import {
  Search,
  Bell,
  Calendar,
  ChevronDown,
  Sparkles,
  Shield,
  Building2,
  Check,
} from 'lucide-react';
import { RashtrapatiBhavanSketch } from '@/components/layout/GovWatermark';
import { TricolorRibbonWave } from '@/components/layout/TricolorRibbon';

export const GovHeader: React.FC = () => {
  const { user, switchUser } = useAuth();
  const [dateRange, setDateRange] = useState('01 Oct 2026 - 31 Oct 2026');
  const [showRoleMenu, setShowRoleMenu] = useState(false);
  const [showDatePicker, setShowDatePicker] = useState(false);

  // Time-appropriate greeting
  const getGreeting = () => {
    return 'Good Morning,';
  };

  return (
    <header className="relative w-full bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-[0_1px_3px_rgba(30,58,138,0.03)] z-30 overflow-hidden">
      {/* 1. Indian National Flag Micro-Stripe */}
      <div className="national-tricolor-strip w-full" />

      {/* 2. Background Architectural Watermark of Rashtrapati Bhavan */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden flex items-center justify-center opacity-45 -top-4">
        <RashtrapatiBhavanSketch className="w-[820px] max-w-none text-sky-400/25" opacity={0.16} />
      </div>

      {/* 3. Main Header Bar */}
      <div className="relative max-w-[1720px] mx-auto px-4 sm:px-6 py-3 flex flex-col md:flex-row items-center justify-between gap-4">
        
        {/* Left: Official Emblem & AICTE Title */}
        <div className="flex items-center gap-3.5 shrink-0 self-start md:self-center">
          {/* Ashoka Lion Capital Emblem */}
          <div className="w-10 h-12 flex flex-col items-center justify-center">
            <svg viewBox="0 0 100 120" className="w-8 h-10 fill-[#1E3A8A]" aria-label="National Emblem of India">
              <path d="M50 5 C40 5 35 15 35 25 C30 25 25 32 25 40 C25 50 32 55 40 58 C38 65 38 72 40 80 L35 85 L35 95 L65 95 L65 85 L60 80 C62 72 62 65 60 58 C68 55 75 50 75 40 C75 32 70 25 65 25 C65 15 60 5 50 5 Z" />
              <circle cx="50" cy="88" r="5" fill="#1E3A8A" stroke="#0EA5E9" strokeWidth="1" />
              <rect x="28" y="100" width="44" height="6" rx="2" fill="#1E3A8A" />
            </svg>
            <span className="text-[6.5px] font-bold text-[#1E3A8A] tracking-tighter uppercase font-serif">
              सत्यमेव जयते
            </span>
          </div>

          <div className="border-l border-slate-200 pl-3">
            <div className="flex items-center gap-2">
              <span className="text-xl font-extrabold tracking-tight text-[#1E3A8A] font-sans">
                AICTE
              </span>
              <span className="text-[10px] font-bold text-sky-700 bg-sky-50 px-1.5 py-0.5 rounded border border-sky-200">
                Central Portal
              </span>
            </div>
            <div className="text-[11px] font-semibold text-slate-800 leading-tight">
              All India Council for Technical Education
            </div>
            <div className="text-[10px] text-slate-500 font-medium">
              Ministry of Education, Government of India
            </div>
          </div>
        </div>

        {/* Center: Greeting & Performance Tagline with Tricolor Swoosh */}
        <div className="flex-1 flex flex-col sm:flex-row items-center justify-center md:justify-start lg:justify-between px-2 gap-4">
          <div className="text-center sm:text-left">
            <div className="flex items-center justify-center sm:justify-start gap-1.5 text-sky-600 font-medium text-xs">
              <Sparkles className="w-3.5 h-3.5 text-sky-500 animate-sparkle" />
              <span className="italic font-serif text-slate-600 text-sm">{getGreeting()}</span>
            </div>
            <div className="text-xl sm:text-2xl font-extrabold text-[#1E3A8A] tracking-tight -mt-0.5">
              {user?.name || 'Dr. John Doe'}
            </div>
            <div className="text-xs text-slate-500 font-medium">
              Your performance summary this week • AICTE Grievance Triage Grid
            </div>
          </div>

          {/* Slogan Banner with National Tricolor Wave */}
          <div className="hidden xl:flex flex-col items-end pr-6">
            <span
              className="text-xs font-semibold text-slate-600 tracking-wide italic font-serif"
              style={{ fontFamily: 'Playfair Display, Georgia, serif' }}
            >
              Quality Education for a Brighter Future
            </span>
            <TricolorRibbonWave width={140} height={16} className="mt-0.5" />
          </div>
        </div>

        {/* Right Controls: Date Range, Search, Notification Bell, User Avatar */}
        <div className="flex items-center gap-2.5 shrink-0 self-end md:self-center">
          
          {/* Date Range Selector Pill */}
          <div className="relative">
            <button
              onClick={() => setShowDatePicker(!showDatePicker)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-50 hover:bg-slate-100 border border-slate-200 text-xs font-medium text-slate-700 shadow-2xs transition cursor-pointer"
            >
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>{dateRange}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {showDatePicker && (
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-xl shadow-lg border border-slate-200 p-2 z-50 text-xs">
                <div className="font-semibold text-slate-700 px-2 py-1 text-[11px] uppercase tracking-wider text-slate-400">
                  Select Evaluation Period
                </div>
                {[
                  '01 Oct 2026 - 31 Oct 2026 (Live)',
                  '01 Jul 2026 - 30 Sep 2026 (Q3)',
                  '01 Apr 2026 - 30 Jun 2026 (Q2)',
                  '01 Jan 2019 - 30 Mar 2019 (Historical)',
                ].map((item) => (
                  <button
                    key={item}
                    onClick={() => {
                      setDateRange(item);
                      setShowDatePicker(false);
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-medium transition ${
                      dateRange === item
                        ? 'bg-[#EBF3FE] text-[#1E3A8A] font-bold'
                        : 'text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Search Icon Button */}
          <button
            aria-label="Search cases"
            className="w-9 h-9 rounded-full bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 hover:text-slate-900 transition shadow-2xs cursor-pointer"
          >
            <Search className="w-4 h-4" />
          </button>

          {/* Notifications Button with Red Counter Badge */}
          <div className="relative">
            <button
              aria-label="Alerts and notifications"
              className="w-9 h-9 rounded-full bg-slate-50 hover:bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 hover:text-slate-900 transition shadow-2xs cursor-pointer"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute -top-0.5 -right-0.5 w-4 h-4 rounded-full bg-[#DC2626] text-white text-[9px] font-bold flex items-center justify-center ring-2 ring-white">
                3
              </span>
            </button>
          </div>

          {/* User Profile Avatar with Role Switcher Dropdown */}
          <div className="relative pl-1 border-l border-slate-200">
            <button
              onClick={() => setShowRoleMenu(!showRoleMenu)}
              className="flex items-center gap-2 group cursor-pointer focus:outline-none"
            >
              <div className="relative">
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-sky-500 to-[#1E3A8A] p-0.5 shadow-xs">
                  <div className="w-full h-full rounded-full bg-white flex items-center justify-center overflow-hidden font-bold text-xs text-[#1E3A8A]">
                    {user?.name ? user.name.slice(0, 2).toUpperCase() : 'JD'}
                  </div>
                </div>
                <span className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full bg-[#16A34A] ring-2 ring-white" />
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600 transition" />
            </button>

            {/* Quick Role Switcher Menu */}
            {showRoleMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 p-2 z-50 text-xs animate-in fade-in slide-in-from-top-1">
                <div className="px-2.5 py-2 border-b border-slate-100">
                  <div className="font-bold text-slate-900 text-sm">
                    {user?.name}
                  </div>
                  <div className="text-[11px] text-sky-700 font-semibold flex items-center gap-1 mt-0.5">
                    <Shield className="w-3 h-3 text-sky-600" />
                    {user?.bureau} Bureau • {user?.role.toUpperCase()}
                  </div>
                </div>

                <div className="py-1">
                  <div className="text-[10px] uppercase font-bold tracking-wider text-slate-400 px-2 py-1">
                    Switch Evaluator Role (SIH Demo)
                  </div>
                  {[
                    { id: 'officer', label: 'Regulation Bureau (RB) Officer', desc: 'Case desk' },
                    { id: 'pgrcOfficer', label: 'PGRC Grievance Cell Officer', desc: 'Student issues' },
                    { id: 'senior', label: 'Senior Bureau Head (Advisor)', desc: 'Inter-bureau' },
                    { id: 'authority', label: 'Chairman AICTE (Apex Authority)', desc: 'Full authority' },
                  ].map((role) => {
                    const isSelected =
                      (role.id === 'officer' && user?.role === 'officer' && user?.bureau === 'RB') ||
                      (role.id === 'pgrcOfficer' && user?.role === 'officer' && user?.bureau === 'PGRC') ||
                      (role.id === 'senior' && user?.role === 'senior') ||
                      (role.id === 'authority' && user?.role === 'authority');

                    return (
                      <button
                        key={role.id}
                        onClick={() => {
                          switchUser(role.id as any);
                          setShowRoleMenu(false);
                        }}
                        className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center justify-between text-xs transition cursor-pointer ${
                          isSelected
                            ? 'bg-[#EBF3FE] text-[#1E3A8A] font-bold'
                            : 'text-slate-700 hover:bg-slate-50'
                        }`}
                      >
                        <div>
                          <div>{role.label}</div>
                          <span className="text-[10px] text-slate-400 block font-normal">
                            {role.desc}
                          </span>
                        </div>
                        {isSelected && <Check className="w-3.5 h-3.5 text-[#1E3A8A]" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </header>
  );
};
