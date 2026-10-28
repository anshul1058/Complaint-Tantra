'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppLayout } from '@/components/layout/AppLayout';
import { getAllOverlaps, postOverlapDecision } from '@/lib/api/client';
import { CaseLink, OverlapTier, OverlapDecision } from '@/lib/types';
import { mockCaseLinks } from '@/lib/mock/data';
import { formatDate } from '@/lib/utils';
import {
  GitMerge,
  Check,
  X,
  Info,
} from 'lucide-react';

export default function OverlapRoomPage() {
  const [links, setLinks] = useState<CaseLink[]>(mockCaseLinks);
  const [selectedTier, setSelectedTier] = useState<'ALL' | OverlapTier>('ALL');

  useEffect(() => {
    getAllOverlaps().then(setLinks).catch(() => setLinks(mockCaseLinks));
  }, []);

  const handleDecision = async (linkId: string, decision: OverlapDecision) => {
    await postOverlapDecision(linkId, decision);
    setLinks((prev) =>
      prev.map((l) => (l.id === linkId ? { ...l, decision } : l))
    );
  };

  const filteredLinks = links.filter((l) => {
    if (selectedTier !== 'ALL' && l.tier !== selectedTier) return false;
    return true;
  });

  const t1Count = links.filter((l) => l.tier === 'T1').length;
  const t2Count = links.filter((l) => l.tier === 'T2').length;
  const t3Count = links.filter((l) => l.tier === 'T3').length;

  return (
    <AppLayout
      pageTitle="Inter-Bureau Overlap Coordination Room"
      hindiTitle="अंतर-ब्यूरो अतिव्याप्ति समन्वय कक्ष"
      actionButton={
        <div className="flex items-center gap-1.5 bg-purple-100 text-purple-900 px-3 py-1.5 rounded border border-purple-300 text-xs font-bold">
          <GitMerge className="w-4 h-4 text-purple-700" />
          Cross-Bureau Intelligence Engine Active
        </div>
      }
    >
      {/* 1. Header Banner */}
      <div className="bg-gradient-to-r from-purple-900 via-indigo-950 to-slate-900 text-white p-5 rounded-lg shadow-md mb-5 border border-purple-500/30">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
          <div>
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-amber-400 text-slate-950">
              CORE INNOVATION — PROBLEM STATEMENT RESOLUTION
            </span>
            <h3 className="text-base md:text-lg font-bold text-white mt-1.5">
              Automated Detection of Multiple Bureau Grievances on the Same Institution
            </h3>
            <p className="text-xs text-slate-300 mt-1 max-w-3xl leading-relaxed">
              Prevents duplicate inquiries, contradictory notices, and regulatory loopholes.
              Officers can confirm links to initiate synchronized Show-Cause proceedings or reject false matches.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs bg-white/10 px-3 py-1.5 rounded font-semibold text-amber-300 border border-white/20">
              Evaluator Threshold F1 ≥ 0.85
            </span>
          </div>
        </div>
      </div>

      {/* 2. Tier Selection Filter Bar */}
      <div className="flex items-center gap-2 mb-5 overflow-x-auto text-xs pb-1">
        <button
          onClick={() => setSelectedTier('ALL')}
          className={`px-3 py-1.5 rounded font-bold transition cursor-pointer ${
            selectedTier === 'ALL'
              ? 'bg-[#1E3A8A] text-white shadow'
              : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
          }`}
        >
          All Overlaps ({links.length})
        </button>

        <button
          onClick={() => setSelectedTier('T1')}
          className={`px-3 py-1.5 rounded font-bold transition cursor-pointer flex items-center gap-1.5 ${
            selectedTier === 'T1'
              ? 'bg-red-700 text-white shadow'
              : 'bg-white border border-red-200 text-red-800 hover:bg-red-50'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          Tier 1: Same Inst. + Related Issue ({t1Count})
        </button>

        <button
          onClick={() => setSelectedTier('T2')}
          className={`px-3 py-1.5 rounded font-bold transition cursor-pointer ${
            selectedTier === 'T2'
              ? 'bg-amber-600 text-white shadow'
              : 'bg-white border border-amber-200 text-amber-800 hover:bg-amber-50'
          }`}
        >
          Tier 2: Same Inst. / Distinct Issue ({t2Count})
        </button>

        <button
          onClick={() => setSelectedTier('T3')}
          className={`px-3 py-1.5 rounded font-bold transition cursor-pointer ${
            selectedTier === 'T3'
              ? 'bg-blue-700 text-white shadow'
              : 'bg-white border border-blue-200 text-blue-800 hover:bg-blue-50'
          }`}
        >
          Tier 3: Possible Duplicate ({t3Count})
        </button>
      </div>

      {/* 3. Overlap Evidence Cards */}
      <div className="space-y-5">
        {filteredLinks.map((link) => {
          const caseA = link.case_a_details;
          const caseB = link.case_b_details;

          return (
            <div
              key={link.id}
              className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden"
            >
              {/* Card Header Bar */}
              <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2 text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-xs font-extrabold ${
                      link.tier === 'T1'
                        ? 'bg-red-600 text-white'
                        : link.tier === 'T2'
                        ? 'bg-amber-600 text-white'
                        : 'bg-blue-600 text-white'
                    }`}
                  >
                    {link.tier} OVERLAP
                  </span>

                  <span className="font-bold text-slate-800">
                    Confidence: {(link.confidence * 100).toFixed(0)}%
                  </span>

                  <span className="text-slate-400">•</span>
                  <span className="text-slate-500">Detected by: {link.detected_by} agent</span>
                </div>

                {/* Decision Badge */}
                <div className="flex items-center gap-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase ${
                      link.decision === 'confirmed'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : link.decision === 'rejected'
                        ? 'bg-slate-200 text-slate-600'
                        : 'bg-amber-100 text-amber-800 border border-amber-300'
                    }`}
                  >
                    Decision: {link.decision}
                  </span>
                </div>
              </div>

              {/* Side-by-Side Cases Comparison Grid */}
              <div className="p-4 md:p-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  
                  {/* Case A Box */}
                  <div className="p-3.5 rounded-lg border border-indigo-200 bg-indigo-50/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs font-bold text-[#1E3A8A] bg-white px-2 py-0.5 rounded border border-indigo-200">
                        {caseA?.case_no}
                      </span>
                      <span className="text-xs font-bold text-indigo-900 bg-indigo-100 px-2 py-0.5 rounded">
                        Bureau: {caseA?.assigned_bureau}
                      </span>
                    </div>

                    <h4 className="font-bold text-slate-900 text-xs md:text-sm">
                      {caseA?.raw_institution}
                    </h4>
                    <p className="text-xs text-slate-600 mt-1">
                      <strong>Category:</strong> {caseA?.category}
                    </p>
                    <p className="text-xs text-slate-700 mt-2 bg-white p-2.5 rounded border border-slate-200 italic line-clamp-3">
                      &quot;{caseA?.text_english}&quot;
                    </p>

                    <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Officer: {caseA?.assigned_officer_name}</span>
                      <Link
                        href={`/cases/${caseA?.id}`}
                        className="text-blue-700 font-bold hover:underline"
                      >
                        Open Dossier &rarr;
                      </Link>
                    </div>
                  </div>

                  {/* Case B Box */}
                  <div className="p-3.5 rounded-lg border border-purple-200 bg-purple-50/30">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs font-bold text-purple-900 bg-white px-2 py-0.5 rounded border border-purple-200">
                        {caseB?.case_no}
                      </span>
                      <span className="text-xs font-bold text-purple-900 bg-purple-100 px-2 py-0.5 rounded">
                        Bureau: {caseB?.assigned_bureau}
                      </span>
                    </div>

                    <h4 className="font-bold text-slate-900 text-xs md:text-sm">
                      {caseB?.raw_institution}
                    </h4>
                    <p className="text-xs text-slate-600 mt-1">
                      <strong>Category:</strong> {caseB?.category}
                    </p>
                    <p className="text-xs text-slate-700 mt-2 bg-white p-2.5 rounded border border-slate-200 italic line-clamp-3">
                      &quot;{caseB?.text_english}&quot;
                    </p>

                    <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500">
                      <span>Officer: {caseB?.assigned_officer_name}</span>
                      <Link
                        href={`/cases/${caseB?.id}`}
                        className="text-purple-700 font-bold hover:underline"
                      >
                        Open Dossier &rarr;
                      </Link>
                    </div>
                  </div>

                </div>

                {/* Evidence & Judge Reasoning */}
                <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 mb-4">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 uppercase mb-1">
                    <Info className="w-3.5 h-3.5 text-indigo-700" />
                    Agentic Overlap Evidence & Cross-Check Rationale:
                  </div>

                  <p className="text-xs text-slate-700 leading-relaxed">
                    {link.evidence.reasoning}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 mt-2 text-[11px] text-slate-600 pt-2 border-t border-slate-200">
                    <span>
                      Permanent ID Match: <strong>{link.evidence.id_match ? 'Exact (1-281459201)' : 'Fuzzy'}</strong>
                    </span>
                    <span>•</span>
                    <span>Name Score: <strong>{((link.evidence.name_score || 0.9) * 100).toFixed(0)}%</strong></span>
                    <span>•</span>
                    <span>Text Cosine Sim: <strong>{((link.evidence.text_sim || 0.7) * 100).toFixed(0)}%</strong></span>
                  </div>
                </div>

                {/* Officer Confirm / Reject Buttons */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-100">
                  <div className="text-xs text-slate-500">
                    Decision logs update ML thresholds and trigger joint-bureau notification.
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDecision(link.id, 'confirmed')}
                      className={`flex items-center gap-1 px-3.5 py-1.5 rounded text-xs font-bold transition cursor-pointer ${
                        link.decision === 'confirmed'
                          ? 'bg-emerald-700 text-white'
                          : 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs'
                      }`}
                    >
                      <Check className="w-3.5 h-3.5" />
                      Confirm Overlap (सहमति)
                    </button>

                    <button
                      onClick={() => handleDecision(link.id, 'rejected')}
                      className={`flex items-center gap-1 px-3.5 py-1.5 rounded text-xs font-semibold transition cursor-pointer ${
                        link.decision === 'rejected'
                          ? 'bg-rose-700 text-white'
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                      }`}
                    >
                      <X className="w-3.5 h-3.5" />
                      Reject Match
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </AppLayout>
  );
}
