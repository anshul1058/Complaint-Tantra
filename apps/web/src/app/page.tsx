'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { KPICards } from '@/components/dashboard/KPICards';
import { TrendChart } from '@/components/dashboard/TrendChart';
import { BureauWorkloadChart } from '@/components/dashboard/BureauWorkloadChart';
import { StatusSummaryCard } from '@/components/dashboard/StatusSummaryCard';
import { TodoRemindersCard } from '@/components/dashboard/TodoRemindersCard';
import { RegionHeatmap } from '@/components/dashboard/RegionHeatmap';
import { DataDecisionsBanner } from '@/components/dashboard/DataDecisionsBanner';
import {
  getDashboardSummary,
  getBureauWorkload,
  getRegionHeatmap,
  getAlerts,
} from '@/lib/api/client';
import {
  DashboardSummary,
  BureauWorkload,
  RegionHeatmapData,
  Alert,
} from '@/lib/types';
import {
  mockDashboardSummary,
  mockBureauWorkload,
  mockRegionHeatmap,
  mockAlerts,
} from '@/lib/mock/data';
import { RefreshCw, ArrowRight, ShieldCheck } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary>(mockDashboardSummary);
  const [workload, setWorkload] = useState<BureauWorkload[]>(mockBureauWorkload);
  const [heatmap, setHeatmap] = useState<RegionHeatmapData[]>(mockRegionHeatmap);
  const [alerts, setAlerts] = useState<Alert[]>(mockAlerts);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [s, w, h, a] = await Promise.all([
        getDashboardSummary(),
        getBureauWorkload(),
        getRegionHeatmap(),
        getAlerts(),
      ]);
      setSummary(s);
      setWorkload(w);
      setHeatmap(h);
      setAlerts(a);
    } catch {
      // fallback
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const timer = setInterval(() => {
      loadData();
    }, 30000);
    return () => clearInterval(timer);
  }, [loadData]);

  return (
    <AppLayout
      actionButton={
        <div className="flex items-center gap-2">
          <button
            onClick={loadData}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 text-xs font-semibold shadow-2xs transition cursor-pointer"
          >
            <RefreshCw
              className={`w-3.5 h-3.5 text-[#0EA5E9] ${
                isRefreshing ? 'animate-spin' : ''
              }`}
            />
            Live Sync (30s)
          </button>

          <Link
            href="/queue"
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#1E3A8A] hover:bg-[#1e40af] text-white text-xs font-bold shadow-xs transition"
          >
            <span>Priority Queue</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      }
    >
      {/* 1. TOP METRIC CARDS ROW: Real Live KPI metrics with reference design styling */}
      <KPICards summary={summary} />

      {/* 2. MIDDLE TWO-COLUMN GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mb-5 items-start">
        
        {/* Left Column (8 cols / 66.6%): Trend Trajectory & Bureau Workload */}
        <div className="lg:col-span-8 space-y-5">
          {/* 6-Month Intake vs Disposal Area Curve with Floating Peak Badge */}
          <TrendChart />

          {/* Bureau-wise Grievance Workload Distribution */}
          <BureauWorkloadChart data={workload} />
        </div>

        {/* Right Column (4 cols / 33.3%): Status Summary & Interactive Action Feeds */}
        <div className="lg:col-span-4 space-y-5">
          {/* Status Summary with Sparkline & Progress Donuts */}
          <StatusSummaryCard summary={summary} />

          {/* Real-time Triage Action Items from API Alerts */}
          <TodoRemindersCard alerts={alerts} />
        </div>

      </div>

      {/* 3. BOTTOM SECTION: Geographic Density & Decisional Quote */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 mb-6 items-stretch">
        
        {/* Left (8 cols): National Grievance Density across Regional Offices */}
        <div className="lg:col-span-8">
          <RegionHeatmap data={heatmap} />
        </div>

        {/* Right (4 cols): National Motto & Tricolor Branding */}
        <div className="lg:col-span-4">
          <DataDecisionsBanner />
        </div>

      </div>

      {/* 4. SIH 2024 EVALUATOR QUICK TOUR BANNER */}
      <div className="bg-gradient-to-r from-sky-50 via-white to-blue-50 border border-sky-200/80 rounded-2xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs shadow-2xs">
        <div className="flex items-center gap-2.5">
          <ShieldCheck className="w-5 h-5 text-[#1E3A8A]" />
          <div>
            <span className="font-extrabold text-[#1E3A8A] uppercase tracking-wide">
              Smart India Hackathon Evaluator Tour:
            </span>
            <span className="text-slate-600 block sm:inline sm:ml-1 font-medium">
              Explore the full AICTE complaint lifecycle in under 3 minutes.
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/queue"
            className="px-3 py-1.5 bg-white border border-slate-200 text-[#1E3A8A] font-bold rounded-xl hover:bg-sky-50 hover:border-sky-300 transition shadow-2xs"
          >
            1. Scored Queue &rarr;
          </Link>
          <Link
            href="/cases/case-001"
            className="px-3 py-1.5 bg-white border border-slate-200 text-[#1E3A8A] font-bold rounded-xl hover:bg-sky-50 hover:border-sky-300 transition shadow-2xs"
          >
            2. AI Case Brief &rarr;
          </Link>
          <Link
            href="/overlaps"
            className="px-3.5 py-1.5 bg-[#1E3A8A] text-white font-bold rounded-xl hover:bg-[#1e40af] transition shadow-xs"
          >
            3. Overlap Room &rarr;
          </Link>
        </div>
      </div>
    </AppLayout>
  );
}
