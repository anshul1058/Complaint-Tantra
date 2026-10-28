'use client';

import React from 'react';
import { CaseAction, CaseStatus } from '@/lib/types';
import { formatDate, timeAgo } from '@/lib/utils';
import {
  FileText,
  UserCheck,
  GitMerge,
  MessageSquare,
  ShieldAlert,
  ArrowRightLeft,
  TrendingUp,
  CheckCircle,
  RotateCcw,
} from 'lucide-react';

interface StatusTimelineProps {
  actions: CaseAction[];
  currentStatus: CaseStatus;
}

export const StatusTimeline: React.FC<StatusTimelineProps> = ({ actions }) => {
  const getActionIcon = (action: CaseAction['action']) => {
    switch (action) {
      case 'created':
        return <FileText className="w-3.5 h-3.5 text-blue-600" />;
      case 'assigned':
        return <UserCheck className="w-3.5 h-3.5 text-indigo-600" />;
      case 'linked':
        return <GitMerge className="w-3.5 h-3.5 text-purple-600" />;
      case 'remark':
        return <MessageSquare className="w-3.5 h-3.5 text-slate-600" />;
      case 'transferred':
        return <ArrowRightLeft className="w-3.5 h-3.5 text-amber-600" />;
      case 'escalated':
        return <TrendingUp className="w-3.5 h-3.5 text-orange-600" />;
      case 'disposed':
        return <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />;
      case 'reopened':
        return <RotateCcw className="w-3.5 h-3.5 text-rose-600" />;
      default:
        return <ShieldAlert className="w-3.5 h-3.5 text-blue-600" />;
    }
  };

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
        <div>
          <h3 className="font-bold text-slate-800 text-sm md:text-base">
            Append-Only Audit Log & Case Timeline
          </h3>
          <p className="text-xs text-slate-500">
            अपरिवर्तनीय लेखा परीक्षा इतिहास (Cryptographic & Tamper-Proof Audit)
          </p>
        </div>

        <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
          {actions.length} Events Logged
        </span>
      </div>

      <div className="relative pl-6 space-y-4 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {actions.map((act) => (
          <div key={act.id} className="relative text-xs">
            {/* Timeline Pin Icon */}
            <div className="absolute -left-6 top-0.5 w-5 h-5 rounded-full bg-white border-2 border-slate-300 flex items-center justify-center shadow-xs">
              {getActionIcon(act.action)}
            </div>

            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200/80">
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-bold text-slate-800 capitalize flex items-center gap-1.5">
                  {act.action.replace('_', ' ')}
                  {act.actor_type === 'agent' && (
                    <span className="text-[9px] px-1 rounded bg-blue-100 text-blue-800 font-normal">
                      AI Agent
                    </span>
                  )}
                </span>
                <span className="text-[10px] text-slate-400">
                  {timeAgo(act.created_at)} ({formatDate(act.created_at)})
                </span>
              </div>

              <p className="text-slate-700 leading-relaxed font-normal">
                {act.remarks}
              </p>

              <div className="mt-1.5 pt-1.5 border-t border-slate-200/50 flex items-center justify-between text-[10px] text-slate-500">
                <span>By: {act.actor_name || 'System'}</span>
                {act.to_state && (
                  <span className="font-semibold text-slate-700">
                    State: {act.from_state ? `${act.from_state} → ` : ''}
                    {act.to_state}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
