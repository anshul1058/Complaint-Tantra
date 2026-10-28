'use client';

import React from 'react';
import { Sparkles, ArrowUp } from 'lucide-react';
import { DashboardSummary } from '@/lib/types';

interface StatusSummaryCardProps {
  summary?: DashboardSummary;
}

export const StatusSummaryCard: React.FC<StatusSummaryCardProps> = ({ summary }) => {
  const total = summary?.total || 1420;
  const disposed = summary?.disposed || 357;
  const overdue = summary?.overdue || 48;

  const disposalRate = ((disposed / total) * 100).toFixed(1);
  const slaCompliance = (((total - overdue) / total) * 100).toFixed(1);

  return (
    <div className="bg-white/95 backdrop-blur-xs rounded-2xl p-5 border border-slate-200/80 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)] relative">
      {/* Header */}
      <div className="flex items-center justify-between pb-3">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-4 h-4 text-[#0EA5E9]" />
          <h3 className="font-extrabold text-[#1E3A8A] text-sm md:text-base tracking-tight">
            Status Summary
          </h3>
        </div>
        <Sparkles className="w-3.5 h-3.5 text-[#0EA5E9] opacity-75" />
      </div>

      {/* Closed Value Stat with Sparkline Wave */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-100">
        <div>
          <div className="text-xs font-semibold text-slate-500">
            Disposed / Closed Cases
          </div>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-3xl font-black text-[#1E3A8A] tracking-tight">
              {disposed.toLocaleString('en-IN')}
            </span>
            <span className="inline-flex items-center text-xs font-bold text-[#16A34A] gap-0.5">
              <ArrowUp className="w-3 h-3 stroke-[3]" />
              +12.5%
            </span>
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5">
            Resolution rate across all active bureaus
          </p>
        </div>

        {/* Mini Smooth Sparkline Curve SVG */}
        <div className="w-32 h-14">
          <svg viewBox="0 0 120 45" className="w-full h-full overflow-visible">
            <defs>
              <linearGradient id="miniSparkGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#0EA5E9" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#0EA5E9" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <path
              d="M 5 35 C 25 32, 40 28, 55 30 C 70 32, 85 10, 100 18 C 108 22, 112 12, 116 8 L 116 45 L 5 45 Z"
              fill="url(#miniSparkGrad)"
            />
            <path
              d="M 5 35 C 25 32, 40 28, 55 30 C 70 32, 85 10, 100 18 C 108 22, 112 12, 116 8"
              fill="none"
              stroke="#0284C7"
              strokeWidth="2.5"
              strokeLinecap="round"
            />
            <circle cx="116" cy="8" r="3.5" fill="#0284C7" />
          </svg>
        </div>
      </div>

      {/* Dual Donut Progress Rings */}
      <div className="grid grid-cols-2 gap-4 mt-5 pt-4 border-t border-slate-100">
        
        {/* Donut 1: Total Disposal Rate */}
        <div className="flex items-center gap-3">
          <div className="relative w-12 h-12 shrink-0">
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              <circle
                cx="18"
                cy="18"
                r="14"
                fill="none"
                stroke="#E2E8F0"
                strokeWidth="3.5"
              />
              <circle
                cx="18"
                cy="18"
                r="14"
                fill="none"
                stroke="#0EA5E9"
                strokeWidth="3.5"
                strokeDasharray="88"
                strokeDashoffset={88 - (88 * parseFloat(disposalRate)) / 100}
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500">
              Disposal Rate
            </div>
            <div className="text-base font-extrabold text-[#1E3A8A] tracking-tight">
              {disposalRate}%
            </div>
          </div>
        </div>

        {/* Donut 2: SLA Compliance Rate */}
        <div className="flex items-center gap-3">
          <div className="relative w-12 h-12 shrink-0">
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              <circle
                cx="18"
                cy="18"
                r="14"
                fill="none"
                stroke="#E2E8F0"
                strokeWidth="3.5"
              />
              <circle
                cx="18"
                cy="18"
                r="14"
                fill="none"
                stroke="#16A34A"
                strokeWidth="3.5"
                strokeDasharray="88"
                strokeDashoffset={88 - (88 * parseFloat(slaCompliance)) / 100}
                strokeLinecap="round"
              />
            </svg>
          </div>
          <div>
            <div className="text-[11px] font-semibold text-slate-500">
              SLA Compliance
            </div>
            <div className="text-base font-extrabold text-[#1E3A8A] tracking-tight">
              {slaCompliance}%
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};
