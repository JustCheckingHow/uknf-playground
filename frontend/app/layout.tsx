import '@/app/globals.css';
import type { Metadata } from 'next';
import Image from 'next/image';
import Link from 'next/link';
import { Inter } from 'next/font/google';
import { ReactNode } from 'react';
import { Toaster } from 'sonner';

import { AuthProvider } from '@/src/providers/AuthProvider';
import { QueryProvider } from '@/src/providers/QueryProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'UKNF Platforma Komunikacyjna',
  description: 'Bezpieczna platforma komunikacyjna UKNF dla podmiotów nadzorowanych.'
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pl">
      <body className={`${inter.className} bg-slate-100 text-slate-900`}>
        <QueryProvider>
          <AuthProvider>
            <Toaster richColors position="top-right" />
            <div className="min-h-screen">
              <header className="border-b border-slate-200 bg-white">
                <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
                  <Link href="/" className="flex items-center gap-3">
                    <Image src="/knf_logo.png" alt="Logo UKNF" width={48} height={48} priority />
                    <div>
                      <p className="text-sm font-semibold uppercase tracking-wider text-primary">Urząd Komisji Nadzoru Finansowego</p>
                      <p className="text-xs text-slate-600">Platforma komunikacyjna podmiotów nadzorowanych</p>
                    </div>
                  </Link>
                </div>
              </header>
              <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
            </div>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
