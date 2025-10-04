'use client';

import { useQuery } from '@tanstack/react-query';
import { BookOpen, Download } from 'lucide-react';

import { Card } from '@/src/components/ui/Card';
import { apiClient } from '@/src/lib/api';
import type { FaqEntry, LibraryDocument } from '@/src/types';

interface LibraryOverviewResponse {
  documents: LibraryDocument[];
  faq: FaqEntry[];
}

function useLibrary() {
  return useQuery({
    queryKey: ['library-overview'],
    queryFn: async () => {
      const response = await apiClient.get<LibraryOverviewResponse>('/library/overview');
      return response.data;
    }
  });
}

export default function LibraryPage() {
  const { data } = useLibrary();
  const documents = data?.documents ?? [];
  const faq = data?.faq ?? [];

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <h1 className="text-lg font-semibold text-slate-900">Biblioteka dokumentów</h1>
        <p className="text-sm text-slate-600">
          Aktualne wytyczne, procedury i materiały wspierające proces raportowania do UKNF. Dokumenty oznaczone jako obowiązkowe muszą zostać wdrożone przez podmioty.
        </p>
      </Card>

      <section className="space-y-3">
        <h2 className="text-base font-semibold text-slate-800">Dokumenty</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {documents.map((document) => (
            <Card key={document.id} className="space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{new Date(document.published_at).toLocaleDateString('pl-PL')}</span>
                {document.is_mandatory && <span className="font-semibold text-red-600">WYMAGANY</span>}
              </div>
              <h3 className="text-base font-semibold text-slate-900">{document.title}</h3>
              <p className="text-sm text-slate-600">{document.description}</p>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Wersja: {document.version}</span>
                <a
                  href={document.document_url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold text-primary hover:bg-primary/10"
                >
                  <Download size={16} /> Pobierz
                </a>
              </div>
            </Card>
          ))}
          {documents.length === 0 && <Card className="text-sm text-slate-500">Brak dokumentów w bibliotece.</Card>}
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <BookOpen size={18} className="text-primary" />
          <h2 className="text-base font-semibold text-slate-800">FAQ</h2>
        </div>
        <div className="space-y-2">
          {faq.map((entry) => (
            <details key={entry.id} className="rounded-lg border border-slate-200 bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-slate-800">
                {entry.question}
              </summary>
              <p className="mt-2 text-sm text-slate-600">{entry.answer}</p>
            </details>
          ))}
          {faq.length === 0 && <Card className="text-sm text-slate-500">Brak wpisów FAQ.</Card>}
        </div>
      </section>
    </div>
  );
}
