'use client';

import React from 'react';
import { DashboardSummary } from '@/lib/types';
import {
  FileText,
  CheckCircle2,
  RefreshCcw,
  Clock,
  AlertTriangle,
  ShieldAlert,
  ArrowUp,
  ArrowDown,
  Sparkles,
} from 'lucide-react';
import Link from 'next/link';

interface KPICardsProps {
  summary: DashboardSummary;
}

export const KPICards: React.FC<KPICardsProps> = ({ summary }) => {
  const disposalRate = summary.total > 0
    ? ((summary.disposed / summary.total) * 100).toFixed(1)
    : '82.4';

  const cards = [
    {
      label: 'Total Grievances',
      sublabel: 'All AICTE Bureaus',
      value: summary.total.toLocaleString('en-IN'),
      icon: FileText,
      iconBg: 'bg-[#E0F2FE]',
      iconColor: 'text-[#0284C7]',
      trend: '+12.4%',
      trendColor: 'text-[#16A34A]',
      trendIcon: ArrowUp,
      href: '/cases',
    },
    {
      label: 'Disposed & Resolved',
      sublabel: `${disposalRate}% Disposal Rate`,
      value: summary.disposed.toLocaleString('en-IN'),
      icon: CheckCircle2,
      iconBg: 'bg-[#DCFCE7]',
      iconColor: 'text-[#16A34A]',
      trend: '+4.2%',
      trendColor: 'text-[#16A34A]',
      trendIcon: ArrowUp,
      href: '/cases?status=Disposed',
    },
    {
      label: 'Under Active Process',
      sublabel: 'Active Bureau Scrutiny',
      value: summary.under_process.toLocaleString('en-IN'),
      icon: RefreshCcw,
      iconBg: 'bg-[#F3E8FF]',
      iconColor: 'text-[#9333EA]',
      trend: '-1.8%',
      trendColor: 'text-[#1E3A8A]',
      trendIcon: ArrowDown,
      href: '/cases?status=Under Process',
    },
    {
      label: 'Pending Initial Triage',
      sublabel: 'Unallocated Intake',
      value: summary.pending.toLocaleString('en-IN'),
      icon: Clock,
      iconBg: 'bg-[#E0F2FE]',
      iconColor: 'text-[#0284C7]',
      trend: '-3.5%',
      trendColor: 'text-[#16A34A]',
      trendIcon: ArrowDown,
      href: '/queue',
    },
    {
      label: 'SLA Overdue',
      sublabel: 'Turnaround Exceeded',
      value: summary.overdue.toLocaleString('en-IN'),
      icon: AlertTriangle,
      iconBg: 'bg-[#FEE2E2]',
      iconColor: 'text-[#DC2626]',
      trend: '+2.1%',
      trendColor: 'text-[#DC2626]',
      trendIcon: ArrowUp,
      isWarning: true,
      href: '/cases',
    },
    {
      label: 'Safety & Distress Flags',
      sublabel: 'Ragging / High Distress',
      value: summary.safety_flagged.toLocaleString('en-IN'),
      icon: ShieldAlert,
      iconBg: 'bg-[#FFE4E6]',
      iconColor: 'text-[#E11D48]',
      trend: 'Urgent',
      trendColor: 'text-[#E11D48]',
      trendIcon: ArrowUp,
      isDanger: true,
      href: '/queue',
    },
  ];

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5 mb-6">
      {cards.map((card, i) => {
        const Icon = card.icon;
        const TrendIcon = card.trendIcon;

        return (
          <Link
            key={i}
            href={card.href}
            className={`group relative bg-white/95 backdrop-blur-xs rounded-2xl p-4 border border-slate-200/80 shadow-[0_2px_10px_-2px_rgba(30,58,138,0.04)] hover:shadow-[0_8px_20px_-4px_rgba(30,58,138,0.08)] hover:border-sky-300 transition-all duration-200 cursor-pointer flex flex-col justify-between ${
              card.isDanger
                ? 'hover:border-rose-300'
                : card.isWarning
                ? 'hover:border-amber-300'
                : ''
            }`}
          >
            <div>
              {/* Top row: Circle Icon + Sparkle Star */}
              <div className="flex items-center justify-between mb-2.5">
                <div
                  className={`w-9 h-9 rounded-full ${card.iconBg} ${card.iconColor} flex items-center justify-center transition-transform group-hover:scale-105`}
                >
                  <Icon className="w-4 h-4 stroke-[2.2]" />
                </div>
                <Sparkles className="w-3.5 h-3.5 text-[#0EA5E9] opacity-75 group-hover:opacity-100 transition-opacity" />
              </div>

              {/* Label */}
              <div className="text-xs font-semibold text-slate-700 leading-tight">
                {card.label}
              </div>

              {/* Value */}
              <div className="text-xl lg:text-2xl font-extrabold text-[#0F172A] tracking-tight mt-1">
                {card.value}
              </div>
            </div>

            {/* Bottom: Trend Indicator & Context */}
            <div className="mt-2 pt-1.5 border-t border-slate-100/80 flex items-center justify-between text-xs">
              <span className={`inline-flex items-center gap-0.5 font-bold text-[11px] ${card.trendColor}`}>
                <TrendIcon className="w-3 h-3 stroke-[2.5]" />
                {card.trend}
              </span>
              <span className="text-[10px] text-slate-400 truncate font-medium">
                {card.sublabel}
              </span>
            </div>
          </Link>
        );
      })}
    </div>
  );
};
