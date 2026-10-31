'use client';

import React, { useState } from 'react';
import { RegionHeatmapData } from '@/lib/types';
import { MapPin, AlertCircle, Compass } from 'lucide-react';

interface RegionHeatmapProps {
  data: RegionHeatmapData[];
}

export const RegionHeatmap: React.FC<RegionHeatmapProps> = ({ data }) => {
  const [selectedRegion, setSelectedRegion] = useState<string>('ALL');

  const filteredData =
    selectedRegion === 'ALL'
      ? data
      : data.filter((d) => d.region === selectedRegion);

  const maxCount = Math.max(...data.map((d) => d.count), 1);

  return (
    <div className="bg-white/95 backdrop-blur-xs rounded-2xl border border-slate-200/80 p-5 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)]">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-slate-100 mb-4 gap-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-sky-50 text-[#0284C7] flex items-center justify-center">
            <MapPin className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-extrabold text-[#1E3A8A] text-sm md:text-base tracking-tight">
              National Grievance Density & Regional Offices (ROs)
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              अखिल भारतीय क्षेत्रीय वितरण • Geo-Locus Scrutiny & Inflow
            </p>
          </div>
        </div>

        {/* Region Filter Buttons */}
        <div className="flex items-center gap-1 overflow-x-auto text-xs">
          {['ALL', 'Northern', 'Western', 'Southern', 'Eastern', 'Central'].map(
            (r) => (
              <button
                type="button"
                key={r}
                onClick={() => setSelectedRegion(r)}
                className={`px-3 py-1 rounded-full transition cursor-pointer text-xs font-bold ${
                  selectedRegion === r
                    ? 'bg-[#1E3A8A] text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {r}
              </button>
            )
          )}
        </div>
      </div>

      {/* Grid of Regional States */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
        {filteredData.map((item, idx) => {
          const intensityPercent = Math.round((item.count / maxCount) * 100);

          return (
            <div
              key={idx}
              className="p-3.5 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-white hover:border-sky-300 hover:shadow-sm transition-all cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 flex items-center gap-1">
                    <Compass className="w-3 h-3 text-[#0EA5E9]" />
                    {item.region} Region
                  </span>
                  <h4 className="font-bold text-slate-900 text-sm mt-0.5">
                    {item.state}
                  </h4>
                </div>

                <div className="text-right">
                  <span className="text-base font-black text-[#1E3A8A]">
                    {item.count}
                  </span>
                  <span className="text-[10px] text-slate-400 block font-medium">cases</span>
                </div>
              </div>

              {/* Intensity Bar */}
              <div className="mt-2.5">
                <div className="w-full bg-slate-200/70 h-2 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-sky-400 to-[#1E3A8A] rounded-full transition-all duration-500"
                    style={{ width: `${intensityPercent}%` }}
                  />
                </div>
              </div>

              <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500 pt-1.5 border-t border-slate-200/60 font-medium">
                <span className="flex items-center gap-1 text-[#DC2626] font-bold">
                  <AlertCircle className="w-3 h-3" />
                  {item.overdue} Overdue
                </span>
                <span className="text-amber-800 font-semibold">
                  {item.critical} C1-Critical
                </span>
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-3.5 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span>* Geospatial density synchronized with AICTE Institution Master</span>
        <span className="font-semibold text-slate-700">Highest Inflow: Maharashtra (315)</span>
      </div>
    </div>
  );
};
