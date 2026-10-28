'use client';

import React from 'react';

export const RashtrapatiBhavanSketch: React.FC<{
  className?: string;
  opacity?: number;
}> = ({ className = '', opacity = 0.2 }) => {
  return (
    <svg
      viewBox="0 0 800 240"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ opacity }}
      aria-hidden="true"
    >
      <g stroke="#0284C7" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round">
        {/* Ground & Terraces */}
        <line x1="20" y1="210" x2="780" y2="210" strokeWidth="1.8" />
        <line x1="50" y1="202" x2="750" y2="202" strokeWidth="1.2" />
        <line x1="90" y1="194" x2="710" y2="194" strokeWidth="1" />

        {/* Central Plinth & Steps */}
        <path d="M 320 210 L 330 190 L 470 190 L 480 210" />
        <line x1="335" y1="195" x2="465" y2="195" />
        <line x1="340" y1="200" x2="460" y2="200" />
        <line x1="345" y1="205" x2="455" y2="205" />

        {/* Central Dome & Drum */}
        {/* Top finial / flag staff */}
        <line x1="400" y1="20" x2="400" y2="55" strokeWidth="1.6" />
        <path d="M 400 25 L 420 32 L 400 39 Z" fill="#0EA5E9" fillOpacity="0.4" />
        <circle cx="400" cy="55" r="4" fill="#0284C7" fillOpacity="0.5" />
        {/* Chattri / Cupola above dome */}
        <path d="M 390 62 C 390 56 410 56 410 62 L 413 72 L 387 72 Z" />
        {/* Great Central Dome */}
        <path d="M 355 110 C 355 60 445 60 445 110 Z" strokeWidth="1.8" fill="#E0F2FE" fillOpacity="0.3" />
        <path d="M 370 110 C 370 75 430 75 430 110" strokeDasharray="3 3" />
        {/* Drum band with decorative motifs */}
        <rect x="350" y="110" width="100" height="18" rx="2" strokeWidth="1.4" />
        <line x1="360" y1="110" x2="360" y2="128" />
        <line x1="375" y1="110" x2="375" y2="128" />
        <line x1="390" y1="110" x2="390" y2="128" />
        <line x1="400" y1="110" x2="400" y2="128" strokeWidth="1.6" />
        <line x1="410" y1="110" x2="410" y2="128" />
        <line x1="425" y1="110" x2="425" y2="128" />
        <line x1="440" y1="110" x2="440" y2="128" />

        {/* Portico Pediment (Triangular Gable) */}
        <path d="M 325 140 L 400 120 L 475 140 Z" strokeWidth="1.8" fill="#F0F9FF" fillOpacity="0.4" />
        <circle cx="400" cy="132" r="4" strokeWidth="1" />

        {/* Central Portico Colonnade (Classical Pillars) */}
        <line x1="335" y1="140" x2="335" y2="190" strokeWidth="2.2" />
        <line x1="350" y1="140" x2="350" y2="190" strokeWidth="2" />
        <line x1="365" y1="140" x2="365" y2="190" strokeWidth="2" />
        <line x1="380" y1="140" x2="380" y2="190" strokeWidth="2" />
        <line x1="395" y1="140" x2="395" y2="190" strokeWidth="2" />
        <line x1="405" y1="140" x2="405" y2="190" strokeWidth="2" />
        <line x1="420" y1="140" x2="420" y2="190" strokeWidth="2" />
        <line x1="435" y1="140" x2="435" y2="190" strokeWidth="2" />
        <line x1="450" y1="140" x2="450" y2="190" strokeWidth="2" />
        <line x1="465" y1="140" x2="465" y2="190" strokeWidth="2.2" />

        {/* Left Wing (Rashtrapati Bhavan / North Block style colonnade) */}
        <rect x="110" y="148" width="215" height="42" strokeWidth="1.2" />
        {/* Left Chattri / Dome Pavilion */}
        <path d="M 170 148 C 170 125 210 125 210 148 Z" fill="#E0F2FE" fillOpacity="0.25" />
        <line x1="190" y1="115" x2="190" y2="128" />
        <path d="M 120 148 L 120 190" strokeWidth="1.8" />
        <path d="M 135 148 L 135 190" strokeWidth="1.4" />
        <path d="M 150 148 L 150 190" strokeWidth="1.4" />
        <path d="M 165 148 L 165 190" strokeWidth="1.4" />
        <path d="M 180 148 L 180 190" strokeWidth="1.4" />
        <path d="M 195 148 L 195 190" strokeWidth="1.4" />
        <path d="M 210 148 L 210 190" strokeWidth="1.4" />
        <path d="M 225 148 L 225 190" strokeWidth="1.4" />
        <path d="M 240 148 L 240 190" strokeWidth="1.4" />
        <path d="M 255 148 L 255 190" strokeWidth="1.4" />
        <path d="M 270 148 L 270 190" strokeWidth="1.4" />
        <path d="M 285 148 L 285 190" strokeWidth="1.4" />
        <path d="M 300 148 L 300 190" strokeWidth="1.4" />
        <path d="M 315 148 L 315 190" strokeWidth="1.8" />

        {/* Right Wing (South Block style colonnade) */}
        <rect x="475" y="148" width="215" height="42" strokeWidth="1.2" />
        {/* Right Chattri / Dome Pavilion */}
        <path d="M 590 148 C 590 125 630 125 630 148 Z" fill="#E0F2FE" fillOpacity="0.25" />
        <line x1="610" y1="115" x2="610" y2="128" />
        <path d="M 485 148 L 485 190" strokeWidth="1.8" />
        <path d="M 500 148 L 500 190" strokeWidth="1.4" />
        <path d="M 515 148 L 515 190" strokeWidth="1.4" />
        <path d="M 530 148 L 530 190" strokeWidth="1.4" />
        <path d="M 545 148 L 545 190" strokeWidth="1.4" />
        <path d="M 560 148 L 560 190" strokeWidth="1.4" />
        <path d="M 575 148 L 575 190" strokeWidth="1.4" />
        <path d="M 590 148 L 590 190" strokeWidth="1.4" />
        <path d="M 605 148 L 605 190" strokeWidth="1.4" />
        <path d="M 620 148 L 620 190" strokeWidth="1.4" />
        <path d="M 635 148 L 635 190" strokeWidth="1.4" />
        <path d="M 650 148 L 650 190" strokeWidth="1.4" />
        <path d="M 665 148 L 665 190" strokeWidth="1.4" />
        <path d="M 680 148 L 680 190" strokeWidth="1.8" />

        {/* Outer Gate Towers & Parapets */}
        <path d="M 90 194 L 90 156 L 110 156 L 110 194" />
        <line x1="90" y1="152" x2="110" y2="152" strokeWidth="2" />
        <path d="M 690 194 L 690 156 L 710 156 L 710 194" />
        <line x1="690" y1="152" x2="710" y2="152" strokeWidth="2" />

        {/* Subtle decorative birds / clouds */}
        <path d="M 240 60 Q 248 54 256 60 Q 264 54 272 60" strokeWidth="0.8" />
        <path d="M 540 50 Q 546 45 552 50 Q 558 45 564 50" strokeWidth="0.8" />
      </g>
    </svg>
  );
};

