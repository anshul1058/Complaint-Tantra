'use client';

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2',
  {
    variants: {
      variant: {
        default: 'border-transparent bg-[#1E3A8A] text-white',
        secondary: 'border-transparent bg-[#e8eaf6] text-[#1E3A8A]',
        destructive: 'border-transparent bg-red-100 text-red-800 border-red-200',
        outline: 'text-slate-800 border-slate-300',
        success: 'border-transparent bg-green-100 text-green-800 border-green-200',
        warning: 'border-transparent bg-amber-100 text-amber-800 border-amber-200',
        saffron: 'border-transparent bg-orange-100 text-orange-800 border-orange-200',
        c1: 'border-red-300 bg-red-100 text-red-900 font-bold',
        c2: 'border-orange-300 bg-orange-100 text-orange-900 font-bold',
        c3: 'border-yellow-300 bg-yellow-100 text-yellow-900 font-bold',
        c4: 'border-green-300 bg-green-100 text-green-900 font-bold',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return <div className={cn(badgeVariants({ variant }), className)} {...props} />;
}

export { Badge, badgeVariants };
