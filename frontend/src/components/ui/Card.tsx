import clsx from 'clsx';
import { HTMLAttributes } from 'react';

type CardProps = HTMLAttributes<HTMLDivElement> & {
  variant?: 'default' | 'muted';
};

export function Card({ className, variant = 'default', ...props }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-lg border border-slate-200 bg-white p-6 shadow-sm',
        variant === 'muted' && 'border-dashed bg-slate-50',
        className
      )}
      {...props}
    />
  );
}
