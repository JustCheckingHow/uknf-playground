import clsx from 'clsx';
import { HTMLAttributes } from 'react';

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: 'success' | 'warning' | 'danger' | 'info' | 'default';
};

const toneClasses: Record<NonNullable<BadgeProps['tone']>, string> = {
  success: 'bg-green-100 text-green-700 border-green-200',
  warning: 'bg-amber-100 text-amber-800 border-amber-200',
  danger: 'bg-red-100 text-red-700 border-red-200',
  info: 'bg-blue-100 text-blue-700 border-blue-200',
  default: 'bg-slate-100 text-slate-700 border-slate-200'
};

export function Badge({ className, tone = 'default', ...props }: BadgeProps) {
  return (
    <span
      className={clsx('inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium', toneClasses[tone], className)}
      {...props}
    />
  );
}
