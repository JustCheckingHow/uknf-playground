'use client';

import { ChangeEvent, useMemo, useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';

import { Button } from '@/src/components/ui/Button';
import { Card } from '@/src/components/ui/Card';
import { DataTable } from '@/src/components/ui/DataTable';
import { Badge } from '@/src/components/ui/Badge';
import { apiClient } from '@/src/lib/api';
import { useAuth } from '@/src/hooks/useAuth';
import type { Report, ReportValidationIssue } from '@/src/types';

const schema = z.object({
  title: z.string().min(5),
  report_type: z.string().min(3),
  period_start: z.string(),
  period_end: z.string()
});

type FormValues = z.infer<typeof schema>;

function useReports() {
  return useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await apiClient.get<Report[]>('/communication/reports/');
      return response.data;
    }
  });
}

export default function ReportsPage() {
  const { profile, user } = useAuth();
  const queryClient = useQueryClient();
  const reportsQuery = useReports();
  const [activeReportId, setActiveReportId] = useState<number | null>(null);
  const [uploadingId, setUploadingId] = useState<number | null>(null);
  const [submittingId, setSubmittingId] = useState<number | null>(null);
  const fileInputsRef = useRef<Record<number, HTMLInputElement | null>>({});

  const submitReportMutation = useMutation({
    mutationFn: async (reportId: number) => {
      await apiClient.post(`/communication/reports/${reportId}/submit/`);
    },
    onMutate: (reportId: number) => {
      setSubmittingId(reportId);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Sprawozdanie przesłane do UKNF');
    },
    onError: () => toast.error('Nie udało się przesłać sprawozdania'),
    onSettled: () => setSubmittingId(null)
  });

  const uploadReportMutation = useMutation({
    mutationFn: async ({ reportId, file }: { reportId: number; file: File }) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post<Report>(
        `/communication/reports/${reportId}/upload/`,
        formData
      );
      return response.data;
    },
    onMutate: ({ reportId }) => {
      setUploadingId(reportId);
    },
    onSuccess: (data) => {
      const hasErrors = Boolean(data.validation?.errors?.length);
      const message = hasErrors
        ? `Walidacja zakończona z błędami (${data.validation?.errors?.length ?? 0})`
        : 'Walidacja zakończona sukcesem';
      toast.success(message);
      setActiveReportId(data.id);
      queryClient.setQueryData<Report[]>(['reports'], (current) => {
        if (!current) {
          return [data];
        }
        return current.map((item) => (item.id === data.id ? data : item));
      });
      queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    onError: () => toast.error('Nie udało się zwalidować sprawozdania'),
    onSettled: () => setUploadingId(null)
  });

  const createReportMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      const actingEntity = profile?.session.acting_entity || profile?.memberships[0]?.entity;
      if (!actingEntity) {
        throw new Error('Brak powiązanego podmiotu');
      }
      const payload = { ...values, entity_id: actingEntity.id };
      const response = await apiClient.post<Report>('/communication/reports/', payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Utworzono szkic sprawozdania');
    },
    onError: () => toast.error('Nie udało się utworzyć sprawozdania')
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors }
  } = useForm<FormValues>({
    resolver: zodResolver(schema)
  });

  const onSubmit = handleSubmit(async (values) => {
    await createReportMutation.mutateAsync(values);
    reset();
  });

  const openFileDialog = (reportId: number) => {
    const input = fileInputsRef.current[reportId];
    if (input) {
      input.click();
    }
  };

  const handleFileChange = (reportId: number, event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    uploadReportMutation.mutate({ reportId, file });
    event.target.value = '';
  };

  const reports = reportsQuery.data ?? [];
  const activeReport = useMemo(() => {
    if (!reports.length) {
      return null;
    }
    if (activeReportId) {
      const selected = reports.find((item) => item.id === activeReportId);
      if (selected) {
        return selected;
      }
    }
    return reports.find((item) => item.validation) ?? reports[0] ?? null;
  }, [activeReportId, reports]);
  const activeMetadata = useMemo(() => {
    if (!activeReport?.validation?.metadata) {
      return {} as Record<string, string | number | null | undefined>;
    }
    return activeReport.validation.metadata as Record<string, string | number | null | undefined>;
  }, [activeReport]);
  const activeFlags = useMemo(() => Object.entries(activeReport?.validation?.flags ?? {}), [activeReport]);

  return (
    <div className="space-y-6">
      <Card className="space-y-6">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Nowe sprawozdanie</h1>
          <p className="text-sm text-slate-600">
            Uzupełnij podstawowe dane. Po zapisaniu możesz dołączyć plik źródłowy i przesłać sprawozdanie do walidacji UKNF.
          </p>
        </div>
        <form className="grid gap-4 md:grid-cols-2" onSubmit={onSubmit}>
          <label className="text-sm">
            <span className="text-slate-700">Tytuł sprawozdania</span>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
              {...register('title')}
            />
            {errors.title && <span className="mt-1 block text-xs text-red-600">{errors.title.message}</span>}
          </label>

          <label className="text-sm">
            <span className="text-slate-700">Typ sprawozdania</span>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
              {...register('report_type')}
            />
            {errors.report_type && (
              <span className="mt-1 block text-xs text-red-600">{errors.report_type.message}</span>
            )}
          </label>

          <label className="text-sm">
            <span className="text-slate-700">Okres od</span>
            <input
              type="date"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
              {...register('period_start')}
            />
          </label>

          <label className="text-sm">
            <span className="text-slate-700">Okres do</span>
            <input
              type="date"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
              {...register('period_end')}
            />
          </label>

          <div className="md:col-span-2 flex items-center justify-between">
            <p className="text-xs text-slate-500">
              Podmiot przypisany: {profile?.session.acting_entity?.name || profile?.memberships[0]?.entity.name || 'brak'}
            </p>
            <Button type="submit" isLoading={createReportMutation.isPending}>
              Zapisz szkic
            </Button>
          </div>
        </form>
      </Card>

      <div className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">Sprawozdania</h2>
        <DataTable
          headers={["Tytuł", "Status", "Okres", "Walidacja", "Akcje"]}
          rows={reports.map((report) => {
            const validationTone = mapValidationTone(report.validation);
            return [
              <span key={`${report.id}-title`} className="font-medium text-slate-900">
                {report.title}
              </span>,
              <Badge key={`${report.id}-status`} tone={mapStatusToTone(report.status)}>
                {mapReportStatus(report.status)}
              </Badge>,
              formatPeriod(report.period_start, report.period_end),
              <div key={`${report.id}-validation`} className="flex flex-col gap-1">
                <Badge tone={validationTone}>{mapValidationStatus(report.validation?.status)}</Badge>
                <span className="text-xs text-slate-500">{formatValidationSummary(report.validation)}</span>
              </div>,
              <div key={`${report.id}-actions`} className="flex flex-wrap items-center gap-2">
                <input
                  type="file"
                  accept=".xlsx"
                  className="hidden"
                  ref={(element) => {
                    if (element) {
                      fileInputsRef.current[report.id] = element;
                    } else {
                      delete fileInputsRef.current[report.id];
                    }
                  }}
                  onChange={(event) => handleFileChange(report.id, event)}
                />
                <Button
                  variant="outline"
                  onClick={() => openFileDialog(report.id)}
                  isLoading={uploadingId === report.id}
                >
                  Dodaj plik
                </Button>
                <Button
                  variant="primary"
                  disabled={report.status !== 'validated'}
                  onClick={() => submitReportMutation.mutate(report.id)}
                  isLoading={submittingId === report.id}
                >
                  Przekaż
                </Button>
                <Button variant="ghost" onClick={() => setActiveReportId(report.id)}>
                  Szczegóły
                </Button>
                {user?.is_internal && <span className="text-xs text-slate-400">ID: {report.id}</span>}
              </div>
            ];
          })}
        />
      </div>

      {activeReport && (
        <Card className="space-y-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-lg font-semibold text-slate-900">Walidacja: {activeReport.title}</h3>
              <p className="text-sm text-slate-600">{mapValidationStatus(activeReport.validation?.status)}</p>
            </div>
            <div className="flex gap-2">
              <Badge tone="danger">{activeReport.validation?.errors.length ?? 0} błędy</Badge>
              <Badge tone="warning">{activeReport.validation?.warnings.length ?? 0} ostrzeżenia</Badge>
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-3">
              <div>
                <h4 className="text-sm font-semibold text-slate-800">Metadane</h4>
                <dl className="space-y-2 text-sm text-slate-600">
                  <div>
                    <dt className="font-medium text-slate-700">Podmiot</dt>
                    <dd>{(activeMetadata.entity_name as string) ?? activeReport.entity.name}</dd>
                  </div>
                  <div>
                    <dt className="font-medium text-slate-700">Okres</dt>
                    <dd>
                      {activeMetadata.period_start && activeMetadata.period_end
                        ? formatPeriod(
                            String(activeMetadata.period_start),
                            String(activeMetadata.period_end)
                          )
                        : formatPeriod(activeReport.period_start, activeReport.period_end)}
                    </dd>
                  </div>
                  {activeMetadata.taxonomy && (
                    <div>
                      <dt className="font-medium text-slate-700">Taksonomia</dt>
                      <dd>{String(activeMetadata.taxonomy)}</dd>
                    </div>
                  )}
                  {activeMetadata.form_id && (
                    <div>
                      <dt className="font-medium text-slate-700">Identyfikator formularza</dt>
                      <dd>{String(activeMetadata.form_id)}</dd>
                    </div>
                  )}
                </dl>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-slate-800">Formularze</h4>
                {activeReport.validation?.forms.length ? (
                  <div className="flex flex-wrap gap-2">
                    {activeReport.validation.forms.map((form) => (
                      <Badge key={form.id} tone="info">
                        {form.id}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">Brak informacji o formularzach.</p>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <div>
                <h4 className="text-sm font-semibold text-slate-800">Flagi</h4>
                {activeFlags.length ? (
                  <ul className="space-y-1 text-sm text-slate-600">
                    {activeFlags.map(([key, value]) => (
                      <li key={key} className="flex items-center justify-between gap-4">
                        <span>{formatFlagLabel(key)}</span>
                        <span className="font-medium text-slate-700">{formatBoolean(value)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-slate-500">Brak dodatkowych informacji o flagach.</p>
                )}
              </div>

              {activeReport.file_path && (
                <div className="flex items-center justify-between rounded-md border border-slate-200 px-3 py-2 text-sm text-slate-600">
                  <span>Plik źródłowy zapisany w systemie.</span>
                </div>
              )}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800">Błędy</h4>
              {activeReport.validation?.errors.length ? (
                <ul className="list-disc space-y-1 pl-5 text-sm text-red-600">
                  {activeReport.validation?.errors.map((issue, index) => (
                    <li key={`${issue.code}-${issue.cell ?? issue.sheet ?? index}`}>
                      {describeIssue(issue)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500">Brak błędów walidacji.</p>
              )}
            </div>

            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-slate-800">Ostrzeżenia</h4>
              {activeReport.validation?.warnings.length ? (
                <ul className="list-disc space-y-1 pl-5 text-sm text-amber-600">
                  {activeReport.validation?.warnings.map((issue, index) => (
                    <li key={`${issue.code}-${issue.cell ?? issue.sheet ?? index}`}>
                      {describeIssue(issue)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-sm text-slate-500">Brak ostrzeżeń.</p>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}

function mapReportStatus(status: string) {
  const mapping: Record<string, string> = {
    draft: 'Robocze',
    submitted: 'Przekazane',
    processing: 'W trakcie',
    validated: 'Walidacja zakończona',
    validation_errors: 'Błędy walidacji',
    technical_failure: 'Błąd techniczny',
    timeout: 'Przekroczono czas',
    disputed: 'Zakwestionowane'
  };
  return mapping[status] ?? status;
}

function mapStatusToTone(status: string): 'success' | 'warning' | 'danger' | 'info' | 'default' {
  switch (status) {
    case 'validated':
      return 'success';
    case 'validation_errors':
    case 'technical_failure':
    case 'timeout':
      return 'danger';
    case 'submitted':
    case 'processing':
      return 'info';
    case 'disputed':
      return 'warning';
    default:
      return 'default';
  }
}

function mapValidationStatus(status?: string) {
  if (!status) {
    return 'Brak walidacji';
  }
  const mapping: Record<string, string> = {
    validated: 'Walidacja zakończona sukcesem',
    validation_errors: 'Błędy walidacji'
  };
  return mapping[status] ?? status;
}

function mapValidationTone(validation?: Report['validation'] | null): 'success' | 'warning' | 'danger' | 'info' | 'default' {
  if (!validation) {
    return 'default';
  }
  if (validation.errors.length) {
    return 'danger';
  }
  if (validation.warnings.length) {
    return 'warning';
  }
  return 'success';
}

function formatValidationSummary(validation?: Report['validation'] | null) {
  if (!validation) {
    return 'Walidacja nie została uruchomiona';
  }
  return `${validation.errors.length} błędów • ${validation.warnings.length} ostrzeżeń`;
}

function formatPeriod(start: string, end: string) {
  const startText = new Date(start).toLocaleDateString('pl-PL');
  const endText = new Date(end).toLocaleDateString('pl-PL');
  return `${startText} — ${endText}`;
}

function formatFlagLabel(key: string) {
  const mapping: Record<string, string> = {
    includes_board_members: 'Dane o członkach zarządu',
    includes_supervisory_board: 'Dane o radzie nadzorczej',
    includes_procurators: 'Dane o prokurentach',
    is_correction: 'Wersja korekty'
  };
  return mapping[key] ?? key.replace(/_/g, ' ');
}

function formatBoolean(value: unknown) {
  if (value === true) return 'Tak';
  if (value === false) return 'Nie';
  if (value === null || value === undefined) return 'Brak danych';
  return String(value);
}

function describeIssue(issue: ReportValidationIssue) {
  const location = [issue.sheet, issue.cell].filter(Boolean).join(' ');
  const expectations: string[] = [];
  if (issue.expected) {
    expectations.push(`oczekiwano: ${issue.expected}`);
  }
  if (issue.actual) {
    expectations.push(`otrzymano: ${issue.actual}`);
  }
  const suffix = expectations.length ? ` (${expectations.join(', ')})` : '';
  return `${location ? `[${location}] ` : ''}${issue.message}${suffix}`;
}
