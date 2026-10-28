'use client';

import React from 'react';

export const TricolorRibbonWave: React.FC<{
  className?: string;
  width?: number;
  height?: number;
}> = ({ className = '', width = 120, height = 18 }) => {
  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 160 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      {/* Saffron Ribbon Curve */}
      <path
        d="M 2 18 C 40 4, 90 24, 158 8"
        stroke="#FF9933"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
      {/* White / Silver Middle Ribbon */}
      <path
        d="M 2 20 C 40 6, 90 26, 158 10"
        stroke="#CBD5E1"
        strokeWidth="2.5"
        strokeLinecap="round"
      />
      {/* Green Ribbon Curve */}
      <path
        d="M 2 22 C 40 8, 90 28, 158 12"
        stroke="#138808"
        strokeWidth="3.2"
        strokeLinecap="round"
      />
    </svg>
  );
};
