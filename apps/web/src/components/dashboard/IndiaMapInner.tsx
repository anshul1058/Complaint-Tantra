'use client';

import React from 'react';
import { CircleMarker, MapContainer, TileLayer, Tooltip } from 'react-leaflet';
import { RegionHeatmapData } from '@/lib/types';

const STATE_CENTER: Record<string, [number, number]> = {
  'Andaman and Nicobar Islands': [11.74, 92.66],
  'Andhra Pradesh': [15.91, 79.74],
  'Arunachal Pradesh': [28.22, 94.73],
  Assam: [26.2, 92.94],
  Bihar: [25.1, 85.31],
  Chandigarh: [30.73, 76.78],
  Chhattisgarh: [21.28, 81.87],
  'Dadra and Nagar Haveli': [20.18, 73.02],
  'Daman and Diu': [20.43, 72.84],
  Delhi: [28.61, 77.21],
  Goa: [15.3, 74.12],
  Gujarat: [22.26, 71.19],
  Haryana: [29.06, 76.09],
  'Himachal Pradesh': [31.1, 77.17],
  'Jammu and Kashmir': [33.78, 76.58],
  Jharkhand: [23.61, 85.28],
  Karnataka: [15.32, 75.71],
  Kerala: [10.85, 76.27],
  Ladakh: [34.15, 77.58],
  'Madhya Pradesh': [23.47, 78.66],
  Maharashtra: [19.75, 75.71],
  Manipur: [24.66, 93.91],
  Meghalaya: [25.47, 91.37],
  Mizoram: [23.16, 92.94],
  Nagaland: [26.16, 94.56],
  Odisha: [20.95, 85.1],
  Puducherry: [11.94, 79.81],
  Punjab: [31.15, 75.34],
  Rajasthan: [27.02, 74.22],
  Sikkim: [27.53, 88.51],
  'Tamil Nadu': [11.13, 78.66],
  Telangana: [18.11, 79.02],
  Tripura: [23.94, 91.99],
  'Uttar Pradesh': [26.85, 80.91],
  Uttarakhand: [30.07, 79.02],
  'West Bengal': [22.99, 87.85],
};

export const IndiaMapInner: React.FC<{ data: RegionHeatmapData[] }> = ({ data }) => {
  const max = Math.max(...data.map((d) => d.count), 1);

  return (
    <MapContainer
      center={[22.5, 80]}
      zoom={4}
      scrollWheelZoom={false}
      className="h-[340px] w-full rounded-xl z-0"
    >
      <TileLayer
        attribution='&copy; OpenStreetMap contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {data.map((row) => {
        const center = STATE_CENTER[row.state];
        if (!center) return null;
        const ratio = row.count / max;
        const criticalShare = row.count ? row.critical / row.count : 0;
        const overdueShare = row.count ? row.overdue / row.count : 0;
        const color =
          criticalShare >= 0.2 ? '#dc2626' : overdueShare >= 0.3 ? '#d97706' : '#2563eb';
        return (
          <CircleMarker
            key={`${row.region}-${row.state}`}
            center={center}
            radius={7 + Math.sqrt(ratio) * 18}
            pathOptions={{
              color: '#ffffff',
              weight: 1.5,
              fillColor: color,
              fillOpacity: 0.72,
            }}
          >
            <Tooltip direction="top" opacity={1}>
              <div className="text-xs">
                <strong>{row.state}</strong>
                <br />
                {row.count} cases · {row.overdue} overdue · {row.critical} critical
              </div>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
};
