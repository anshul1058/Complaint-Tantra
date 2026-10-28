'use client';

import React from 'react';
import Link from 'next/link';
import { GitMerge, ArrowRight, ShieldCheck } from 'lucide-react';
import { OverlapTier } from '@/lib/types';

interface OverlapBannerProps {
  caseNo: string;
  overlapCount: number;
  tier?: OverlapTier;
  confidence?: number;
  relatedCaseNo?: string;
  relatedBureau?: string;
}

export const OverlapBanner: React.FC<OverlapBannerProps> = ({
  overlapCount,
  tier = 'T1',
  confidence = 0.93,
  relatedCaseNo = 'AICTE/PGRC/2026/0412',
  relatedBureau = 'PGRC',
}) => {
  if (overlapCount === 0) return null;

  return (
    <div className="w-full bg-gradient-to-r from-purple-900 via-indigo-900 to-slate-900 text-white rounded-lg p-4 mb-5 shadow-md border border-purple-500/40">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div className="p-2.5 bg-purple-500/20 rounded-lg border border-purple-400/30 text-purple-300 mt-0.5">
            <GitMerge className="w-6 h-6 animate-pulse" />
          </div>

          <div>
            <div className="flex items-center flex-wrap gap-2">
              <span className="font-extrabold text-sm md:text-base tracking-wide text-amber-300">
                POTENTIAL OVERLAPPING CASES — COORDINATION REQUIRED
              </span>
              <span className="px-2 py-0.5 bg-rose-600 text-white text-xs font-bold rounded">
                Tier {tier} Overlap
              </span>
              <span className="px-2 py-0.5 bg-purple-600/40 text-purple-200 text-xs font-semibold rounded border border-purple-400/40">
                {(confidence * 100).toFixed(0)}% Confidence
              </span>
            </div>

            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              This institution has <strong>{overlapCount} active cross-bureau case(s)</strong>.
              Detected with <strong>{relatedBureau}</strong> (Case No: {relatedCaseNo}). Coordinated notice recommended before issuing unilateral sanction.
            </p>

            <div className="flex items-center gap-4 mt-2 text-[11px] text-purple-200 font-medium">
              <span className="flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                Permanent ID Match: 1-281459201
              </span>
              <span>•</span>
              <span>Text Cosine Sim: 0.78</span>
              <span>•</span>
              <span>Temporal Window: 3-day overlap</span>
            </div>
          </div>
        </div>

        <Link
          href="/overlaps"
          className="self-end md:self-center shrink-0 flex items-center gap-1.5 px-4 py-2 rounded-md bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold text-xs shadow-md transition"
        >
          Coordination Room
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};
