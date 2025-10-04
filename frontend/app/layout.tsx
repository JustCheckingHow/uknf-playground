import './globals.css';
import Image from 'next/image';
import Link from 'next/link';
import { ReactNode } from 'react';

import { ThemeToggle } from '@/components/ThemeToggle';
import { ThemeProvider } from '@/components/theme-provider';

const navigation = [
  { href: '/', label: 'Overview' },
  { href: '/reports', label: 'Reports' },
  { href: '/messages', label: 'Messages' },
  { href: '/cases', label: 'Cases' },
  { href: '/announcements', label: 'Announcements' },
  { href: '/library', label: 'Library' },
  { href: '/faq', label: 'FAQ' },
  { href: '/entities', label: 'Entities' }
];

export const metadata = {
  title: 'UKNF Communication Platform',
  description: 'Demo regulatory communication portal'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-50 text-slate-900 transition-colors duration-200 dark:bg-slate-950 dark:text-slate-100">
        <ThemeProvider>
          <div className="flex min-h-screen">
            <aside className="hidden w-72 flex-col border-r border-slate-200 bg-slate-100 p-6 transition-colors dark:border-slate-800 dark:bg-slate-900 sm:flex">
              <div className="flex items-center gap-3">
                <Image
                  src="/knf_logo.png"
                  alt="Polish Financial Supervision Authority (UKNF) logo"
                  width={140}
                  height={40}
                  priority
                  className="h-9 w-auto"
                />
                <span className="sr-only">UKNF Platform</span>
              </div>
              <nav className="mt-6 flex flex-1 flex-col gap-2 text-sm transition-colors">
                {navigation.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    className="rounded px-3 py-2 font-medium text-slate-600 transition-colors hover:bg-slate-200 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                  >
                    {item.label}
                  </Link>
                ))}
              </nav>
              <div className="text-xs text-slate-500 dark:text-slate-500">v0.1.0 demo</div>
            </aside>
            <div className="flex flex-1 flex-col">
              <header className="flex items-center justify-between border-b border-slate-200 bg-white/80 px-6 py-4 backdrop-blur transition-colors dark:border-slate-800 dark:bg-slate-900/60">
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">Secure supervision</p>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">UKNF Communication Platform</h2>
                </div>
                <ThemeToggle />
              </header>
              <main>{children}</main>
            </div>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
