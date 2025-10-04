interface PageHeaderProps {
  title: string;
  description?: string;
}

export function PageHeader({ title, description }: PageHeaderProps) {
  return (
    <div className="mb-6 space-y-2">
      <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">{title}</h1>
      {description ? <p className="text-sm text-slate-600 dark:text-slate-300">{description}</p> : null}
    </div>
  );
}
