'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FileText, MessageSquare, Building2, Megaphone, Library, Shield, ClipboardCheck } from 'lucide-react';
import clsx from 'clsx';

const links = [
  { href: '/dashboard', label: 'Pulpit', icon: Building2 },
  { href: '/dashboard/reports', label: 'Sprawozdania', icon: FileText },
  { href: '/dashboard/messages', label: 'Wiadomości', icon: MessageSquare },
  { href: '/dashboard/announcements', label: 'Komunikaty', icon: Megaphone },
  { href: '/dashboard/library', label: 'Biblioteka', icon: Library },
  { href: '/dashboard/access-requests', label: 'Wnioski', icon: ClipboardCheck },
  { href: '/dashboard/settings', label: 'Administracja', icon: Shield }
];

export function DashboardSidebar() {
  const pathname = usePathname();

  return (
    <aside className="space-y-4">
      <nav className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
        <ul className="space-y-1">
          {links.map((link) => {
            const Icon = link.icon;
            const isActive = pathname === link.href;
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={clsx(
                    'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition',
                    isActive ? 'bg-primary text-white shadow-sm' : 'text-slate-600 hover:bg-primary/10 hover:text-primary'
                  )}
                >
                  <Icon size={18} aria-hidden />
                  <span>{link.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="rounded-lg border border-dashed border-primary/40 bg-primary/5 p-4 text-xs text-slate-600">
        <p className="font-semibold text-primary">Ważne</p>
        <p className="mt-1 leading-relaxed">
          Wszystkie operacje są audytowane. Pamiętaj o zachowaniu poufności danych podmiotów oraz zgodności z politykami UKNF.
        </p>
      </div>
    </aside>
  );
}