export const IndiaMapOutline: React.FC<{
  className?: string;
  opacity?: number;
}> = ({ className = '', opacity = 0.15 }) => {
  return (
    <svg
      viewBox="0 0 200 240"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={{ opacity }}
      aria-hidden="true"
    >
      <path
        d="M 95 10 C 105 15 110 25 115 28 C 122 32 135 34 138 42 C 142 50 136 58 140 66 C 145 74 165 72 172 80 C 178 88 168 96 160 102 C 150 108 142 104 135 112 C 130 118 132 128 128 136 C 124 144 116 156 112 168 C 108 180 102 196 98 212 C 96 220 94 228 92 232 C 90 228 86 218 82 208 C 76 192 70 178 66 164 C 62 152 56 142 50 132 C 45 122 36 118 32 108 C 28 98 32 90 38 82 C 44 74 54 70 58 60 C 62 50 68 36 74 24 C 80 15 88 10 95 10 Z"
        stroke="#0EA5E9"
        strokeWidth="1.5"
        strokeDasharray="4 3"
        fill="#E0F2FE"
        fillOpacity="0.1"
      />
      {/* Ashoka Chakra in centre */}
      <circle cx="98" cy="120" r="14" stroke="#0284C7" strokeWidth="1" strokeDasharray="2 2" />
      <circle cx="98" cy="120" r="3" fill="#0284C7" />
    </svg>
  );
};
