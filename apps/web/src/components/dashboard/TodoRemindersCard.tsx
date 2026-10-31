'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  Bell,
  Plus,
  CheckCircle2,
  Circle,
  ArrowRight,
  ShieldAlert,
  GitMerge,
  Clock,
  TrendingUp,
} from 'lucide-react';
import { Alert } from '@/lib/types';
import { timeAgo } from '@/lib/utils';

interface TodoRemindersCardProps {
  alerts: Alert[];
}

export const TodoRemindersCard: React.FC<TodoRemindersCardProps> = ({ alerts }) => {
  const [completedIds, setCompletedIds] = useState<Record<string, boolean>>({});

  const toggleComplete = (id: string) => {
    setCompletedIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const getAlertIcon = (kind: Alert['kind']) => {
    switch (kind) {
      case 'safety':
        return <ShieldAlert className="w-3.5 h-3.5 text-[#DC2626]" />;
      case 'overlap':
        return <GitMerge className="w-3.5 h-3.5 text-purple-600" />;
      case 'overdue':
        return <Clock className="w-3.5 h-3.5 text-[#F59E0B]" />;
      case 'escalation':
        return <TrendingUp className="w-3.5 h-3.5 text-orange-600" />;
      default:
        return <Bell className="w-3.5 h-3.5 text-sky-600" />;
    }
  };

  const getBadgeStyle = (severity: Alert['severity']) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'high':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      default:
        return 'bg-sky-100 text-sky-800 border-sky-200';
    }
  };

  const displayAlerts = alerts.slice(0, 5);

  return (
    <div className="bg-white/95 backdrop-blur-xs rounded-2xl p-5 border border-slate-200/80 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)]">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <Bell className="w-4 h-4 text-[#1E3A8A]" />
          <div>
            <h3 className="font-extrabold text-[#1E3A8A] text-sm md:text-base tracking-tight">
              Action Items & Triage Feeds
            </h3>
            <span className="text-[10px] text-slate-400 font-medium">
              Real-time automated decision alerts ({alerts.length} Pending)
            </span>
          </div>
        </div>

        {/* Plus Button linking to priority queue */}
        <Link
          href="/queue"
          aria-label="View priority queue"
          className="w-7 h-7 rounded-full bg-[#1E3A8A] hover:bg-[#1e40af] text-white flex items-center justify-center transition shadow-xs cursor-pointer"
        >
          <Plus className="w-4 h-4" />
        </Link>
      </div>

      {/* Checklist of Real Action Items */}
      <div className="space-y-3 mt-3.5">
        {displayAlerts.map((alt) => {
          const isDone = completedIds[alt.id];

          return (
            <div
              key={alt.id}
              className="flex items-start justify-between gap-3 group transition-colors p-1.5 rounded-xl hover:bg-slate-50/80 border border-transparent hover:border-slate-100"
            >
              <div className="flex items-start gap-2.5">
                <button
                  type="button"
                  onClick={() => toggleComplete(alt.id)}
                  className="mt-0.5 text-slate-300 hover:text-emerald-600 transition cursor-pointer"
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-[#16A34A] fill-emerald-50" />
                  ) : (
                    <Circle className="w-4 h-4 text-slate-300 group-hover:text-slate-400" />
                  )}
                </button>

                <div>
                  <div className="flex items-center gap-1.5">
                    {getAlertIcon(alt.kind)}
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                      {alt.kind.replace('_', ' ')}
                    </span>
                  </div>

                  <h4 className={`text-xs font-bold leading-snug mt-0.5 ${
                    isDone ? 'line-through text-slate-400' : 'text-slate-800'
                  }`}>
                    {alt.message}
                  </h4>

                  <div className="flex items-center flex-wrap gap-2 mt-1">
                    {alt.institution_name && (
                      <span className="text-[10px] text-slate-400 font-medium truncate max-w-[170px]">
                        🏛️ {alt.institution_name}
                      </span>
                    )}

                    <span
                      className={`text-[9.5px] font-bold px-1.5 py-0.2 rounded-full border ${getBadgeStyle(
                        alt.severity
                      )}`}
                    >
                      {alt.severity.toUpperCase()}
                    </span>

                    <span className="text-[10px] text-slate-400">
                      {timeAgo(alt.created_at)}
                    </span>
                  </div>
                </div>
              </div>

              {alt.case_no && (
                <Link
                  href={`/cases/${alt.case_id || 'case-001'}`}
                  className="p-1 text-slate-400 hover:text-[#1E3A8A] transition rounded self-center"
                  title="Open Case"
                >
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-3 pt-2.5 border-t border-slate-100 text-center">
        <Link
          href="/overlaps"
          className="text-xs font-bold text-[#1E3A8A] hover:text-sky-700 hover:underline inline-flex items-center gap-1"
        >
          <span>Open Overlap Coordination Room</span>
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
};
