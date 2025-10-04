import { Link, Outlet } from 'react-router-dom';

export function RootLayout() {
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3">
          <Link to="/" className="flex items-center gap-3">
            <img src="/knf_logo.png" alt="Logo UKNF" width={48} height={48} loading="lazy" />
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-primary">
                Urząd Komisji Nadzoru Finansowego
              </p>
              <p className="text-xs text-slate-600">Platforma komunikacyjna podmiotów nadzorowanych</p>
            </div>
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
