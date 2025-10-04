'use client';

import axios from 'axios';
import { FormEvent, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, BookOpen, Download, MessageCircle, Upload } from 'lucide-react';

import { Button } from '@/src/components/ui/Button';
import { Card } from '@/src/components/ui/Card';
import { apiClient } from '@/src/lib/api';
import type { FaqEntry, LibraryDocument, LibraryQaResponse } from '@/src/types';

const DOCUMENT_CATEGORY_OPTIONS = [
  { value: 'reporting', label: 'Raportowanie' },
  { value: 'supervision', label: 'Nadzór' },
  { value: 'legal', label: 'Prawo' },
  { value: 'faq', label: 'FAQ' }
];

const DOCUMENT_CATEGORY_LABELS = DOCUMENT_CATEGORY_OPTIONS.reduce<Record<string, string>>((acc, option) => {
  acc[option.value] = option.label;
  return acc;
}, {});

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

function resolveErrorMessage(error: unknown) {
  if (!error) {
    return null;
  }
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { detail?: string } | undefined;
    return data?.detail ?? error.message;
  }
  if (typeof error === 'string') {
    return error;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return null;
}

export default function LibraryPage() {
  const { data } = useLibrary();
  const queryClient = useQueryClient();
  const documents = data?.documents ?? [];
  const faq = data?.faq ?? [];

  const uploadFormRef = useRef<HTMLFormElement | null>(null);
  const [uploadForm, setUploadForm] = useState({
    description: '',
    category: DOCUMENT_CATEGORY_OPTIONS[0].value,
    version: '1.0',
    is_mandatory: false
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const [question, setQuestion] = useState('');
  const [qaResult, setQaResult] = useState<LibraryQaResponse | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async (payload: FormData) => {
      const response = await apiClient.post<LibraryDocument>('/library/documents', payload, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['library-overview'] });
      setUploadForm({
        description: '',
        category: DOCUMENT_CATEGORY_OPTIONS[0].value,
        version: '1.0',
        is_mandatory: false
      });
      setSelectedFile(null);
      uploadFormRef.current?.reset();
    }
  });

  const qaMutation = useMutation({
    mutationFn: async (payload: { question: string }) => {
      const response = await apiClient.post<LibraryQaResponse>('/library/qa', payload);
      return response.data;
    },
    onSuccess: (data) => {
      setQaResult(data);
      setQuestion('');
    }
  });

  const uploadError = resolveErrorMessage(uploadMutation.error);
  const qaError = resolveErrorMessage(qaMutation.error);

  const handleUploadSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedFile) {
      return;
    }

    const formData = new FormData();
    formData.append('description', uploadForm.description);
    formData.append('category', uploadForm.category);
    formData.append('version', uploadForm.version);
    formData.append('file', selectedFile);
    if (uploadForm.is_mandatory) {
      formData.append('is_mandatory', 'true');
    }

    uploadMutation.mutate(formData);
  };

  const handleQuestionSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!question.trim()) {
      return;
    }
    qaMutation.mutate({ question: question.trim() });
  };

  return (
    <div className="space-y-6">
      <Card className="space-y-3">
        <h1 className="text-lg font-semibold text-slate-900">Biblioteka dokumentów</h1>
        <p className="text-sm text-slate-600">
          Aktualne wytyczne, procedury i materiały wspierające proces raportowania do UKNF. Dokumenty oznaczone jako obowiązkowe muszą zostać wdrożone przez podmioty.
        </p>
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <Upload size={18} className="text-primary" />
            <h2 className="text-base font-semibold text-slate-800">Dodaj dokument do biblioteki</h2>
          </div>
          <form ref={uploadFormRef} onSubmit={handleUploadSubmit} className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-1 text-sm">
                <span className="font-medium text-slate-700">Kategoria</span>
                <select
                  required
                  value={uploadForm.category}
                  onChange={(event) => setUploadForm((prev) => ({ ...prev, category: event.target.value }))}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none"
                >
                  {DOCUMENT_CATEGORY_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="space-y-1 text-sm">
                <span className="font-medium text-slate-700">Wersja</span>
                <input
                  type="text"
                  value={uploadForm.version}
                  onChange={(event) => setUploadForm((prev) => ({ ...prev, version: event.target.value }))}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none"
                  placeholder="np. 1.0"
                />
              </label>
              <label className="flex items-center gap-2 pt-6 text-sm text-slate-700">
                <input
                  type="checkbox"
                  checked={uploadForm.is_mandatory}
                  onChange={(event) => setUploadForm((prev) => ({ ...prev, is_mandatory: event.target.checked }))}
                  className="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary"
                />
                <span>Dokument obowiązkowy</span>
              </label>
            </div>
            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Opis (opcjonalnie)</span>
              <textarea
                value={uploadForm.description}
                onChange={(event) => setUploadForm((prev) => ({ ...prev, description: event.target.value }))}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none"
                rows={3}
                placeholder="Krótki opis zawartości dokumentu"
              />
            </label>
            <div className="space-y-2 text-sm">
              <label className="font-medium text-slate-700">
                Plik dokumentu
                <input
                  type="file"
                  required
                  onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                  className="mt-2 block w-full text-xs text-slate-600 file:mr-3 file:rounded-md file:border file:border-slate-300 file:bg-white file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 file:hover:bg-slate-50"
                  accept=".pdf,.doc,.docx,.txt,.md,.rtf"
                />
              </label>
              {selectedFile && (
                <p className="text-xs text-slate-500">Wybrano: {selectedFile.name} (nazwa w bibliotece)</p>
              )}
            </div>
            {uploadError && (
              <p className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle size={16} aria-hidden />
                {uploadError}
              </p>
            )}
            <Button type="submit" isLoading={uploadMutation.isPending} className="w-full justify-center">
              Prześlij dokument
            </Button>
          </form>
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <MessageCircle size={18} className="text-primary" />
            <h2 className="text-base font-semibold text-slate-800">Asystent biblioteki</h2>
          </div>
          <p className="text-sm text-slate-600">
            Zadaj pytanie dotyczące dokumentów. Agent przeanalizuje zgromadzone materiały i przygotuje streszczoną odpowiedź wraz ze źródłami.
          </p>
          <form onSubmit={handleQuestionSubmit} className="space-y-3">
            <label className="space-y-1 text-sm">
              <span className="font-medium text-slate-700">Twoje pytanie</span>
              <textarea
                required
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none"
                rows={4}
                placeholder="Wpisz pytanie dotyczące dokumentów z biblioteki"
              />
            </label>
            {qaError && (
              <p className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle size={16} aria-hidden />
                {qaError}
              </p>
            )}
            <Button type="submit" isLoading={qaMutation.isPending} className="w-full justify-center">
              Uzyskaj odpowiedź
            </Button>
          </form>
          {qaResult && (
            <div className="space-y-3 rounded-md border border-slate-200 bg-slate-50 p-4">
              <h3 className="text-sm font-semibold text-slate-800">Odpowiedź</h3>
              <p className="whitespace-pre-line text-sm text-slate-700">{qaResult.answer}</p>
              {qaResult.sources.length > 0 && (
                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Źródła</p>
                  <ul className="space-y-2 text-sm">
                    {qaResult.sources.map((source) => (
                      <li key={source.id} className="flex items-center justify-between gap-2 rounded border border-slate-200 bg-white px-3 py-2">
                        <div>
                          <p className="font-medium text-slate-800">{source.title}</p>
                          <p className="text-xs text-slate-500">
                            {DOCUMENT_CATEGORY_LABELS[source.category] ?? source.category} • wersja {source.version}
                          </p>
                        </div>
                        {source.document_url && (
                          <a
                            href={source.document_url}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
                          >
                            <Download size={14} aria-hidden />
                            Zobacz
                          </a>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      <section className="space-y-3">
        <h2 className="text-base font-semibold text-slate-800">Dokumenty</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {documents.map((document) => (
            <Card key={document.id} className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-500">
                <span>{new Date(document.published_at).toLocaleDateString('pl-PL')}</span>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">
                    {DOCUMENT_CATEGORY_LABELS[document.category] ?? document.category}
                  </span>
                  {document.is_mandatory && <span className="font-semibold text-red-600">WYMAGANY</span>}
                </div>
              </div>
              <h3 className="text-base font-semibold text-slate-900">{document.title}</h3>
              <p className="text-sm text-slate-600">{document.description}</p>
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>Wersja: {document.version}</span>
                {document.document_url ? (
                  <a
                    href={document.document_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-2 rounded-md border border-slate-300 px-3 py-2 text-xs font-semibold text-primary hover:bg-primary/10"
                  >
                    <Download size={16} aria-hidden /> Pobierz
                  </a>
                ) : (
                  <span className="text-xs text-slate-400">Brak pliku do pobrania</span>
                )}
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
