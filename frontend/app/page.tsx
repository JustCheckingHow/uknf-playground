import Link from 'next/link';

const modules = [
  {
    name: 'Reports',
    description: 'Submit regulatory reports and track validation lifecycle.',
    href: '/reports'
  },
  {
    name: 'Messages',
    description: 'Secure bi-directional messaging with UKNF teams.',
    href: '/messages'
  },
  {
    name: 'Cases',
    description: 'Manage regulatory matters and follow-up actions.',
    href: '/cases'
  },
  {
    name: 'Announcements',
    description: 'Official notices with acknowledgement tracking.',
    href: '/announcements'
  },
  {
    name: 'Library',
    description: 'Reference documentation and guidance materials.',
    href: '/library'
  },
  {
    name: 'FAQ',
    description: 'Searchable repository of questions and answers.',
    href: '/faq'
  },
  {
    name: 'Entities',
    description: 'Maintain supervised entity profiles and contacts.',
    href: '/entities'
  }
];

export default function DashboardPage() {
  return (
    <section className="space-y-6">
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm transition-colors dark:border-slate-800 dark:bg-slate-900/60 dark:shadow-black/30">
        <h3 className="text-xl font-semibold text-white">Operational Overview</h3>
        <p className="mt-2 text-sm text-slate-300">
          The demo highlights the core communication capabilities between UKNF and supervised
          entities. Each module is wired to the backend REST API and designed with SSR-first Next.js
          architecture for accessibility, performance, and traceability.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {modules.map((module) => (
          <Link
            key={module.name}
            href={module.href}
            className="block rounded-lg border border-slate-200 bg-white p-5 transition hover:border-slate-300 hover:bg-slate-50 dark:border-slate-800 dark:bg-slate-900/40 dark:hover:border-slate-700 dark:hover:bg-slate-900"
          >
            <h4 className="text-lg font-medium text-slate-900 dark:text-white">{module.name}</h4>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{module.description}</p>
            <span className="mt-4 inline-flex items-center text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
              Explore
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}
