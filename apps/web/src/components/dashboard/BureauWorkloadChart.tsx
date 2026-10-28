'use client';

import React from 'react';
import { BureauWorkload } from '@/lib/types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Building2 } from 'lucide-react';

interface BureauWorkloadChartProps {
  data: BureauWorkload[];
}

export const BureauWorkloadChart: React.FC<BureauWorkloadChartProps> = ({ data }) => {
  const totalLoad = data.reduce((acc, curr) => acc + (curr.total || 0), 0);

  return (
    <div className="bg-white/95 backdrop-blur-xs rounded-2xl p-5 border border-slate-200/80 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)]">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between pb-3 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#E0F2FE] text-[#0284C7] flex items-center justify-center">
              <Building2 className="w-4 h-4" />
            </div>
            <h3 className="font-extrabold text-[#1E3A8A] text-sm md:text-base tracking-tight">
              Bureau Grievance Workload Distribution
            </h3>
          </div>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            ब्यूरो-वार कार्यभार एवं निस्तारण स्थिति • Live SQL Aggregation across 6 cells
          </p>

          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 tracking-tight">
              {totalLoad.toLocaleString('en-IN')}{' '}
              <span className="text-sm font-bold text-slate-500">Active Grievances</span>
            </span>
            <span className="text-xs font-bold text-[#16A34A] bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              6 Active Cells
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 font-medium">
          <span className="px-2.5 py-1 bg-slate-50 rounded-lg border border-slate-200">
            Highest: PGRC Cell
          </span>
        </div>
      </div>

      {/* Bar Chart Canvas */}
      <div className="h-64 sm:h-72 w-full mt-2">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 20, right: 10, left: -20, bottom: 20 }}
            barGap={3}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
            <XAxis
              dataKey="bureau"
              tick={{ fontSize: 11, fill: '#64748B', fontWeight: 600 }}
              axisLine={{ stroke: '#E2E8F0' }}
              tickLine={false}
              interval={0}
            />
            <YAxis
              tick={{ fontSize: 11, fill: '#64748B', fontWeight: 600 }}
              axisLine={false}
              tickLine={false}
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
            <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
            <Bar
              dataKey="pending"
              name="Pending (लंबित)"
              fill="#F59E0B"
              stackId="a"
            />
            <Bar
              dataKey="under_process"
              name="Under Process (प्रक्रियाधीन)"
              fill="#0EA5E9"
              stackId="a"
            />
            <Bar
              dataKey="disposed"
              name="Disposed (निस्तारित)"
              fill="#16A34A"
              stackId="a"
            />
            <Bar
              dataKey="overdue"
              name="Overdue (ओवरड्यू)"
              fill="#DC2626"
              radius={[4, 4, 0, 0]}
              stackId="a"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span>* Event-driven cross-bureau synchronization via AICTE Message Broker</span>
        <span className="font-semibold text-slate-700">Real-time DB Connection</span>
      </div>
    </div>
  );
};
