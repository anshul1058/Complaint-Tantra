'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppLayout } from '@/components/layout/AppLayout';
import { getPriorityQueue } from '@/lib/api/client';
import { Case } from '@/lib/types';
import { mockCases } from '@/lib/mock/data';
import { formatDate } from '@/lib/utils';
import {
  ListOrdered,
  Sparkles,
  ShieldAlert,
  GitMerge,
  ArrowRight,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export default function PriorityQueuePage() {
  const [cases, setCases] = useState<Case[]>(mockCases);
  const [bureauFilter, setBureauFilter] = useState('ALL');
  const [expandedCaseId, setExpandedCaseId] = useState<string | null>('case-001');

  useEffect(() => {
    getPriorityQueue().then(setCases).catch(() => setCases(mockCases));
  }, []);

  const filteredCases = cases.filter((c) => {
    if (bureauFilter !== 'ALL' && c.assigned_bureau !== bureauFilter) return false;
    return true;
  });

  const sortedCases = [...filteredCases].sort(
    (a, b) => b.priority_score - a.priority_score
  );

  return (
    <AppLayout
      pageTitle="AI Priority Scored Queue"
      hindiTitle="एआई प्राथमिकता क्रमबद्ध कतार"
      actionButton={
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-500 font-medium">Filter Bureau:</span>
          <select
            value={bureauFilter}
            onChange={(e) => setBureauFilter(e.target.value)}
            className="text-xs font-semibold px-2.5 py-1.5 rounded border border-slate-300 bg-white text-slate-700 focus:outline-none"
          >
            <option value="ALL">All AICTE Bureaus</option>
            <option value="RB">RB (Regulation Bureau)</option>
            <option value="PGRC">PGRC (Grievance Cell)</option>
            <option value="Approval">Approval Bureau</option>
          </select>
        </div>
      }
    >
      {/* Informational Triage Banner */}
      <div className="bg-gradient-to-r from-[#1E3A8A] via-[#1e40af] to-[#0284C7] text-white p-5 rounded-2xl shadow-sm mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-white/10 rounded-xl text-sky-200">
            <ListOrdered className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-extrabold text-sm md:text-base tracking-wide flex items-center gap-2">
              Explainable Triage & Priority Ordering Engine
              <span className="bg-[#0EA5E9] text-white text-[10px] px-2 py-0.5 rounded-full font-extrabold uppercase">
                Deterministic Scoring
              </span>
            </h3>
            <p className="text-sky-100 mt-1">
              Ranked dynamically by: Criticality (35%) + Emotion Distress (20%) + SLA Urgency (25%) + Overlap (10%) + Risk Index (10%).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 font-semibold">
          <span className="bg-emerald-500/20 text-emerald-200 px-3 py-1 rounded-full border border-emerald-500/30">
            Human-in-the-Loop Active
          </span>
        </div>
      </div>

      {/* Ranked Queue Cards List */}
      <div className="space-y-4">
        {sortedCases.map((c, index) => {
          const isExpanded = expandedCaseId === c.id;
          const score = c.priority_score;

          return (
            <div
              key={c.id}
              className={`bg-white/95 rounded-2xl border transition-all duration-200 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)] hover:shadow-md ${
                c.safety_flag
                  ? 'border-rose-400 border-l-6'
                  : score >= 80
                  ? 'border-slate-200 border-l-6 border-l-[#DC2626]'
                  : score >= 60
                  ? 'border-slate-200 border-l-6 border-l-[#F59E0B]'
                  : 'border-slate-200 border-l-6 border-l-[#16A34A]'
              }`}
            >
              <div className="p-5">
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
                  
                  {/* Left: Rank Badge + Score Circle + Case Identifiers */}
                  <div className="flex items-center gap-3.5">
                    {/* Rank Badge */}
                    <div className="flex flex-col items-center justify-center w-11 h-11 rounded-xl bg-slate-50 text-slate-700 font-extrabold text-sm border border-slate-200">
                      <span className="text-[9px] uppercase font-semibold text-slate-400">RANK</span>
                      #{index + 1}
                    </div>

                    {/* Priority Score Display */}
                    <div className="flex flex-col items-center justify-center px-3.5 py-1.5 rounded-xl bg-[#1E3A8A] text-white shadow-2xs">
                      <span className="text-[9px] uppercase text-sky-300 font-bold tracking-wider">
                        SCORE
                      </span>
                      <span className="text-base font-extrabold text-white">
                        {score.toFixed(1)}
                      </span>
                    </div>

                    <div>
                      <div className="flex items-center flex-wrap gap-2">
                        <span className="font-mono text-xs font-bold text-[#1E3A8A] bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-200">
                          {c.case_no}
                        </span>
                        <span className="text-xs font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-800">
                          {c.assigned_bureau}
                        </span>
                        <span
                          className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full ${
                            c.criticality === 'C1'
                              ? 'bg-red-100 text-red-900 border border-red-300'
                              : c.criticality === 'C2'
                              ? 'bg-amber-100 text-amber-900 border border-amber-300'
                              : 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                          }`}
                        >
                          {c.criticality}
                        </span>

                        {c.safety_flag && (
                          <span className="flex items-center gap-1 text-[11px] font-extrabold px-2 py-0.5 rounded bg-rose-600 text-white animate-pulse">
                            <ShieldAlert className="w-3.5 h-3.5" />
                            SAFETY ESCALATION
                          </span>
                        )}

                        {c.overlap_count && c.overlap_count > 0 ? (
                          <span className="flex items-center gap-1 text-[11px] font-bold px-2 py-0.5 rounded bg-purple-100 text-purple-900 border border-purple-300">
                            <GitMerge className="w-3 h-3 text-purple-700" />
                            {c.overlap_count} Cross-Bureau Overlap
                          </span>
                        ) : null}
                      </div>

                      <h4 className="font-bold text-slate-900 text-sm md:text-base mt-1">
                        {c.raw_institution}
                      </h4>
                      <p className="text-xs font-medium text-slate-600">
                        {c.category} • <span className="text-slate-400">Lodged: {formatDate(c.received_at)}</span>
                      </p>
                    </div>
                  </div>

                  {/* Right: Actions */}
                  <div className="flex items-center gap-2 self-end md:self-center">
                    <button
                      onClick={() => setExpandedCaseId(isExpanded ? null : c.id)}
                      className="flex items-center gap-1 px-3 py-1.5 rounded text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition cursor-pointer"
                    >
                      {isExpanded ? (
                        <>
                          Hide Why #{index + 1} <ChevronUp className="w-3.5 h-3.5" />
                        </>
                      ) : (
                        <>
                          Why #{index + 1}? <ChevronDown className="w-3.5 h-3.5" />
                        </>
                      )}
                    </button>

                    <Link
                      href={`/cases/${c.id}`}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded-full bg-[#1E3A8A] hover:bg-[#1e40af] text-white text-xs font-bold shadow-xs transition"
                    >
                      Open Case
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>

                {/* AI Summary Snip */}
                <p className="text-xs text-slate-600 mt-3 pt-2.5 border-t border-slate-100 line-clamp-2">
                  <strong className="text-slate-800">AI Brief:</strong> {c.ai_summary}
                </p>

                {/* Expanded "Why #1" Panel */}
                {isExpanded && (
                  <div className="mt-4 pt-3 border-t border-slate-200 bg-amber-50/70 p-4 rounded-lg border border-amber-200">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-extrabold uppercase text-amber-900 flex items-center gap-1.5">
                        <Sparkles className="w-4 h-4 text-amber-600" />
                        Scoring Rationales for #{index + 1} Ranking:
                      </span>
                      <span className="text-[11px] font-semibold text-amber-800">
                        Emotion Signal: {c.emotion_label} ({c.emotion_intensity * 100}%)
                      </span>
                    </div>

                    <ul className="space-y-1.5">
                      {c.priority_reasons.reasons.map((r, ri) => (
                        <li
                          key={ri}
                          className="text-xs text-slate-700 flex items-start gap-2"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5 text-amber-600 mt-0.5 shrink-0" />
                          <span>{r}</span>
                        </li>
                      ))}
                    </ul>

                    {c.safety_flag && c.safety_flag_reason && (
                      <div className="mt-2.5 p-2 bg-rose-100/80 border border-rose-300 rounded text-xs text-rose-900 font-semibold flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-rose-700 shrink-0" />
                        <span>Safety Intervention Required: {c.safety_flag_reason}</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </AppLayout>
  );
}
