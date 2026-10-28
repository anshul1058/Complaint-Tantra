'use client';

import React from 'react';
import { PriorityReasons } from '@/lib/types';
import { Sparkles, Brain, CheckCircle2 } from 'lucide-react';

interface PriorityBreakdownProps {
  priorityScore: number;
  priorityReasons: PriorityReasons;
}

export const PriorityBreakdown: React.FC<PriorityBreakdownProps> = ({
  priorityScore,
  priorityReasons,
}) => {
  const { components, reasons } = priorityReasons;

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'from-rose-600 to-red-600 text-red-700';
    if (score >= 60) return 'from-amber-500 to-orange-500 text-orange-700';
    if (score >= 40) return 'from-yellow-400 to-amber-500 text-amber-700';
    return 'from-emerald-500 to-green-600 text-green-700';
  };

  const formulaRows = [
    {
      name: 'Criticality Factor (C1-C4)',
      weight: '35% weight',
      val: components.criticality,
      max: 0.35,
      color: 'bg-red-500',
    },
    {
      name: 'Emotion & Distress Urgency',
      weight: '20% weight',
      val: components.emotion,
      max: 0.20,
      color: 'bg-orange-500',
    },
    {
      name: 'SLA Time Pressure (Days left / Overdue)',
      weight: '25% weight',
      val: components.time,
      max: 0.25,
      color: 'bg-amber-500',
    },
    {
      name: 'Cross-Bureau T1 Overlap Bonus',
      weight: '10% weight',
      val: components.overlap,
      max: 0.10,
      color: 'bg-purple-600',
    },
    {
      name: 'Institution Track Record Risk Index',
      weight: '10% weight',
      val: components.risk,
      max: 0.10,
      color: 'bg-blue-600',
    },
  ];

  return (
    <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-[#1E3A8A]" />
          <div>
            <h3 className="font-bold text-slate-800 text-sm md:text-base">
              AI Priority Score Breakdown (Score: {priorityScore.toFixed(1)}/100)
            </h3>
            <p className="text-xs text-slate-500">
              एआई प्राथमिकता गणना एवं कारण (Explainable Multi-Factor Formula)
            </p>
          </div>
        </div>

        <span className="flex items-center gap-1 text-xs font-bold text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
          <Sparkles className="w-3.5 h-3.5 text-amber-500" />
          Deterministic & Explainable
        </span>
      </div>

      {/* Main Score Bar & Gauge */}
      <div className="mb-5 bg-slate-50 p-3.5 rounded-lg border border-slate-200">
        <div className="flex items-center justify-between text-xs mb-1.5 font-bold">
          <span className="text-slate-700 uppercase tracking-wide">
            Aggregated Priority Gauge
          </span>
          <span className={`text-base font-extrabold ${getScoreColor(priorityScore)}`}>
            {priorityScore.toFixed(1)} / 100
          </span>
        </div>

        <div className="w-full bg-slate-200 h-3 rounded-full overflow-hidden flex">
          <div
            className={`h-full bg-gradient-to-r ${getScoreColor(
              priorityScore
            )} transition-all duration-700 rounded-full`}
            style={{ width: `${Math.min(priorityScore, 100)}%` }}
          />
        </div>
      </div>

      {/* Factor Bars */}
      <div className="space-y-3 mb-5">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Factor Contributions
        </div>

        {formulaRows.map((row, i) => {
          const pct = Math.min(Math.round((row.val / row.max) * 100), 100);

          return (
            <div key={i} className="text-xs">
              <div className="flex justify-between items-center mb-1">
                <span className="font-medium text-slate-700">
                  {row.name} <span className="text-slate-400 text-[10px]">({row.weight})</span>
                </span>
                <span className="font-mono font-bold text-slate-800">
                  +{(row.val * 100).toFixed(1)} pts
                </span>
              </div>
              <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-full ${row.color} rounded-full`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Why #1 Reason List */}
      <div className="bg-amber-50/60 rounded-lg p-3.5 border border-amber-200/80">
        <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 mb-2 uppercase tracking-wide">
          <CheckCircle2 className="w-4 h-4 text-amber-600" />
          Rationales & Evidence Summary
        </div>

        <ul className="space-y-1.5">
          {reasons.map((r, i) => (
            <li
              key={i}
              className="text-xs text-slate-700 flex items-start gap-2 leading-relaxed"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-amber-600 mt-1.5 shrink-0" />
              <span>{r}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
