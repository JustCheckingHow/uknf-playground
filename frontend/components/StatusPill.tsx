interface StatusPillProps {
  status: string;
}

const STATUS_STYLES: Record<string, string> = {
  Draft: 'bg-slate-200 text-slate-800 dark:bg-slate-700 dark:text-slate-100',
  Submitted: 'bg-blue-100 text-blue-700 dark:bg-blue-600/20 dark:text-blue-100',
  Validated: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-600/20 dark:text-emerald-100',
  'Validation Error': 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-200',
  Rejected: 'bg-rose-100 text-rose-700 dark:bg-rose-600/20 dark:text-rose-100'
};

export function StatusPill({ status }: StatusPillProps) {
  const normalized = status.trim();
  const colors =
    STATUS_STYLES[normalized] ?? 'bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200';

  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors ${colors}`}>
      {normalized}
    </span>
  );
}
