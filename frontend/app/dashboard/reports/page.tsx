'use client';

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
import type { Report } from '@/src/types';

const schema = z.object({
  title: z.string().min(5),
  report_type: z.string().min(3),
  period_start: z.string(),
  period_end: z.string(),
  file_path: z.string().optional()
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

  const submitReportMutation = useMutation({
    mutationFn: async (reportId: number) => {
      await apiClient.post(`/communication/reports/${reportId}/submit/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      toast.success('Sprawozdanie przesłane do UKNF');
    },
    onError: () => toast.error('Nie udało się przesłać sprawozdania')
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

  const reports = reportsQuery.data ?? [];

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
          headers={["Tytuł", "Status", "Okres", "Akcje"]}
          rows={reports.map((report) => [
            report.title,
            <Badge key={`${report.id}-status`} tone={mapStatusToTone(report.status)}>
              {mapReportStatus(report.status)}
            </Badge>,
            `${new Date(report.period_start).toLocaleDateString('pl-PL')} — ${new Date(report.period_end).toLocaleDateString('pl-PL')}`,
            <div key={`${report.id}-actions`} className="flex items-center gap-2">
              <Button
                variant="outline"
                disabled={report.status !== 'draft'}
                onClick={() => submitReportMutation.mutate(report.id)}
              >
                Prześlij
              </Button>
              {user?.is_internal && <span className="text-xs text-slate-400">ID: {report.id}</span>}
            </div>
          ])}
        />
      </div>
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
