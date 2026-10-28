'use client';

import React from 'react';
import { GovHeader } from '@/components/layout/GovHeader';
import { AppSidebar } from '@/components/layout/AppSidebar';
import { SLAAlertStrip } from '@/components/layout/SLAAlertStrip';

interface AppLayoutProps {
  children: React.ReactNode;
  pageTitle?: string;
  hindiTitle?: string;
  actionButton?: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  pageTitle,
  hindiTitle,
  actionButton,
}) => {
  return (
    <div className="min-h-screen flex flex-col bg-[#F3F7FD] text-slate-900 selection:bg-sky-100 selection:text-[#1E3A8A]">
      {/* Official AICTE & Government of India Header */}
      <GovHeader />

      {/* Global Live SLA Alert Strip (compact, sleek) */}
      <SLAAlertStrip />

      {/* Main Body Grid */}
      <div className="flex-1 flex w-full max-w-[1720px] mx-auto">
        {/* Left Sidebar Navigation */}
        <AppSidebar className="hidden md:flex shrink-0" />

        {/* Dynamic Center Stage */}
        <main className="flex-1 p-4 sm:p-6 lg:p-7 overflow-x-hidden">
          {pageTitle && (
            <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b border-slate-200/80">
              <div>
                <div className="flex items-center gap-2.5">
                  <h1 className="text-xl md:text-2xl font-extrabold text-[#1E3A8A] tracking-tight">
                    {pageTitle}
                  </h1>
                  {hindiTitle && (
                    <span className="text-xs font-bold text-sky-800 bg-sky-50 px-2 py-0.5 rounded border border-sky-200">
                      {hindiTitle}
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-1 font-medium">
                  Central Monitoring & Triage Grid • Live AICTE Data Lake Sync
                </p>
              </div>

              {actionButton && <div>{actionButton}</div>}
            </div>
          )}

          {children}
        </main>
      </div>

      {/* Modern, Clean Gov Footer */}
      <footer className="bg-white border-t border-slate-200/80 text-slate-500 text-xs py-4 px-6 mt-auto">
        <div className="max-w-[1720px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <div className="flex items-center gap-2">
            <span className="font-bold text-[#1E3A8A]">शिकायत-तंत्र | Complaint-Tantra</span>
            <span className="text-slate-300">•</span>
            <span className="text-slate-500 text-[11px]">
              AICTE Integrated Grievance Scrutiny & Bureau Overlap Platform
            </span>
          </div>

          <div className="flex items-center gap-3 text-[11px] font-medium text-slate-400">
            <span className="text-[#1E3A8A] font-serif font-bold">सत्यमेव जयते</span>
            <span>•</span>
            <span className="text-emerald-700 font-semibold">Digital India</span>
            <span>•</span>
            <span>Smart India Hackathon</span>
          </div>
        </div>
      </footer>
    </div>
  );
};
