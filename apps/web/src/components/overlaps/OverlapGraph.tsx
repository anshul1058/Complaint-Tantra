'use client';

import React, { useMemo } from 'react';
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
} from '@xyflow/react';
import { CaseLink } from '@/lib/types';
import { GitMerge } from 'lucide-react';

const TIER_COLOR: Record<string, string> = {
  T1: '#dc2626',
  T2: '#d97706',
  T3: '#2563eb',
};

export const OverlapGraph: React.FC<{ links: CaseLink[] }> = ({ links }) => {
  const { nodes, edges } = useMemo(() => {
    const ids = new Map<string, { caseNo: string; bureau: string; tier: string }>();
    for (const link of links) {
      for (const [id, details] of [
        [link.case_a, link.case_a_details],
        [link.case_b, link.case_b_details],
      ] as const) {
        const current = ids.get(id);
        if (!current || link.tier === 'T1') {
          ids.set(id, {
            caseNo: details?.case_no || id.slice(0, 8),
            bureau: details?.assigned_bureau || 'Unknown bureau',
            tier: link.tier,
          });
        }
      }
    }

    const list = [...ids.entries()];
    const radius = Math.max(220, list.length * 22);
    const graphNodes: Node[] = list.map(([id, meta], index) => {
      const angle = (2 * Math.PI * index) / Math.max(list.length, 1);
      const color = TIER_COLOR[meta.tier] || '#475569';
      return {
        id,
        position: {
          x: Math.cos(angle) * radius,
          y: Math.sin(angle) * radius,
        },
        data: { label: `${meta.caseNo}\n${meta.bureau}` },
        style: {
          width: 168,
          padding: 8,
          borderRadius: 12,
          border: `2px solid ${color}`,
          background: '#ffffff',
          color: '#0f172a',
          fontSize: 11,
          fontWeight: 700,
          whiteSpace: 'pre-line',
          textAlign: 'center',
        },
      };
    });

    const graphEdges: Edge[] = links
      .filter((link) => ids.has(link.case_a) && ids.has(link.case_b))
      .map((link) => ({
        id: link.id,
        source: link.case_a,
        target: link.case_b,
        type: 'default',
        animated: link.tier === 'T1',
        label: `${link.tier} ${(link.confidence * 100).toFixed(0)}%`,
        labelStyle: { fontSize: 10, fontWeight: 700 },
        labelBgStyle: { fill: '#ffffff', fillOpacity: 0.9 },
        style: {
          stroke: TIER_COLOR[link.tier] || '#475569',
          strokeWidth: link.tier === 'T1' ? 2.4 : 1.6,
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: TIER_COLOR[link.tier] || '#475569',
        },
      }));

    return { nodes: graphNodes, edges: graphEdges };
  }, [links]);

  if (!links.length) {
    return (
      <div className="bg-white rounded-lg border border-dashed border-slate-300 p-8 text-center text-xs text-slate-500 mb-5">
        No overlap links for this tier yet.
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm mb-5 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-800">
          <GitMerge className="w-4 h-4 text-purple-700" />
          Overlap Network
          <span className="font-medium text-slate-500">
            {nodes.length} cases · {edges.length} links
          </span>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-semibold text-slate-600">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-600" />T1</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-amber-600" />T2</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-blue-600" />T3</span>
        </div>
      </div>
      <div className="h-[420px] bg-slate-50">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          minZoom={0.25}
          nodesConnectable={false}
          elementsSelectable
        >
          <Background gap={18} color="#cbd5e1" />
          <MiniMap pannable zoomable />
          <Controls showInteractive={false} />
        </ReactFlow>
      </div>
    </div>
  );
};
