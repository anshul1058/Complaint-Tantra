'use client';

import React from 'react';
import { Compass } from 'lucide-react';
import { TricolorRibbonWave } from '@/components/layout/TricolorRibbon';
import { IndiaMapOutline } from '@/components/layout/GovWatermark';

export const DataDecisionsBanner: React.FC = () => {
  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-sky-50/90 via-blue-50/60 to-indigo-50/70 rounded-2xl p-6 border border-sky-200/70 shadow-[0_2px_12px_-2px_rgba(30,58,138,0.04)] flex flex-col justify-between min-h-[140px]">
      {/* India Map Silhouette Watermark in Background */}
      <div className="absolute right-8 -top-8 w-44 pointer-events-none opacity-20">
        <IndiaMapOutline opacity={0.35} />
      </div>

      <div className="relative z-10 flex items-start justify-between">
        <div>
          <blockquote
            className="text-base sm:text-lg font-bold text-[#1E3A8A] italic tracking-tight font-serif"
            style={{ fontFamily: 'Playfair Display, Georgia, serif' }}
          >
            &ldquo;Data today, better decisions tomorrow.&rdquo;
          </blockquote>
          <p className="text-[11px] font-medium text-slate-500 mt-1">
            Empowering technical education governance through AI triage
          </p>
        </div>

        {/* Circular Compass Element */}
        <div className="w-9 h-9 rounded-full bg-white/80 border border-sky-200 flex items-center justify-center text-[#0284C7] shadow-2xs shrink-0">
          <Compass className="w-5 h-5 text-sky-600 animate-spin-slow" />
        </div>
      </div>

      {/* Tricolor Ribbon Wave in Bottom Left */}
      <div className="relative z-10 mt-4">
        <TricolorRibbonWave width={130} height={16} />
      </div>
    </div>
  );
};
