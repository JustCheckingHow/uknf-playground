'use client';

import { useQuery } from '@tanstack/react-query';
import { BarChart3, FileText, MessageSquare, Megaphone } from 'lucide-react';

import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { DataTable } from '@/components/ui/DataTable';
import { apiClient } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import type { Announcement, MessageThread, Report } from '@/types';

function useReports() {
  return useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const response = await apiClient.get<Report[]>('/communication/reports/');
      return response.data;
    }
  });
}

function useAnnouncements() {
  return useQuery({
    queryKey: ['announcements'],
    queryFn: async () => {
      const response = await apiClient.get<Announcement[]>('/communication/announcements/');
      return response.data;
    }
  });
}

function useThreads() {
  return useQuery({
    queryKey: ['threads'],
    queryFn: async () => {
      const response = await apiClient.get<MessageThread[]>('/communication/messages/');
      return response.data;
    }
  });
}

export default function DashboardPage() {
  const { profile } = useAuth();
  const reportsQuery = useReports();
  const announcementsQuery = useAnnouncements();
  const threadsQuery = useThreads();

  const recentReports = reportsQuery.data?.slice(0, 5) || [];
  const openThreads = threadsQuery.data?.filter((thread) => !thread.is_internal_only).slice(0, 5) || [];
  const latestAnnouncements = announcementsQuery.data?.slice(0, 3) || [];

  return (
    <div className="space-y-6">
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card className="space-y-3">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>Sprawozdania</span>
            <FileText size={18} className="text-primary" aria-hidden />
          </div>
          <p className="text-3xl font-semibold text-slate-900">{reportsQuery.data?.length ?? 0}</p>
          <p className="text-xs text-slate-500">Łączna liczba raportów powiązanych z Twoimi podmiotami.</p>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>Otwarte wątki</span>
            <MessageSquare size={18} className="text-primary" aria-hidden />
          </div>
          <p className="text-3xl font-semibold text-slate-900">{openThreads.length}</p>
          <p className="text-xs text-slate-500">Aktywne kanały komunikacji wymagające odpowiedzi.</p>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>Komunikaty</span>
            <Megaphone size={18} className="text-primary" aria-hidden />
          </div>
          <p className="text-3xl font-semibold text-slate-900">{announcementsQuery.data?.length ?? 0}</p>
          <p className="text-xs text-slate-500">Opublikowane komunikaty UKNF.</p>
        </Card>

        <Card className="space-y-3">
          <div className="flex items-center justify-between text-sm text-slate-500">
            <span>Powiadomienia</span>
            <BarChart3 size={18} className="text-primary" aria-hidden />
          </div>
          <p className="text-3xl font-semibold text-slate-900">{profile?.memberships.length ?? 0}</p>
          <p className="text-xs text-slate-500">Powiązane podmioty: {profile?.memberships.map((m) => m.entity.name).join(', ') || 'brak'}</p>
        </Card>
      </section>

      <section className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Najnowsze sprawozdania</h2>
          </div>
          <DataTable
            headers={["Tytuł", "Podmiot", "Status", "Złożono"]}
            rows={recentReports.map((report) => [
              report.title,
              report.entity.name,
              <Badge key={report.id} tone={mapStatusToTone(report.status)}>{mapReportStatus(report.status)}</Badge>,
              new Date(report.submitted_at || report.created_at).toLocaleString('pl-PL')
            ])}
          />
        </div>

        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-slate-900">Komunikaty UKNF</h2>
          <div className="space-y-3">
            {latestAnnouncements.map((item) => (
              <Card key={item.id} className="space-y-2 p-4">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>{new Date(item.published_at).toLocaleDateString('pl-PL')}</span>
                  <Badge tone={item.requires_acknowledgement ? 'warning' : 'info'}>
                    {item.requires_acknowledgement ? 'Wymaga potwierdzenia' : 'Informacja'}
                  </Badge>
                </div>
                <p className="text-sm font-semibold text-slate-800">{item.title}</p>
                <p className="text-xs text-slate-600">{item.summary}</p>
              </Card>
            ))}
            {latestAnnouncements.length === 0 && (
              <Card className="text-sm text-slate-600">Brak nowych komunikatów.</Card>
            )}
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">Otwarte kanały komunikacji</h2>
        <DataTable
          headers={["Temat", "Podmiot", "Ostatnia aktualizacja"]}
          rows={openThreads.map((thread) => [
            thread.subject,
            thread.entity?.name ?? 'Komunikat globalny',
            new Date(thread.updated_at).toLocaleString('pl-PL')
          ])}
        />
      </section>
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
