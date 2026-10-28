'use client';

import React, { useState } from 'react';
import { AppLayout } from '@/components/layout/AppLayout';
import { useAuth } from '@/lib/auth';
import {
  mockBureauWorkload,
  mockRegionHeatmap,
  mockInstitutions,
  mockInstitutionRisks,
} from '@/lib/mock/data';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  BarChart3,
  Download,
  FileSpreadsheet,
  ShieldAlert,
  Building2,
  Layers,
  Clock,
} from 'lucide-react';

export default function ReportsPage() {
  const { hasRole, switchUser } = useAuth();
  const [reportType, setReportType] = useState<
    'bureau' | 'institution' | 'region' | 'ageing' | 'disposal'
  >('bureau');

  const isAuthorized = hasRole(['senior', 'authority', 'admin']);

  // Ageing bucket data
  const ageingData = [
    { bucket: '0 - 7 Days', count: 485, color: '#10b981' },
    { bucket: '8 - 15 Days', count: 320, color: '#3b82f6' },
    { bucket: '16 - 30 Days', count: 180, color: '#f59e0b' },
    { bucket: '31 - 60 Days', count: 85, color: '#f97316' },
    { bucket: '60+ Days (Overdue)', count: 48, color: '#ef4444' },
  ];

  const handleExportCSV = () => {
    alert(`Generating official AICTE CSV report for: ${reportType.toUpperCase()}...`);
  };

  const handleExportPDF = () => {
    alert(`Compiling official Government of India Dossier PDF for: ${reportType.toUpperCase()}...`);
  };

  if (!isAuthorized) {
    return (
      <AppLayout pageTitle="Reports & Analytics" hindiTitle="रिपोर्ट और विश्लेषण">
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
          <div className="mt-4 pt-4 border-t border-slate-200">
            <span className="text-xs font-semibold text-slate-700 block mb-2">
              For SIH Hackathon Evaluation, switch role:
            </span>
            <button
              onClick={() => switchUser('senior')}
              className="px-4 py-2 bg-[#1E3A8A] hover:bg-[#1e40af] text-white rounded text-xs font-bold shadow transition cursor-pointer"
            >
              Switch to Senior Management (Dr. Abhay Jere)
            </button>
          </div>
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout
      pageTitle="Executive Reports & Cross-Bureau Analytics"
      hindiTitle="कार्यकारी रिपोर्ट एवं विश्लेषण"
      actionButton={
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs font-bold hover:bg-emerald-100 transition shadow-xs cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            Export CSV
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-[#1E3A8A] text-white text-xs font-bold hover:bg-[#1e40af] transition shadow-xs cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            Official PDF Brief
          </button>
        </div>
      }
    >
      {/* 1. Report Category Selector */}
      <div className="flex items-center gap-2 mb-5 overflow-x-auto text-xs pb-1">
        {[
          { key: 'bureau', label: 'Bureau Workload & SLA', icon: Layers },
          { key: 'institution', label: 'High Risk Institutions', icon: Building2 },
          { key: 'region', label: 'Regional Distribution', icon: BarChart3 },
          { key: 'ageing', label: 'Pendency & Ageing Matrix', icon: Clock },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = reportType === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setReportType(tab.key as typeof reportType)}
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

      {/* 2. Visualizations and Tables based on reportType */}

      {/* Bureau Report */}
      {reportType === 'bureau' && (
        <div className="space-y-5">
          <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
            <h4 className="font-bold text-slate-800 text-sm mb-4">
              Bureau Disposal Compliance & Overdue Ratio
            </h4>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mockBureauWorkload}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="bureau" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: '11px' }} />
                  <Bar dataKey="disposed" name="Disposed" fill="#10b981" />
                  <Bar dataKey="pending" name="Pending" fill="#f59e0b" />
                  <Bar dataKey="overdue" name="Overdue" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0f172a] text-white text-[11px] uppercase font-semibold">
                <tr>
                  <th className="py-2.5 px-3">Bureau / Cell</th>
                  <th className="py-2.5 px-3">Total Inflow</th>
                  <th className="py-2.5 px-3">Disposed</th>
                  <th className="py-2.5 px-3">Pending</th>
                  <th className="py-2.5 px-3">Overdue</th>
                  <th className="py-2.5 px-3">Disposal Rate</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {mockBureauWorkload.map((b, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-bold text-slate-800">{b.bureau}</td>
                    <td className="py-2.5 px-3 font-semibold">{b.total}</td>
                    <td className="py-2.5 px-3 text-emerald-700 font-bold">{b.disposed}</td>
                    <td className="py-2.5 px-3 text-amber-700">{b.pending}</td>
                    <td className="py-2.5 px-3 text-red-700 font-bold">{b.overdue}</td>
                    <td className="py-2.5 px-3 font-bold text-[#1E3A8A]">
                      {b.total > 0 ? ((b.disposed / b.total) * 100).toFixed(1) : 0}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Ageing Report */}
      {reportType === 'ageing' && (
        <div className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
              <h4 className="font-bold text-slate-800 text-sm mb-4">
                Case Ageing Distribution (SLA SLA-Clock)
              </h4>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={ageingData}
                      dataKey="count"
                      nameKey="bucket"
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      label
                    >
                      {ageingData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend wrapperStyle={{ fontSize: '11px' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="bg-white rounded-lg border border-slate-200 p-5 shadow-sm">
              <h4 className="font-bold text-slate-800 text-sm mb-2">
                Executive SLA Pendency Breakdown
              </h4>
              <p className="text-xs text-slate-500 mb-4">
                Cases exceeding 30 days are automatically escalated to Senior Management digest.
              </p>

              <div className="space-y-3">
                {ageingData.map((item, i) => (
                  <div key={i} className="text-xs">
                    <div className="flex justify-between items-center mb-1">
                      <span className="font-bold text-slate-700">{item.bucket}</span>
                      <span className="font-extrabold text-slate-900">{item.count} cases</span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${(item.count / 485) * 100}%`,
                          backgroundColor: item.color,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* High Risk Institutions Report */}
      {reportType === 'institution' && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-white text-[11px] uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-3">Institution Name</th>
                <th className="py-2.5 px-3">Permanent ID</th>
                <th className="py-2.5 px-3">City & State</th>
                <th className="py-2.5 px-3">Risk Index (0-100)</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {mockInstitutions.map((inst) => {
                const r = mockInstitutionRisks[inst.id] || { risk_index: 25.0 };
                return (
                  <tr key={inst.id} className="hover:bg-slate-50">
                    <td className="py-2.5 px-3 font-bold text-slate-800">{inst.name}</td>
                    <td className="py-2.5 px-3 font-mono">{inst.permanent_id}</td>
                    <td className="py-2.5 px-3 text-slate-600">
                      {inst.city}, {inst.state}
                    </td>
                    <td className="py-2.5 px-3 font-extrabold text-red-700 text-sm">
                      {r.risk_index.toFixed(1)}
                    </td>
                    <td className="py-2.5 px-3">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-100 text-red-800">
                        High Scrutiny
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Regional Report */}
      {reportType === 'region' && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#0f172a] text-white text-[11px] uppercase font-semibold">
              <tr>
                <th className="py-2.5 px-3">Regional Office</th>
                <th className="py-2.5 px-3">State / UT</th>
                <th className="py-2.5 px-3">Total Cases</th>
                <th className="py-2.5 px-3">Overdue SLA</th>
                <th className="py-2.5 px-3">C1 Critical</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {mockRegionHeatmap.map((rm, i) => (
                <tr key={i} className="hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-bold text-slate-800">{rm.region}</td>
                  <td className="py-2.5 px-3">{rm.state}</td>
                  <td className="py-2.5 px-3 font-extrabold text-[#1E3A8A]">{rm.count}</td>
                  <td className="py-2.5 px-3 text-red-600 font-bold">{rm.overdue}</td>
                  <td className="py-2.5 px-3 text-amber-700 font-semibold">{rm.critical}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppLayout>
  );
}
