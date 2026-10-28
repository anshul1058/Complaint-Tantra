'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import {
  LayoutDashboard,
  ListOrdered,
  FolderSearch,
  GitMerge,
  Building2,
  BarChart3,
  LogOut,
  ShieldCheck,
} from 'lucide-react';
import { RashtrapatiBhavanSketch } from '@/components/layout/GovWatermark';
import { TricolorRibbonWave } from '@/components/layout/TricolorRibbon';

interface SidebarProps {
  className?: string;
}

export const AppSidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const pathname = usePathname();
  const { user, logout, hasRole } = useAuth();

  const coreNav = [
    {
      label: 'Command Dashboard',
      hindi: 'कमांड डैशबोर्ड',
      href: '/',
      icon: LayoutDashboard,
      roles: ['officer', 'regional', 'senior', 'authority', 'admin'] as const,
    },
    {
      label: 'Priority Queue',
      hindi: 'प्राथमिकता कतार',
      href: '/queue',
      icon: ListOrdered,
      badge: 'Scored',
      roles: ['officer', 'regional', 'senior', 'authority', 'admin'] as const,
    },
    {
      label: 'Complaint Cases',
      hindi: 'शिकायत मामले',
      href: '/cases',
      icon: FolderSearch,
      roles: ['officer', 'regional', 'senior', 'authority', 'admin'] as const,
    },
    {
      label: 'Overlap Room',
      hindi: 'समन्वय कक्ष (T1-T3)',
      href: '/overlaps',
      icon: GitMerge,
      badge: 'T1 Active',
      roles: ['officer', 'regional', 'senior', 'authority', 'admin'] as const,
    },
  ];

  const intelligenceNav = [
    {
      label: 'Institution 360°',
      hindi: 'संस्थान रूपरेखा',
      href: '/institutions/inst-001',
      icon: Building2,
      roles: ['officer', 'regional', 'senior', 'authority', 'admin'] as const,
    },
    {
      label: 'Reports & Analytics',
      hindi: 'रिपोर्ट और विश्लेषण',
      href: '/reports',
      icon: BarChart3,
      roles: ['senior', 'authority', 'admin'] as const, // Senior+ only per frontend-guide.md
    },
  ];

  return (
    <aside
      className={`w-64 bg-white border-r border-slate-200/80 flex flex-col justify-between shadow-[1px_0_3px_rgba(30,58,138,0.02)] min-h-[calc(100vh-68px)] relative select-none ${className}`}
    >
      {/* Scrollable Navigation Area */}
      <div className="p-3.5 space-y-5 overflow-y-auto z-10">
        
        {/* Section 1: CORE TRIAGE WORKFLOWS */}
        <div>
          <div className="px-3 pb-2 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            AICTE Triage & Cases
          </div>
          <nav className="space-y-1">
            {coreNav.map((item) => {
              const isAuthorized = hasRole([...item.roles]);
              if (!isAuthorized) return null;

              const isActive =
                item.href === '/'
                  ? pathname === '/'
                  : pathname.startsWith(item.href);

              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                    isActive
                      ? 'bg-[#EBF3FE] text-[#1E3A8A] font-semibold shadow-2xs'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={`w-4 h-4 transition-colors ${
                        isActive ? 'text-[#1E3A8A]' : 'text-slate-400 group-hover:text-slate-600'
                      }`}
                    />
                    <div className="flex flex-col">
                      <span className="leading-tight">{item.label}</span>
                      <span className="text-[10px] text-slate-400 group-hover:text-slate-500">
                        {item.hindi}
                      </span>
                    </div>
                  </div>

                  {item.badge && (
                    <span
                      className={`text-[9.5px] font-bold px-1.5 py-0.5 rounded-full ${
                        item.badge.includes('T1')
                          ? 'bg-purple-100 text-purple-800 border border-purple-200'
                          : 'bg-sky-100 text-sky-800 border border-sky-200'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Section 2: INTELLIGENCE & MASTERS */}
        <div>
          <div className="px-3 pb-2 text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            Intelligence & Reports
          </div>
          <nav className="space-y-1">
            {intelligenceNav.map((item) => {
              const isAuthorized = hasRole([...item.roles]);
              if (!isAuthorized) return null;

              const isActive =
                item.href === '/reports'
                  ? pathname.startsWith('/reports')
                  : pathname.startsWith('/institutions');

              const Icon = item.icon;

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                    isActive
                      ? 'bg-[#EBF3FE] text-[#1E3A8A] font-semibold shadow-2xs'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={`w-4 h-4 transition-colors ${
                        isActive ? 'text-[#1E3A8A]' : 'text-slate-400 group-hover:text-slate-600'
                      }`}
                    />
                    <div className="flex flex-col">
                      <span className="leading-tight">{item.label}</span>
                      <span className="text-[10px] text-slate-400 group-hover:text-slate-500">
                        {item.hindi}
                      </span>
                    </div>
                  </div>
                </Link>
              );
            })}
          </nav>
        </div>

      </div>

      {/* Bottom Area: Parliament sketch, Tricolor Wave, and Mottos */}
      <div className="relative pt-6 pb-4 px-4 border-t border-slate-100 bg-gradient-to-b from-white to-sky-50/40 overflow-hidden shrink-0">
        {/* Subtle Parliament Sketch Watermark in Bottom Left */}
        <div className="absolute -bottom-2 -left-8 w-60 opacity-30 pointer-events-none">
          <RashtrapatiBhavanSketch opacity={0.25} />
        </div>

        {/* Tricolor Wave & AICTE Pillars */}
        <div className="relative z-10 flex flex-col items-center text-center">
          <TricolorRibbonWave width={110} height={14} className="mb-2" />
          <div className="text-[10px] font-bold text-[#1E3A8A] tracking-wider uppercase">
            Skilling • Regulating • Transforming
          </div>
          <div className="text-[9px] text-slate-400 mt-0.5">
            AICTE Central Grievance Matrix
          </div>
        </div>

        {/* Active Officer Session Bar */}
        <div className="relative z-10 mt-3 pt-2.5 border-t border-slate-200/60 flex items-center justify-between text-xs">
          <div className="text-left truncate max-w-[150px]">
            <span className="text-[11px] font-bold text-slate-800 block truncate flex items-center gap-1">
              <ShieldCheck className="w-3 h-3 text-[#1E3A8A] shrink-0 inline" />
              {user?.name || 'Officer'}
            </span>
            <span className="text-[10px] text-slate-400">
              {user?.bureau} ({user?.role?.toUpperCase()})
            </span>
          </div>

          <button
            onClick={logout}
            title="Sign Out"
            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
