'use client';

import * as React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

const buttonVariants = cva(
  'inline-flex items-center justify-center whitespace-nowrap rounded-xl text-xs font-bold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#0EA5E9] focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 cursor-pointer shadow-xs active:scale-[0.98]',
  {
    variants: {
      variant: {
        default: 'bg-[#1E3A8A] text-white hover:bg-[#1e40af] focus-visible:ring-[#1E3A8A]',
        saffron: 'bg-[#F59E0B] text-white hover:bg-[#d97706] focus-visible:ring-[#F59E0B]',
        green: 'bg-[#16A34A] text-white hover:bg-[#15803d] focus-visible:ring-[#16A34A]',
        destructive: 'bg-[#DC2626] text-white hover:bg-[#b91c1c] focus-visible:ring-[#DC2626]',
        outline: 'border border-slate-200 bg-white hover:bg-slate-50 text-slate-700',
        secondary: 'bg-[#EBF3FE] text-[#1E3A8A] hover:bg-[#dbeafe]',
        ghost: 'hover:bg-slate-100 text-slate-700 shadow-none',
        link: 'text-[#1E3A8A] underline-offset-4 hover:underline shadow-none',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 rounded-lg px-3 text-xs',
        lg: 'h-11 rounded-2xl px-6 text-sm',
        icon: 'h-9 w-9 p-0 rounded-full',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = 'Button';

export { Button, buttonVariants };
