import Link from 'next/link';
import { ShieldCheck, FileText, MessageSquare, Users } from 'lucide-react';

const featureCards = [
  {
    title: 'Sprawozdania regulacyjne',
    description: 'Kompletny proces przesyłania, walidacji i monitoringu statusów raportów.',
    icon: FileText
  },
  {
    title: 'Bezpieczne kanały komunikacji',
    description: 'Szyfrowana korespondencja z UKNF, wątki tematyczne i notatki wewnętrzne.',
    icon: MessageSquare
  },
  {
    title: 'Zarządzanie podmiotami',
    description: 'Jednolite profile podmiotów, role użytkowników i aktualizator danych.',
    icon: Users
  },
  {
    title: 'Zgodność i audyt',
    description: 'Ścieżka audytu, polityki retencji oraz konfiguracja bezpieczeństwa.',
    icon: ShieldCheck
  }
];

export default function HomePage() {
  return (
    <div className="space-y-10">
      <section className="grid gap-6 rounded-xl bg-white p-8 shadow-sm md:grid-cols-2">
        <div className="space-y-6">
          <span className="inline-flex items-center rounded-full bg-primary/10 px-4 py-1 text-xs font-semibold uppercase tracking-wider text-primary">
            Platforma UKNF
          </span>
          <h1 className="text-3xl font-bold text-slate-900 md:text-4xl">
            Centralna platforma komunikacyjna UKNF i podmiotów nadzorowanych
          </h1>
          <p className="text-lg text-slate-600">
            Wykorzystaj cyfrowy kanał do przekazywania sprawozdań, prowadzenia spraw i bieżącej korespondencji z Urzędem Komisji Nadzoru Finansowego.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/login"
              className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-2 text-sm font-semibold text-white shadow transition hover:bg-primary/90"
            >
              Zaloguj się
            </Link>
            <Link
              href="/register"
              className="inline-flex items-center justify-center rounded-md border border-primary px-6 py-2 text-sm font-semibold text-primary transition hover:bg-primary/5"
            >
              Zarejestruj konto
            </Link>
            <a
              href="#features"
              className="inline-flex items-center justify-center rounded-md border border-primary px-6 py-2 text-sm font-semibold text-primary transition hover:bg-primary/5"
            >
              Poznaj funkcjonalności
            </a>
          </div>
        </div>
        <div className="rounded-lg border border-dashed border-slate-300 bg-slate-50 p-6 text-sm text-slate-600">
          <h2 className="mb-3 text-base font-semibold text-slate-800">Status platformy</h2>
          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <span className="mt-1 h-2.5 w-2.5 rounded-full bg-green-500" aria-hidden="true" />
              <span>
                <strong className="block text-sm text-slate-800">Dostępność systemu:</strong>
                99.94% w ostatnich 30 dniach
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-1 h-2.5 w-2.5 rounded-full bg-green-500" aria-hidden="true" />
              <span>
                <strong className="block text-sm text-slate-800">Środowisko:</strong>
                Region UE (Warszawa) | Dane rezydujące w UE
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="mt-1 h-2.5 w-2.5 rounded-full bg-green-500" aria-hidden="true" />
              <span>
                <strong className="block text-sm text-slate-800">Ostatnia rewizja bezpieczeństwa:</strong>
                Styczeń 2024 (penetration test)
              </span>
            </li>
          </ul>
        </div>
      </section>

      <section id="features" className="space-y-6">
        <h2 className="text-2xl font-semibold text-slate-900">Najważniejsze moduły</h2>
        <div className="grid gap-5 md:grid-cols-2">
          {featureCards.map((card) => (
            <article key={card.title} className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <card.icon aria-hidden />
              </div>
              <h3 className="text-lg font-semibold text-slate-900">{card.title}</h3>
              <p className="mt-2 text-sm text-slate-600">{card.description}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
