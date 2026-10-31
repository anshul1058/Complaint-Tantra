'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { AppLayout } from '@/components/layout/AppLayout';
import { getCases } from '@/lib/api/client';
import { Case } from '@/lib/types';
import { mockCases } from '@/lib/mock/data';
import { formatDate, statusColor } from '@/lib/utils';
import {
  Search,
  RefreshCw,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react';

export default function CasesListPage() {
  const [cases, setCases] = useState<Case[]>(mockCases);
  const [search, setSearch] = useState('');
  const [bureau, setBureau] = useState('ALL');
  const [status, setStatus] = useState('ALL');

  const fetchFiltered = async () => {
    const res = await getCases({
      search: search || undefined,
      bureau: bureau !== 'ALL' ? bureau : undefined,
      status: status !== 'ALL' ? status : undefined,
    });
    setCases(res);
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchFiltered();
  }, [bureau, status]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchFiltered();
  };

  const handleReset = () => {
    setSearch('');
    setBureau('ALL');
    setStatus('ALL');
    setCases(mockCases);
  };

  return (
    <AppLayout
      pageTitle="All Complaint Cases"
      hindiTitle="समस्त शिकायत प्रकरण"
      actionButton={
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={fetchFiltered}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-xs transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#1E3A8A]" />
            Refresh List
          </button>
        </div>
      }
    >
      {/* Search & Filter Toolbar */}
      <div className="bg-white/95 rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)] mb-5">
        <form onSubmit={handleSearchSubmit} className="space-y-3">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* Search Input */}
            <div className="lg:col-span-1">
              <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                Search Case / Inst. / ID
              </label>
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Case no, college name..."
                  className="w-full pl-9 pr-3 py-1.5 text-xs rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-[#0EA5E9]"
                />
              </div>
            </div>

            {/* Bureau Filter */}
            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                Assigned Bureau
              </label>
              <select
                value={bureau}
                onChange={(e) => setBureau(e.target.value)}
                className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#0EA5E9]"
              >
                <option value="ALL">All Bureaus (RB, PGRC, etc.)</option>
                <option value="RB">RB (Regulation Bureau)</option>
                <option value="PGRC">PGRC (Grievance Cell)</option>
                <option value="Approval">Approval Bureau</option>
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                State Machine Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                className="w-full px-3 py-1.5 text-xs rounded-xl border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-[#0EA5E9]"
              >
                <option value="ALL">All Statuses</option>
                <option value="Received">Received</option>
                <option value="Under Process">Under Process</option>
                <option value="Transferred">Transferred</option>
                <option value="Escalated">Escalated</option>
                <option value="Disposed">Disposed</option>
                <option value="Reopened">Reopened</option>
              </select>
            </div>

            {/* Submit & Reset Buttons */}
            <div className="flex items-end gap-2">
              <button
                type="submit"
                className="flex-1 py-1.5 px-4 bg-[#1E3A8A] hover:bg-[#1e40af] text-white text-xs font-bold rounded-xl shadow-xs transition flex items-center justify-center gap-1.5 cursor-pointer"
              >
                <Search className="w-3.5 h-3.5" />
                Apply Filter
              </button>
              <button
                type="button"
                onClick={handleReset}
                className="py-1.5 px-3 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-xl transition cursor-pointer"
              >
                Reset
              </button>
            </div>
          </div>
        </form>
      </div>

      {/* Case Table */}
      <div className="bg-white/95 rounded-2xl border border-slate-200/80 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)] overflow-hidden">
        <div className="p-3.5 bg-slate-50/80 border-b border-slate-200/80 flex items-center justify-between text-xs font-semibold text-slate-600">
          <span>Found {cases.length} cases matching criteria</span>
          <span className="text-[11px] text-slate-400">Click any row to open case dossier</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-white text-[11px] uppercase tracking-wider font-semibold">
              <tr>
                <th className="py-3 px-3">Case No.</th>
                <th className="py-3 px-3">Institution & City</th>
                <th className="py-3 px-3">Bureau</th>
                <th className="py-3 px-3">Category</th>
                <th className="py-3 px-3">Status</th>
                <th className="py-3 px-3">Crit.</th>
                <th className="py-3 px-3">Priority</th>
                <th className="py-3 px-3">Received</th>
                <th className="py-3 px-3">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {cases.map((c) => (
                <tr
                  key={c.id}
                  className="hover:bg-indigo-50/40 transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-3 font-mono font-bold text-[#1E3A8A]">
                    <Link href={`/cases/${c.id}`} className="hover:underline">
                      {c.case_no}
                    </Link>
                    {c.safety_flag && (
                      <span className="block text-[10px] text-rose-600 font-bold flex items-center gap-0.5 mt-0.5">
                        <ShieldAlert className="w-3 h-3" /> Safety
                      </span>
                    )}
                  </td>

                  <td className="py-3 px-3 max-w-[240px]">
                    <div className="font-bold text-slate-900 truncate">
                      {c.raw_institution}
                    </div>
                    <div className="text-[10px] text-slate-500">
                      {c.institution_city}, {c.institution_state}
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    <span className="font-semibold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                      {c.assigned_bureau}
                    </span>
                  </td>

                  <td className="py-3 px-3 max-w-[200px]">
                    <div className="truncate text-slate-700 font-medium">
                      {c.category}
                    </div>
                  </td>

                  <td className="py-3 px-3">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold border ${statusColor(
                        c.status
                      )}`}
                    >
                      {c.status}
                    </span>
                  </td>

                  <td className="py-3 px-3">
                    <span
                      className={`px-1.5 py-0.5 rounded text-[10px] font-extrabold ${
                        c.criticality === 'C1'
                          ? 'bg-red-100 text-red-800'
                          : c.criticality === 'C2'
                          ? 'bg-orange-100 text-orange-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {c.criticality}
                    </span>
                  </td>

                  <td className="py-3 px-3 font-extrabold text-[#0f172a]">
                    {c.priority_score.toFixed(0)}
                  </td>

                  <td className="py-3 px-3 text-slate-500">
                    {formatDate(c.received_at)}
                  </td>

                  <td className="py-3 px-3">
                    <Link
                      href={`/cases/${c.id}`}
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-[#1E3A8A] hover:text-[#ff6f00]"
                    >
                      View <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppLayout>
  );
}
