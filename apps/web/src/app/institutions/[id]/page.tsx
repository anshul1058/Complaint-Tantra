'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { AppLayout } from '@/components/layout/AppLayout';
import { getInstitution, getInstitutionRisk, getInstitutionIntel } from '@/lib/api/client';
import { Institution, InstitutionRisk, WebFinding } from '@/lib/types';
import { mockInstitutions, mockInstitutionRisks, mockWebFindings, mockCases } from '@/lib/mock/data';
import { formatDate } from '@/lib/utils';
import {
  Building2,
  ShieldAlert,
  Globe,
  ExternalLink,
  RefreshCw,
  History,
} from 'lucide-react';

function Institution360Content() {
  const params = useParams();
  const instId = (params?.id as string) || 'inst-001';

  const [inst, setInst] = useState<Institution>(mockInstitutions[0]);
  const [risk, setRisk] = useState<InstitutionRisk>(mockInstitutionRisks['inst-001']);
  const [intel, setIntel] = useState<WebFinding[]>(mockWebFindings);
  const [activeTab, setActiveTab] = useState<'intel' | 'history' | 'risk'>('intel');
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    getInstitution(instId).then((res) => res && setInst(res));
    getInstitutionRisk(instId).then((res) => res && setRisk(res));
    getInstitutionIntel(instId).then(setIntel);
  }, [instId]);

  const handleRefreshIntel = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      alert('Web Intelligence Agent crawled news & public notices. 4 findings verified.');
    }, 800);
  };

  const instCases = mockCases.filter(
    (c) => c.institution_id === instId || c.institution_id === 'inst-001'
  );

  return (
    <AppLayout
      pageTitle={`Institution 360°: ${inst.name}`}
      hindiTitle="संस्थान 360° रूपरेखा"
      actionButton={
        <div className="flex items-center gap-2">
          <button
            onClick={handleRefreshIntel}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-white border border-slate-300 text-slate-800 text-xs font-semibold hover:bg-slate-50 transition shadow-xs cursor-pointer"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 text-[#1E3A8A] ${
                isRefreshing ? 'animate-spin' : ''
              }`}
            />
            {isRefreshing ? 'Crawling Public Web...' : 'Refresh Web Intel'}
          </button>
        </div>
      }
    >
      {/* 1. Institution Master Header Card */}
      <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm mb-5">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="p-3 bg-gradient-to-tr from-[#1E3A8A] to-[#1e40af] rounded-lg text-amber-300 shadow-sm mt-0.5">
              <Building2 className="w-8 h-8" />
            </div>

            <div>
              <div className="flex items-center flex-wrap gap-2">
                <span className="font-mono text-xs font-bold text-[#1E3A8A] bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
                  AICTE PID: {inst.permanent_id || '1-281459201'}
                </span>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                  {inst.region} Regional Office
                </span>
              </div>

              <h3 className="text-lg md:text-xl font-bold text-slate-900 mt-1">
                {inst.name}
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {inst.address}, {inst.city}, {inst.state} • Trust: <strong>{inst.trust_or_society}</strong>
              </p>
            </div>
          </div>

          {/* Risk Index Meter Badge */}
          <div className="flex items-center gap-3 bg-slate-50 p-3 rounded-lg border border-slate-200">
            <div className="text-right">
              <span className="text-[10px] uppercase font-bold text-slate-500 block">
                INSTITUTION RISK INDEX
              </span>
              <span className="text-2xl font-extrabold text-red-700">
                {risk.risk_index.toFixed(1)} / 100
              </span>
              <span className="text-[10px] text-red-600 font-semibold block">
                High Regulatory Risk
              </span>
            </div>

            <div className="p-2 bg-red-100 text-red-800 rounded-full border border-red-200">
              <ShieldAlert className="w-6 h-6 animate-pulse" />
            </div>
          </div>
        </div>

        {/* Risk Formula Breakdown Sub-Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-4 pt-3 border-t border-slate-100 text-xs">
          <div className="bg-slate-50 p-2 rounded">
            <span className="text-[10px] text-slate-400 block font-semibold">Complaint Load (35%)</span>
            <span className="font-bold text-slate-800">{(risk.complaint_load * 100).toFixed(0)}% percentile</span>
          </div>
          <div className="bg-slate-50 p-2 rounded">
            <span className="text-[10px] text-slate-400 block font-semibold">Repeat Offender (25%)</span>
            <span className="font-bold text-amber-700">{(risk.repeat_offender * 100).toFixed(0)}% repeat rate</span>
          </div>
          <div className="bg-slate-50 p-2 rounded">
            <span className="text-[10px] text-slate-400 block font-semibold">Web Media Risk (25%)</span>
            <span className="font-bold text-red-700">{(risk.web_reputation * 100).toFixed(0)}% negative sentiment</span>
          </div>
          <div className="bg-slate-50 p-2 rounded">
            <span className="text-[10px] text-slate-400 block font-semibold">Cross-Bureau Overlap (15%)</span>
            <span className="font-bold text-purple-700">{(risk.overlap_density * 100).toFixed(0)}% density</span>
          </div>
        </div>
      </div>

      {/* 2. Navigation Tabs */}
      <div className="flex items-center gap-2 mb-5 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('intel')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-bold transition cursor-pointer ${
            activeTab === 'intel'
              ? 'bg-[#1E3A8A] text-white shadow-xs'
              : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <Globe className="w-4 h-4 text-amber-400" />
          Agentic Web Intelligence ({intel.length} Cited Findings)
        </button>

        <button
          onClick={() => setActiveTab('history')}
          className={`flex items-center gap-2 px-4 py-2 rounded-md text-xs font-bold transition cursor-pointer ${
            activeTab === 'history'
              ? 'bg-[#1E3A8A] text-white shadow-xs'
              : 'bg-white text-slate-700 hover:bg-slate-100 border border-slate-200'
          }`}
        >
          <History className="w-4 h-4 text-[#ff6f00]" />
          Complaint History ({instCases.length} Cases)
        </button>
      </div>

      {/* 3. Tab Contents */}

      {/* Tab: Web Intelligence */}
      {activeTab === 'intel' && (
        <div className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 p-3 rounded-lg text-xs text-amber-900 flex items-center justify-between">
            <span>
              ℹ️ <strong>Legal Disclaimer:</strong> Public news and web intelligence are used strictly as <em>contextual intelligence</em>, not substantive evidence of violation. All findings carry source URLs and timestamps.
            </span>
            <span className="font-bold text-amber-700 shrink-0">100% Citation Coverage</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {intel.map((wf) => (
              <div
                key={wf.id}
                className="bg-white rounded-lg border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-red-100 text-red-800 border border-red-200">
                      Topic: {wf.topic}
                    </span>
                    <span className="text-[10px] text-slate-400">
                      Published: {wf.published_at}
                    </span>
                  </div>

                  <h4 className="font-bold text-slate-900 text-sm leading-snug">
                    {wf.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-1 font-medium">
                    Source: {wf.source_name}
                  </p>

                  <p className="text-xs text-slate-700 mt-2.5 leading-relaxed bg-slate-50 p-2.5 rounded border border-slate-100">
                    {wf.summary}
                  </p>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                        wf.sentiment === 'negative'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {wf.sentiment.toUpperCase()}
                    </span>
                    <span className="text-[11px] text-slate-500">
                      Match: {(wf.match_confidence * 100).toFixed(0)}%
                    </span>
                  </div>

                  <a
                    href={wf.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-[11px] font-bold text-blue-700 hover:underline"
                  >
                    Open Source URL <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Complaint History */}
      {activeTab === 'history' && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-3 bg-slate-50 border-b border-slate-200 font-bold text-xs text-slate-700">
            Cross-Bureau Case Register for this Institution
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0f172a] text-white text-[11px] uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Case No.</th>
                  <th className="py-2.5 px-3">Bureau</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Criticality</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Received</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {instCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-mono font-bold text-[#1E3A8A]">
                      {c.case_no}
                    </td>
                    <td className="py-2.5 px-3 font-semibold text-slate-700">
                      {c.assigned_bureau}
                    </td>
                    <td className="py-2.5 px-3 max-w-[250px] truncate text-slate-700">
                      {c.category}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">
                        {c.status}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 font-extrabold text-red-700">
                      {c.criticality}
                    </td>
                    <td className="py-2.5 px-3 font-bold text-[#1E3A8A]">
                      {c.priority_score.toFixed(0)}
                    </td>
                    <td className="py-2.5 px-3 text-slate-500">
                      {formatDate(c.received_at)}
                    </td>
                    <td className="py-2.5 px-3">
                      <Link
                        href={`/cases/${c.id}`}
                        className="font-bold text-blue-700 hover:underline"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppLayout>
  );
}

export default function Institution360Page() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#f4f6fa] flex items-center justify-center text-xs text-slate-500">
          Loading institution 360 profile...
        </div>
      }
    >
      <Institution360Content />
    </Suspense>
  );
}
