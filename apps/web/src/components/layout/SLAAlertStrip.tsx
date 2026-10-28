'use client';

import React from 'react';
import Link from 'next/link';
import { AlertTriangle, ShieldAlert, GitMerge, Clock, ArrowRight } from 'lucide-react';

interface SLAAlertStripProps {
  overdueCount?: number;
  safetyCount?: number;
  overlapCount?: number;
}

export const SLAAlertStrip: React.FC<SLAAlertStripProps> = ({
  overdueCount = 48,
  safetyCount = 6,
  overlapCount = 12,
}) => {
  return (
    <div className="w-full bg-[#FEF2F2] border-b border-red-200/80 text-slate-800 px-4 py-1.5 text-xs">
      <div className="max-w-[1720px] mx-auto flex flex-col md:flex-row items-center justify-between gap-2">
        <div className="flex items-center flex-wrap gap-2.5">
          <div className="flex items-center gap-1.5 font-bold uppercase tracking-wider bg-[#DC2626] text-white px-2 py-0.5 rounded-full text-[10px] shadow-2xs">
            <AlertTriangle className="w-3 h-3 text-amber-200 animate-pulse" />
            Active Alert Stream
          </div>

          <div className="flex items-center gap-3 text-xs font-semibold text-slate-700">
            <span className="flex items-center gap-1">
              <ShieldAlert className="w-3.5 h-3.5 text-[#DC2626]" />
              Safety Flags:{' '}
              <strong className="text-[#DC2626] bg-red-100/80 px-1.5 py-0.2 rounded font-extrabold text-[11px]">
                {safetyCount} Urgent
              </strong>
            </span>

            <span className="text-slate-300">•</span>

            <span className="flex items-center gap-1">
              <GitMerge className="w-3.5 h-3.5 text-purple-600" />
              T1 Inter-Bureau Overlaps:{' '}
              <strong className="text-purple-700 bg-purple-100/80 px-1.5 py-0.2 rounded font-extrabold text-[11px]">
                {overlapCount} Cases
              </strong>
            </span>

            <span className="text-slate-300">•</span>

            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-[#F59E0B]" />
              SLA Overdue:{' '}
              <strong className="text-amber-800 bg-amber-100/80 px-1.5 py-0.2 rounded font-extrabold text-[11px]">
                {overdueCount} Pending
              </strong>
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/overlaps"
            className="flex items-center gap-1 text-[11px] font-bold text-[#1E3A8A] hover:text-sky-700 hover:underline transition"
          >
            Review Overlap Coordination Room &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
};
