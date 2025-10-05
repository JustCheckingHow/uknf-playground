'use client';

import axios from 'axios';
import { FormEvent, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, BookOpen, Download, MessageCircle, Trash, Upload } from 'lucide-react';
import Select from 'react-select';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { apiClient } from '@/lib/api';
import type { FaqEntry, LibraryDocument, LibraryQaResponse } from '@/types';
import { select2Styles, type SelectOption } from '@/components/ui/select2Styles';
import { useAuth } from '@/hooks/useAuth';

const DOCUMENT_CATEGORY_OPTIONS: SelectOption[] = [
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
    const status = error.response?.status ?? 0;
    const data = error.response?.data as { detail?: string } | undefined;
    if (data?.detail) {
      return data.detail;
    }
    if (status >= 500) {
      return 'Nie udało się obsłużyć żądania. Spróbuj ponownie później.';
    }
    return error.message;
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
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const documents = data?.documents ?? [];
  const faq = data?.faq ?? [];
  const isInternalUser = user?.is_internal ?? false;

  const uploadFormRef = useRef<HTMLFormElement | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploadForm, setUploadForm] = useState({
    title: '',
    description: '',
    category: DOCUMENT_CATEGORY_OPTIONS[0].value,
    version: '1.0',
    is_mandatory: false
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadValidationError, setUploadValidationError] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deletingDocumentId, setDeletingDocumentId] = useState<number | null>(null);

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
        title: '',
        description: '',
        category: DOCUMENT_CATEGORY_OPTIONS[0].value,
        version: '1.0',
        is_mandatory: false
      });
      setSelectedFile(null);
      setUploadValidationError(null);
      uploadFormRef.current?.reset();
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  });

  const deleteDocumentMutation = useMutation<void, unknown, number>({
    mutationFn: async (documentId) => {
      await apiClient.delete(`/library/documents/${documentId}`);
    },
    onMutate: (documentId) => {
      setDeletingDocumentId(documentId);
      setDeleteError(null);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['library-overview'] });
    },
    onError: (error) => {
      setDeleteError(resolveErrorMessage(error) ?? 'Nie udało się usunąć dokumentu.');
    },
    onSettled: () => {
      setDeletingDocumentId(null);
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
      setUploadValidationError('Wybierz plik do przesłania.');
      return;
    }
    setUploadValidationError(null);

    const formData = new FormData();
    const trimmedTitle = uploadForm.title.trim();
    const trimmedDescription = uploadForm.description.trim();
    formData.append('category', uploadForm.category);
    formData.append('version', uploadForm.version);
    formData.append('file', selectedFile);
    if (trimmedTitle) {
      formData.append('title', trimmedTitle);
    }
    if (trimmedDescription) {
      formData.append('description', trimmedDescription);
    }
    if (uploadForm.is_mandatory) {
      formData.append('is_mandatory', 'true');
    }

    uploadMutation.mutate(formData);
  };

  const handleDeleteDocument = (document: LibraryDocument) => {
    if (!isInternalUser) {
      return;
    }
    const confirmationTitle = document.title?.trim() || 'ten dokument';
    if (!window.confirm(`Czy na pewno chcesz usunąć dokument "${confirmationTitle}"?`)) {
      return;
    }
    deleteDocumentMutation.mutate(document.id);
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

      <div className="grid gap-6">
        {isInternalUser && (
          <Card className="space-y-4">
            <div className="flex items-center gap-2">
              <Upload size={18} className="text-primary" />
              <h2 className="text-base font-semibold text-slate-800">Dodaj dokument do biblioteki</h2>
            </div>
            <form ref={uploadFormRef} onSubmit={handleUploadSubmit} className="space-y-4">
              <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
                <div className="grid gap-4">
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="flex flex-col gap-1 text-sm">
                      <label htmlFor="library-document-category" className="font-medium text-slate-700">
                        Kategoria
                      </label>
                      <Select<SelectOption>
                        inputId="library-document-category"
                        className="mt-1 w-full"
                        classNamePrefix="select2"
                        options={DOCUMENT_CATEGORY_OPTIONS}
                        value={
                          DOCUMENT_CATEGORY_OPTIONS.find((option) => option.value === uploadForm.category) ?? null
                        }
                        isSearchable
                        styles={select2Styles}
                        noOptionsMessage={() => 'Brak wyników'}
                        onChange={(option) => {
                          if (option) {
                            setUploadForm((prev) => ({ ...prev, category: option.value }));
                          }
                        }}
                      />
                    </div>
                    <label className="flex flex-col gap-1 text-sm">
                      <span className="font-medium text-slate-700">Wersja</span>
                      <input
                        type="text"
                        value={uploadForm.version}
                        onChange={(event) => setUploadForm((prev) => ({ ...prev, version: event.target.value }))}
                        className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none"
                        placeholder="np. 1.0"
                      />
                    </label>
                    <label className="flex items-center gap-2 text-sm text-slate-700">
                      <input
                        type="checkbox"
                        checked={uploadForm.is_mandatory}
                        onChange={(event) => setUploadForm((prev) => ({ ...prev, is_mandatory: event.target.checked }))}
                        className="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary"
                      />
                      <span>Dokument obowiązkowy</span>
                    </label>
                  </div>
                  <label className="flex flex-col gap-1 text-sm">
                    <span className="font-medium text-slate-700">Tytuł</span>
                    <input
                      type="text"
                      value={uploadForm.title}
                      onChange={(event) => setUploadForm((prev) => ({ ...prev, title: event.target.value }))}
                      className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none"
                      placeholder="np. Instrukcja raportowania"
                    />
                    <span className="text-xs text-slate-500">Pozostaw puste, aby użyć nazwy pliku.</span>
                  </label>
                  <label className="flex flex-col gap-1 text-sm">
                    <span className="font-medium text-slate-700">Opis</span>
                    <textarea
                      rows={3}
                      value={uploadForm.description}
                      onChange={(event) => setUploadForm((prev) => ({ ...prev, description: event.target.value }))}
                      className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none"
                      placeholder="Krótki opis, czego dotyczy dokument."
                    />
                  </label>
                </div>
                <div className="grid gap-2 text-sm">
                  <span className="font-medium text-slate-700">Plik dokumentu</span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={(event) => {
                      const file = event.target.files?.[0] ?? null;
                      setSelectedFile(file);
                      setUploadValidationError(null);
                      if (file) {
                        const fallbackTitle = file.name.replace(/\.[^/.]+$/, '') || file.name;
                        setUploadForm((prev) => {
                          if (prev.title.trim()) {
                            return prev;
                          }
                          return { ...prev, title: fallbackTitle };
                        });
                      }
                    }}
                    className="sr-only"
                    accept=".pdf,.doc,.docx,.txt,.md,.rtf"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full justify-start gap-2 border-dashed"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    <Upload size={16} aria-hidden />
                    <span className="truncate text-left">
                      {selectedFile ? selectedFile.name : 'Wybierz plik z dysku'}
                    </span>
                  </Button>
                  <p className="text-xs text-slate-500">Akceptowane formaty: PDF, DOC, DOCX, TXT, MD, RTF.</p>
                </div>
              </div>
              {(uploadValidationError || uploadError) && (
                <p className="flex items-center gap-2 text-sm text-red-600">
                  <AlertCircle size={16} aria-hidden />
                  {uploadValidationError ?? uploadError}
                </p>
              )}
              <div className="flex justify-end">
                <Button type="submit" isLoading={uploadMutation.isPending} className="w-full justify-center md:w-auto">
                  Prześlij dokument
                </Button>
              </div>
            </form>
          </Card>
        )}

        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <MessageCircle size={18} className="text-primary" />
            <h2 className="text-base font-semibold text-slate-800">Asystent biblioteki</h2>
          </div>
          <p className="text-sm text-slate-600">
            Zadaj pytanie dotyczące dokumentów. Agent przeanalizuje zgromadzone materiały i przygotuje streszczoną odpowiedź wraz ze źródłami.
          </p>
          <form onSubmit={handleQuestionSubmit} className="flex flex-col gap-3 md:flex-row md:items-end">
            <label className="flex-1 space-y-1 text-sm">
              <span className="font-medium text-slate-700">Twoje pytanie</span>
              <input
                required
                type="text"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                disabled={qaMutation.isPending}
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 focus:border-primary focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-100"
                placeholder="Wpisz pytanie dotyczące dokumentów z biblioteki"
              />
            </label>
            {qaError && (
              <p className="flex items-center gap-2 text-sm text-red-600 md:basis-full">
                <AlertCircle size={16} aria-hidden />
                {qaError}
              </p>
            )}
            <Button
              type="submit"
              isLoading={qaMutation.isPending}
              className="w-full justify-center md:w-auto"
              disabled={!question.trim()}
            >
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
        {deleteError && (
          <p className="flex items-center gap-2 text-sm text-red-600">
            <AlertCircle size={16} aria-hidden />
            {deleteError}
          </p>
        )}
        <div className="grid gap-4 md:grid-cols-2">
          {documents.map((document) => {
            const documentTitle = document.title?.trim() || 'Dokument bez tytułu';
            const documentDescription = document.description?.trim();
            const isDeletingThisDocument = deleteDocumentMutation.isPending && deletingDocumentId === document.id;

            return (
              <Card key={document.id} className="space-y-3">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500">
                    <span>{new Date(document.published_at).toLocaleDateString('pl-PL')}</span>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-[11px] font-semibold text-slate-600">
                        {DOCUMENT_CATEGORY_LABELS[document.category] ?? document.category}
                      </span>
                      {document.is_mandatory && <span className="font-semibold text-red-600">WYMAGANY</span>}
                    </div>
                  </div>
                  {isInternalUser && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="gap-1 text-red-600 hover:bg-red-50 hover:text-red-700"
                      onClick={() => handleDeleteDocument(document)}
                      isLoading={isDeletingThisDocument}
                      disabled={deletingDocumentId !== null && deletingDocumentId !== document.id}
                    >
                      <Trash size={14} aria-hidden />
                      Usuń
                    </Button>
                  )}
                </div>
                <h3 className="text-base font-semibold text-slate-900">{documentTitle}</h3>
                {documentDescription ? (
                  <p className="text-sm text-slate-600">{documentDescription}</p>
                ) : (
                  <p className="text-sm text-slate-500">Brak opisu.</p>
                )}
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
            );
          })}
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
