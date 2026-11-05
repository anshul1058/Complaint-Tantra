'use client';

import Link from 'next/link';
import { ArrowRight, GitMerge, ShieldAlert } from 'lucide-react';
import { Case } from '@/lib/types';
import { formatDate } from '@/lib/utils';

interface RecentComplaintsCardProps {
  cases: Case[];
}

function statusClass(status: Case['status']): string {
  if (status === 'Disposed') return 'bg-emerald-50 text-emerald-700 border-emerald-200';
  if (status === 'Escalated') return 'bg-rose-50 text-rose-700 border-rose-200';
  if (status === 'Under Process' || status === 'UnderProcess') {
    return 'bg-amber-50 text-amber-700 border-amber-200';
  }
  return 'bg-sky-50 text-sky-700 border-sky-200';
}

export function RecentComplaintsCard({ cases }: RecentComplaintsCardProps) {
  return (
    <section className="bg-white border border-slate-200 rounded-2xl shadow-2xs overflow-hidden">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between gap-3">
        <div>
          <h2 className="text-sm font-extrabold text-slate-900">Recent Complaints</h2>
          <p className="text-[11px] text-slate-500 mt-0.5">
            Live records ranked by the backend priority engine
          </p>
        </div>
        <Link
          href="/queue"
          className="text-xs font-bold text-[#1E3A8A] hover:text-blue-700 flex items-center gap-1"
        >
          View all <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {cases.length === 0 ? (
        <div className="px-5 py-8 text-center text-xs text-slate-500">
          No complaints are available for your officer scope yet.
        </div>
      ) : (
        <div className="divide-y divide-slate-100">
          {cases.slice(0, 10).map((item) => (
            <Link
              key={item.id}
              href={`/cases/${item.id}`}
              className="block px-5 py-3 hover:bg-slate-50 transition"
            >
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className="font-mono text-[10px] font-bold text-[#1E3A8A] bg-sky-50 border border-sky-200 rounded px-1.5 py-0.5">
                      {item.case_no}
                    </span>
                    <span className="text-[10px] font-bold text-slate-600 bg-slate-100 rounded px-1.5 py-0.5">
                      {item.assigned_bureau}
                    </span>
                    <span className={`text-[10px] font-bold border rounded px-1.5 py-0.5 ${statusClass(item.status)}`}>
                      {item.status}
                    </span>
                    {item.safety_flag && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-rose-700">
                        <ShieldAlert className="w-3 h-3" /> Safety
                      </span>
                    )}
                    {!!item.overlap_count && (
                      <span className="inline-flex items-center gap-1 text-[10px] font-bold text-purple-700">
                        <GitMerge className="w-3 h-3" /> {item.overlap_count} overlap
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-xs font-bold text-slate-800 truncate">
                    {item.institution_name || item.raw_institution}
                  </p>
                  <p className="text-[11px] text-slate-500 truncate">
                    {item.category} · {item.ai_summary || item.text_english}
                  </p>
                </div>
                <div className="shrink-0 text-left lg:text-right">
                  <p className="text-sm font-extrabold text-[#1E3A8A]">
                    {item.priority_score.toFixed(1)}
                  </p>
                  <p className="text-[10px] text-slate-500">priority · {formatDate(item.received_at)}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
