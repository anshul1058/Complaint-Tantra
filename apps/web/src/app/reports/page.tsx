'use client';

import React, { useCallback, useEffect, useState } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { useAuth } from '@/lib/auth';
import { downloadReport, getReport, ReportType } from '@/lib/api/client';
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  ShieldAlert,
  Building2,
  Layers,
  Clock,
} from 'lucide-react';

const REPORTS: { key: ReportType; label: string; icon: typeof Layers }[] = [
  { key: 'bureau', label: 'Bureau Workload & SLA', icon: Layers },
  { key: 'institution', label: 'High Risk Institutions', icon: Building2 },
  { key: 'region', label: 'Regional Distribution', icon: BarChart3 },
  { key: 'ageing', label: 'Pendency & Ageing Matrix', icon: Clock },
  { key: 'status', label: 'Status-wise', icon: Layers },
  { key: 'duplicates', label: 'Overlap / Duplicates', icon: BarChart3 },
  { key: 'performance', label: 'Disposal Performance', icon: Clock },
  { key: 'monthly', label: 'Monthly Trend', icon: BarChart3 },
];

export default function ReportsPage() {
  const { hasRole, switchUser } = useAuth();
  const [reportType, setReportType] = useState<ReportType>('bureau');
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const isAuthorized = hasRole(['senior', 'authority', 'admin']);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      setRows(await getReport(reportType));
    } catch (err) {
      setRows([]);
      setError(err instanceof Error ? err.message : 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }, [reportType]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (isAuthorized) load();
  }, [isAuthorized, load]);

  const exportReport = async (format: 'csv' | 'pdf') => {
    try {
      await downloadReport(reportType, format);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
    }
  };

  if (!isAuthorized) {
    return (
      <AppLayout pageTitle="Reports & Analytics">
        <div className="bg-white rounded-xl border border-amber-300 p-8 text-center max-w-xl mx-auto my-12 shadow-md">
          <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-800 flex items-center justify-center mx-auto mb-3">
            <ShieldAlert className="w-6 h-6 text-amber-700" />
          </div>
          <h3 className="font-bold text-slate-800 text-lg">
            Restricted Access: Senior Management / Competent Authority Only
          </h3>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed">
            Per AICTE RBAC policy (§8), organization-wide aggregate analytics and export permissions are restricted to Senior Management, Bureau Heads, and the Competent Authority.
          </p>
          <button
            onClick={() => switchUser('senior')}
            className="mt-4 px-4 py-2 bg-[#1E3A8A] hover:bg-[#1e40af] text-white rounded text-xs font-bold shadow transition cursor-pointer"
          >
            Switch to Senior Management
          </button>
        </div>
      </AppLayout>
    );
  }

  const columns = rows.length ? Object.keys(rows[0]) : [];

  return (
    <AppLayout
      pageTitle="Executive Reports & Cross-Bureau Analytics"
      actionButton={
        <div className="flex items-center gap-2">
          <button
            onClick={() => exportReport('csv')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs font-bold hover:bg-emerald-100 transition shadow-xs cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            Export CSV
          </button>
          <button
            onClick={() => exportReport('pdf')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#1E3A8A] text-white text-xs font-bold hover:bg-[#1e40af] transition shadow-xs cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Official PDF
          </button>
        </div>
      }
    >
      <div className="flex items-center gap-2 mb-5 overflow-x-auto text-xs pb-1">
        {REPORTS.map((tab) => {
          const Icon = tab.icon;
          const isActive = reportType === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setReportType(tab.key)}
              className={`flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-bold transition cursor-pointer ${
                isActive
                  ? 'bg-[#1E3A8A] text-white shadow'
                  : 'bg-white border border-slate-300 text-slate-700 hover:bg-slate-50'
              }`}
            >
              <Icon className="w-4 h-4 text-amber-400" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {error && (
        <div className="mb-4 text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          {error}
        </div>
      )}

      <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
        <table className="w-full text-left text-xs">
          <thead className="bg-[#0f172a] text-white text-[11px] uppercase font-semibold">
            <tr>
              {columns.map((col) => (
                <th key={col} className="py-2.5 px-3">{col.replaceAll('_', ' ')}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {rows.map((row, index) => (
              <tr key={index} className="hover:bg-slate-50">
                {columns.map((col) => (
                  <td key={col} className="py-2.5 px-3 text-slate-700">
                    {String(row[col] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr>
                <td colSpan={Math.max(columns.length, 1)} className="py-8 text-center text-slate-500">
                  No data available for this report.
                </td>
              </tr>
            )}
            {loading && (
              <tr>
                <td colSpan={Math.max(columns.length, 1)} className="py-8 text-center text-slate-500">
                  Loading report…
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </AppLayout>
  );
}
