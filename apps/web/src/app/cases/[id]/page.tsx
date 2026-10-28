'use client';

import React, { useEffect, useState, Suspense, useCallback } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { AppLayout } from '@/components/layout/AppLayout';
import { PriorityBreakdown } from '@/components/cases/PriorityBreakdown';
import { StatusTimeline } from '@/components/cases/StatusTimeline';
import { OverlapBanner } from '@/components/cases/OverlapBanner';
import { getCase, getCaseActions, getCaseOverlaps, postCaseAction } from '@/lib/api/client';
import { Case, CaseAction, CaseLink } from '@/lib/types';
import { mockCases, mockCaseActions, mockCaseLinks } from '@/lib/mock/data';
import { formatDate, statusColor } from '@/lib/utils';
import {
  Building2,
  Sparkles,
  ShieldAlert,
  Send,
  ArrowRightLeft,
  TrendingUp,
  CheckCircle,
  RotateCcw,
  MessageSquare,
  FileText,
} from 'lucide-react';

function CaseDetailContent() {
  const params = useParams();
  const caseId = (params?.id as string) || 'case-001';

  const [caseData, setCaseData] = useState<Case>(mockCases[0]);
  const [actions, setActions] = useState<CaseAction[]>(mockCaseActions);
  const [overlaps, setOverlaps] = useState<CaseLink[]>(mockCaseLinks);
  const [remarks, setRemarks] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const loadCaseDetails = useCallback(async () => {
    try {
      const [c, a, o] = await Promise.all([
        getCase(caseId),
        getCaseActions(caseId),
        getCaseOverlaps(caseId),
      ]);
      if (c) setCaseData(c);
      setActions(a);
      setOverlaps(o);
    } catch {
      // fallback
    }
  }, [caseId]);

  useEffect(() => {
    loadCaseDetails();
  }, [loadCaseDetails]);

  const handleAction = async (actionType: string, toState?: string) => {
    if (!remarks.trim() && actionType === 'remark') {
      alert('Please enter remarks before submitting.');
      return;
    }
    setIsSubmitting(true);
    try {
      await postCaseAction(caseId, {
        action: actionType,
        remarks: remarks || `Action: ${actionType} triggered by officer`,
        to_state: toState,
      });
      setRemarks('');
      if (toState) {
        setCaseData((prev) => ({ ...prev, status: toState as Case['status'] }));
      }
      await loadCaseDetails();
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <AppLayout
      pageTitle={`Case Dossier: ${caseData.case_no}`}
      hindiTitle="शिकायत प्रकरण विवरण"
      actionButton={
        <div className="flex items-center gap-2">
          <Link
            href={`/institutions/${caseData.institution_id || 'inst-001'}`}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white border border-slate-300 text-slate-800 text-xs font-semibold hover:bg-slate-50 transition shadow-xs"
          >
            <Building2 className="w-3.5 h-3.5 text-[#ff6f00]" />
            Institution 360° Profile
          </Link>
        </div>
      }
    >
      {/* 1. Potential Overlap Banner (FR-33) */}
      {overlaps.length > 0 && (
        <OverlapBanner
          caseNo={caseData.case_no}
          overlapCount={overlaps.length}
          tier={overlaps[0]?.tier || 'T1'}
          confidence={overlaps[0]?.confidence || 0.93}
          relatedCaseNo={overlaps[0]?.case_b_details?.case_no || 'AICTE/PGRC/2026/0412'}
          relatedBureau={overlaps[0]?.case_b_details?.assigned_bureau || 'PGRC'}
        />
      )}

      {/* 2. Top Info Header Strip */}
      <div className="bg-white rounded-lg border border-slate-200 p-4 md:p-5 shadow-sm mb-5">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center flex-wrap gap-2 mb-1.5">
              <span className="font-mono text-sm font-extrabold text-[#1E3A8A] bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
                {caseData.case_no}
              </span>

              <span
                className={`px-2.5 py-0.5 rounded text-xs font-bold border ${statusColor(
                  caseData.status
                )}`}
              >
                Status: {caseData.status}
              </span>

              <span
                className={`px-2 py-0.5 rounded text-xs font-extrabold ${
                  caseData.criticality === 'C1'
                    ? 'bg-red-100 text-red-900 border border-red-300'
                    : 'bg-orange-100 text-orange-900 border border-orange-300'
                }`}
              >
                {caseData.criticality}
              </span>

              {caseData.safety_flag && (
                <span className="flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded bg-rose-600 text-white animate-pulse">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Safety Review Active
                </span>
              )}
            </div>

            <h3 className="text-base md:text-lg font-bold text-slate-900">
              {caseData.raw_institution}
            </h3>
            <p className="text-xs text-slate-600 mt-0.5">
              {caseData.category} • Assigned to: <strong>{caseData.assigned_officer_name} ({caseData.assigned_bureau})</strong>
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="flex items-center gap-3 bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs">
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">
                RECEIVED
              </span>
              <span className="font-bold text-slate-700">
                {formatDate(caseData.received_at)}
              </span>
            </div>
            <div className="h-7 w-px bg-slate-200" />
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">
                SLA TARGET
              </span>
              <span className="font-bold text-red-600">
                {formatDate(caseData.expected_disposal)}
              </span>
            </div>
            <div className="h-7 w-px bg-slate-200" />
            <div>
              <span className="text-[10px] text-slate-400 block font-semibold uppercase">
                PRIORITY SCORE
              </span>
              <span className="font-extrabold text-base text-[#1E3A8A]">
                {caseData.priority_score.toFixed(1)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. Main Two-Column Work Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Left Column (2 Cols): Complaint Texts + AI Summary + Priority Breakdown */}
        <div className="lg:col-span-2 space-y-5">
          
          {/* AI Case Brief Card */}
          <div className="bg-gradient-to-br from-indigo-50/80 via-white to-amber-50/30 rounded-lg border border-indigo-200 p-5 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-indigo-100 mb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-700" />
                <h4 className="font-bold text-slate-900 text-sm md:text-base">
                  AI Intake & Case Brief (Intake Agent Output)
                </h4>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-100 text-indigo-800 border border-indigo-200">
                AI-Generated Brief • Version 2.1
              </span>
            </div>

            <p className="text-xs md:text-sm text-slate-800 leading-relaxed font-normal">
              {caseData.ai_summary}
            </p>

            <div className="mt-3 pt-2 border-t border-indigo-100/60 flex items-center justify-between text-[11px] text-slate-500">
              <span>Emotion Signal: <strong>{caseData.emotion_label} ({caseData.emotion_intensity * 100}%)</strong></span>
              <span>Next Action: <strong>{caseData.next_action}</strong></span>
            </div>
          </div>

          {/* Original Complaint vs English Translation Tabs */}
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
              <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <FileText className="w-4 h-4 text-slate-600" />
                Raw Grievance Text & Translation
              </h4>
              <span className="text-xs font-semibold text-slate-500">
                Source: {caseData.language}
              </span>
            </div>

            {/* Side-by-side or stacked texts */}
            <div className="space-y-4">
              <div>
                <label className="block text-[11px] font-bold text-slate-500 uppercase mb-1">
                  Original Text as Lodged by Complainant ({caseData.complainant_type})
                </label>
                <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs text-slate-800 leading-relaxed font-serif">
                  {caseData.text_original}
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-bold text-indigo-800 uppercase mb-1 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                  Canonical English Translation (Audited Intake Output)
                </label>
                <div className="bg-indigo-50/40 p-3.5 rounded-lg border border-indigo-200 text-xs text-slate-800 leading-relaxed">
                  {caseData.text_english}
                </div>
              </div>
            </div>
          </div>

          {/* Priority Score Breakdown Component */}
          <PriorityBreakdown
            priorityScore={caseData.priority_score}
            priorityReasons={caseData.priority_reasons}
          />

          {/* Officer Action Panel */}
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <h4 className="font-bold text-slate-900 text-sm mb-2 flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-[#1E3A8A]" />
              Officer Action & Case Transition
            </h4>
            <p className="text-xs text-slate-500 mb-3">
              Record a formal remark or transition case status. Every action is cryptographically logged.
            </p>

            <textarea
              rows={3}
              value={remarks}
              onChange={(e) => setRemarks(e.target.value)}
              placeholder="Enter official inquiry remarks, hearing notice details, or transfer reasons..."
              className="w-full p-2.5 text-xs rounded-md border border-slate-300 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A] mb-3"
            />

            <div className="flex flex-wrap items-center gap-2">
              <button
                onClick={() => handleAction('remark')}
                disabled={isSubmitting}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold rounded shadow-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <Send className="w-3.5 h-3.5" />
                Add Remark
              </button>

              <button
                onClick={() => handleAction('transferred', 'Transferred')}
                disabled={isSubmitting}
                className="px-3 py-1.5 bg-purple-700 hover:bg-purple-800 text-white text-xs font-bold rounded shadow-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <ArrowRightLeft className="w-3.5 h-3.5" />
                Transfer to PGRC
              </button>

              <button
                onClick={() => handleAction('escalated', 'Escalated')}
                disabled={isSubmitting}
                className="px-3 py-1.5 bg-orange-600 hover:bg-orange-700 text-white text-xs font-bold rounded shadow-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <TrendingUp className="w-3.5 h-3.5" />
                Escalate to Chairman
              </button>

              <button
                onClick={() => handleAction('disposed', 'Disposed')}
                disabled={isSubmitting}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded shadow-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <CheckCircle className="w-3.5 h-3.5" />
                Dispose / Close Case
              </button>

              <button
                onClick={() => handleAction('reopened', 'Reopened')}
                disabled={isSubmitting}
                className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded shadow-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Reopen
              </button>
            </div>
          </div>
        </div>

        {/* Right Column (1 Col): Metadata + Action Timeline */}
        <div className="space-y-5">
          {/* Metadata Card */}
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <h4 className="font-bold text-slate-800 text-xs uppercase tracking-wider pb-2 border-b border-slate-100 mb-3">
              Case Attributes
            </h4>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Source Bureau:</span>
                <span className="font-bold text-slate-800">{caseData.source_bureau}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Assigned Bureau:</span>
                <span className="font-bold text-slate-800">{caseData.assigned_bureau}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Assigned Officer:</span>
                <span className="font-bold text-slate-800">{caseData.assigned_officer_name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Complainant:</span>
                <span className="font-bold text-slate-800 capitalize">{caseData.complainant_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Category:</span>
                <span className="font-semibold text-slate-800 text-right max-w-[160px] truncate">{caseData.category}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-100">
                <span className="text-slate-500">Received Date:</span>
                <span className="font-bold text-slate-800">{formatDate(caseData.received_at)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">SLA Expiry:</span>
                <span className="font-bold text-red-600">{formatDate(caseData.expected_disposal)}</span>
              </div>
            </div>
          </div>

          {/* Append-Only Status Timeline */}
          <StatusTimeline
            actions={actions}
            currentStatus={caseData.status}
          />
        </div>

      </div>
    </AppLayout>
  );
}

export default function CaseDetailPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#f4f6fa] flex items-center justify-center text-xs text-slate-500">
          Loading case dossier...
        </div>
      }
    >
      <CaseDetailContent />
    </Suspense>
  );
}
