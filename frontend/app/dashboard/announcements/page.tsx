'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Check, Clock } from 'lucide-react';

import { Button } from '@/src/components/ui/Button';
import { Card } from '@/src/components/ui/Card';
import { Badge } from '@/src/components/ui/Badge';
import { apiClient } from '@/src/lib/api';
import type { Announcement, MessageThread } from '@/src/types';

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

export default function AnnouncementsPage() {
  const queryClient = useQueryClient();
  const announcementsQuery = useAnnouncements();
  const threadsQuery = useThreads();

  const acknowledgeMutation = useMutation({
    mutationFn: async (announcementId: number) => {
      await apiClient.post(`/communication/announcements/${announcementId}/acknowledge/`, { acknowledged: true });
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['announcements'] })
  });

  const announcements = announcementsQuery.data ?? [];
  const globalMessages = (threadsQuery.data ?? []).filter((thread) => thread.is_global);

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold text-slate-900">Komunikaty</h1>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Komunikaty globalne</h2>
        {globalMessages.map((thread) => {
          const latestMessage = thread.messages[thread.messages.length - 1] ?? null;
          const publishedAt = latestMessage?.created_at ?? thread.created_at;
          return (
            <Card key={thread.id} className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900">{thread.subject}</h2>
                  <p className="text-xs text-slate-500">
                    Opublikowano: {new Date(publishedAt).toLocaleString('pl-PL')}
                  </p>
                </div>
                <Badge tone="info">Komunikat globalny</Badge>
              </div>
              <p className="text-sm text-slate-600">{latestMessage?.body ?? 'Brak treści komunikatu.'}</p>
              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-3 text-xs text-slate-500">
                <span className="inline-flex items-center gap-2">
                  <Clock size={14} /> Ostatnia aktualizacja: {new Date(thread.updated_at).toLocaleString('pl-PL')}
                </span>
              </div>
            </Card>
          );
        })}
        {globalMessages.length === 0 && <Card className="text-sm text-slate-500">Brak globalnych komunikatów.</Card>}
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-slate-900">Komunikaty UKNF</h2>
        {announcements.map((announcement) => (
          <Card key={announcement.id} className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">{announcement.title}</h2>
                <p className="text-xs text-slate-500">
                  Opublikowano: {new Date(announcement.published_at).toLocaleString('pl-PL')}
                </p>
              </div>
              <Badge tone={announcement.requires_acknowledgement ? 'warning' : 'info'}>
                {announcement.requires_acknowledgement ? 'Wymaga potwierdzenia' : 'Informacja'}
              </Badge>
            </div>
            <p className="text-sm text-slate-600">{announcement.content}</p>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-3 text-xs text-slate-500">
              <span className="inline-flex items-center gap-2">
                <Clock size={14} /> Poziom potwierdzeń: {(announcement.acknowledgement_rate * 100).toFixed(0)}%
              </span>
              {announcement.requires_acknowledgement && (
                <Button
                  size="sm"
                  onClick={() => acknowledgeMutation.mutate(announcement.id)}
                  isLoading={acknowledgeMutation.isPending}
                >
                  <Check size={16} className="mr-2" /> Potwierdź zapoznanie
                </Button>
              )}
            </div>
          </Card>
        ))}
        {announcements.length === 0 && <Card className="text-sm text-slate-500">Brak aktywnych komunikatów.</Card>}
      </section>
    </div>
  );
}
