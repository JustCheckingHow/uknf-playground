'use client';

import clsx from 'clsx';
import { Loader2 } from 'lucide-react';
import { ButtonHTMLAttributes, DetailedHTMLProps } from 'react';

type ButtonProps = DetailedHTMLProps<ButtonHTMLAttributes<HTMLButtonElement>, HTMLButtonElement> & {
  variant?: 'primary' | 'outline' | 'ghost';
  size?: 'sm' | 'md';
  isLoading?: boolean;
};

export function Button({ className, variant = 'primary', size = 'md', isLoading, children, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center justify-center rounded-md text-sm font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/80 disabled:cursor-not-allowed disabled:opacity-60',
        {
          'bg-primary text-white shadow hover:bg-primary/90': variant === 'primary',
          'border border-slate-300 bg-white text-slate-700 hover:bg-slate-50': variant === 'outline',
          'text-slate-600 hover:bg-slate-100': variant === 'ghost'
        },
        size === 'sm' ? 'px-3 py-2' : 'px-4 py-2',
        className
      )}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}
