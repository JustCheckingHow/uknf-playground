import { ReactNode } from 'react';

interface Column<T> {
  header: string;
  accessor: (row: T) => ReactNode;
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  emptyState?: ReactNode;
}

export function DataTable<T>({ columns, rows, emptyState }: DataTableProps<T>) {
  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-10 text-center text-sm text-slate-500 transition-colors dark:border-slate-800 dark:bg-slate-900/20 dark:text-slate-400">
        {emptyState ?? 'No data available'}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 transition-colors dark:border-slate-800">
      <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-800">
        <thead className="bg-slate-100 text-left text-xs uppercase tracking-wide text-slate-500 transition-colors dark:bg-slate-900/80 dark:text-slate-400">
          <tr>
            {columns.map((column) => (
              <th key={column.header} className="px-4 py-3 font-medium">
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200 bg-white text-sm text-slate-700 transition-colors dark:divide-slate-800 dark:bg-slate-950 dark:text-slate-200">
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="hover:bg-slate-100/60 dark:hover:bg-slate-900/40">
              {columns.map((column) => (
                <td key={column.header} className="px-4 py-3 align-top">
                  {column.accessor(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
