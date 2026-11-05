'use client';

import dynamic from 'next/dynamic';
import { RegionHeatmapData } from '@/lib/types';

const Inner = dynamic(
  () => import('./IndiaMapInner').then((mod) => mod.IndiaMapInner),
  {
    ssr: false,
    loading: () => (
      <div className="h-[340px] rounded-xl bg-slate-100 animate-pulse" />
    ),
  }
);

export const IndiaMap: React.FC<{ data: RegionHeatmapData[] }> = ({ data }) => (
  <Inner data={data} />
);
