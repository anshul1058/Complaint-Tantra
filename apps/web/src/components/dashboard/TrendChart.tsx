'use client';

import React, { useState } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Sparkles, ChevronDown } from 'lucide-react';

export const TrendChart: React.FC = () => {
  const [period, setPeriod] = useState('6 Months');

  const trendData = [
    { month: 'MAY', received: 145, disposed: 130, overdue: 12 },
    { month: 'JUN', received: 180, disposed: 165, overdue: 15 },
    { month: 'JUL', received: 240, disposed: 210, overdue: 22 },
    { month: 'AUG', received: 310, disposed: 280, overdue: 28 },
    { month: 'SEP', received: 275, disposed: 260, overdue: 19 },
    { month: 'OCT', received: 278, disposed: 223, overdue: 48 },
  ];

  return (
    <div className="bg-white/95 backdrop-blur-xs rounded-2xl p-5 border border-slate-200/80 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)] relative">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 gap-3">
        <div>
          <div className="flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-[#0EA5E9]" />
            <h3 className="font-extrabold text-[#1E3A8A] text-sm md:text-base tracking-tight">
              Grievance Intake & Disposal Trajectory
            </h3>
          </div>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            मासिक शिकायत आवक एवं निस्तारण रुझान • Real-time AICTE Bureau Intake vs Resolution
          </p>
        </div>

        {/* Legend & Period Dropdown */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-3 font-semibold text-slate-600">
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#1E3A8A]" />
              Received (आवक)
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-[#0EA5E9]" />
              Disposed (निस्तारित)
            </span>
          </div>

          <div className="relative">
            <button
              type="button"
              className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition cursor-pointer"
            >
              <span>{period}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>
          </div>
        </div>
      </div>

      {/* Floating Peak Intake Badge like the reference image */}
      <div className="hidden sm:flex absolute top-18 right-32 z-10 items-center gap-1.5 px-3 py-1 rounded-full bg-white/95 border border-sky-200 shadow-md text-xs font-bold text-[#1E3A8A] backdrop-blur-xs">
        <Sparkles className="w-3.5 h-3.5 text-[#0EA5E9]" />
        <span>Peak Inflow: 310 Cases</span>
      </div>

      {/* Chart Canvas */}
      <div className="h-64 sm:h-72 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={trendData}
            margin={{ top: 20, right: 10, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorReceived" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#1E3A8A" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#1E3A8A" stopOpacity={0.0} />
              </linearGradient>
              <linearGradient id="colorDisposed" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0EA5E9" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#0EA5E9" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 11, fill: '#64748B', fontWeight: 600 }}
              axisLine={{ stroke: '#E2E8F0' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748B', fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
              ticks={[0, 100, 200, 300]}
              domain={[0, 350]}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#FFFFFF',
                borderRadius: '12px',
                border: '1px solid #E2E8F0',
                boxShadow: '0 10px 25px -5px rgba(30, 58, 138, 0.1)',
                fontSize: '12px',
                fontWeight: 600,
              }}
            />
            <Area
              type="monotone"
              dataKey="received"
              name="Received"
              stroke="#1E3A8A"
              strokeWidth={2.8}
              fill="url(#colorReceived)"
              activeDot={{ r: 6, stroke: '#1E3A8A', strokeWidth: 2, fill: '#FFFFFF' }}
            />
            <Area
              type="monotone"
              dataKey="disposed"
              name="Disposed"
              stroke="#0EA5E9"
              strokeWidth={2.4}
              fill="url(#colorDisposed)"
              activeDot={{ r: 5, stroke: '#0EA5E9', strokeWidth: 2, fill: '#FFFFFF' }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span>Target SLA turnaround: 10 days for C1/C2</span>
        <span className="font-semibold text-[#16A34A]">Disposal Rate: 82.4%</span>
      </div>
    </div>
  );
};
