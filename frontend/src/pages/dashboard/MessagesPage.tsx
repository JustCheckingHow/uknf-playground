'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import type { Message, MessageThread } from '@/types';

interface MessageForm {
  body: string;
}

interface BroadcastForm {
  subject: string;
  body: string;
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

function useThreadMessages(threadId?: number) {
  return useQuery({
    queryKey: ['thread', threadId],
    enabled: Boolean(threadId),
    queryFn: async () => {
      const response = await apiClient.get<Message[]>(`/communication/messages/${threadId}/messages/`);
      return response.data;
    }
  });
}

export default function MessagesPage() {
  const [selectedThreadId, setSelectedThreadId] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const { profile } = useAuth();
  const isInternalUser = profile?.user.is_internal ?? false;
  const threadsQuery = useThreads();
  const messagesQuery = useThreadMessages(selectedThreadId ?? undefined);
  const {
    register: registerMessage,
    handleSubmit: handleMessageSubmit,
    reset: resetMessageForm
  } = useForm<MessageForm>();
  const {
    register: registerBroadcast,
    handleSubmit: handleBroadcastSubmit,
    reset: resetBroadcastForm
  } = useForm<BroadcastForm>();

  const sendMessageMutation = useMutation({
    mutationFn: async (payload: MessageForm) => {
      if (!selectedThreadId) throw new Error('Brak wybranego wątku');
      await apiClient.post(`/communication/messages/${selectedThreadId}/messages/`, payload);
    },
    onSuccess: () => {
      if (selectedThreadId) {
        queryClient.invalidateQueries({ queryKey: ['thread', selectedThreadId] });
      }
      resetMessageForm();
    }
  });

  const broadcastMutation = useMutation({
    mutationFn: async (payload: BroadcastForm) => {
      const response = await apiClient.post<MessageThread>('/communication/messages/broadcast/', payload);
      return response.data;
    },
    onSuccess: (thread) => {
      setSelectedThreadId(thread.id);
      queryClient.setQueryData<MessageThread[]>(['threads'], (current) => {
        if (!current) {
          return [thread];
        }
        const withoutDuplicate = current.filter((item) => item.id !== thread.id);
        return [thread, ...withoutDuplicate];
      });
      queryClient.setQueryData<Message[]>(['thread', thread.id], thread.messages);
      resetBroadcastForm();
    }
  });

  const threads = threadsQuery.data ?? [];
  const messages = messagesQuery.data ?? [];
  const selectedThread = threads.find((thread) => thread.id === selectedThreadId) ?? null;

  return (
    <div className="space-y-4">
      {isInternalUser && (
        <Card className="space-y-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-slate-900">Wyślij komunikat globalny</h2>
            <p className="text-xs text-slate-500">
              Komunikat pojawi się w skrzynce wiadomości wszystkich użytkowników i zostanie zapisany w archiwum.
            </p>
          </div>
          <form
            className="space-y-3"
            onSubmit={handleBroadcastSubmit((values) => broadcastMutation.mutate(values))}
          >
            <label className="block text-sm text-slate-700">
              Temat komunikatu
              <input
                type="text"
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                placeholder="Np. Pilny komunikat UKNF"
                {...registerBroadcast('subject', { required: true })}
              />
            </label>
            <label className="block text-sm text-slate-700">
              Treść komunikatu
              <textarea
                rows={4}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                placeholder="Wpisz treść komunikatu, który ma trafić do wszystkich użytkowników"
                {...registerBroadcast('body', { required: true })}
              />
            </label>
            <Button type="submit" isLoading={broadcastMutation.isPending}>
              Wyślij komunikat globalny
            </Button>
          </form>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
        <Card className="space-y-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Kanały komunikacji</h2>
            <p className="text-xs text-slate-500">Zachowaj poufność informacji. Wątki są archiwizowane.</p>
          </div>
          <div className="space-y-2">
            {threads.map((thread) => {
              const scopeLabel = thread.is_global
                ? 'Komunikat globalny'
                : thread.entity?.name ?? 'Brak powiązanego podmiotu';
              return (
                <button
                  key={thread.id}
                  onClick={() => setSelectedThreadId(thread.id)}
                  className={`w-full rounded-md border px-3 py-2 text-left text-sm transition ${
                    selectedThreadId === thread.id
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-slate-200 bg-slate-50 text-slate-700 hover:border-primary/50'
                  }`}
                >
                  <p className="font-medium">{thread.subject}</p>
                  <p className="text-xs text-slate-500">{scopeLabel}</p>
                </button>
              );
            })}
            {threads.length === 0 && <p className="text-sm text-slate-500">Brak wątków komunikacji.</p>}
          </div>
        </Card>

        <Card className="flex min-h-[420px] flex-col">
          {selectedThread ? (
            <>
              <div className="flex items-center justify-between border-b border-slate-200 pb-3">
                <div>
                  <h3 className="text-lg font-semibold text-slate-900">{selectedThread.subject}</h3>
                  {selectedThread.is_global ? (
                    <p className="text-xs text-slate-500">Komunikat globalny</p>
                  ) : (
                    <p className="text-xs text-slate-500">
                      Podmiot: {selectedThread.entity?.name ?? 'Brak danych'}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  {selectedThread.is_global && <Badge tone="info">Globalny</Badge>}
                  {selectedThread.is_internal_only ? (
                    <Badge tone="info">Wewnętrzny</Badge>
                  ) : (
                    <Badge tone="success">Zewnętrzny</Badge>
                  )}
                </div>
              </div>

              <div className="mt-4 flex-1 space-y-4 overflow-y-auto pr-2">
                {messages.map((message) => (
                  <div key={message.id} className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>{message.sender?.email ?? 'System'}</span>
                      <span>{new Date(message.created_at).toLocaleString('pl-PL')}</span>
                    </div>
                    <p className="mt-2 text-slate-700">{message.body}</p>
                    {message.is_internal_note && <Badge tone="warning">Notatka wewnętrzna</Badge>}
                  </div>
                ))}
                {messages.length === 0 && (
                  <p className="text-sm text-slate-500">Brak wiadomości w tym wątku.</p>
                )}
              </div>

              <form
                className="mt-4 space-y-3 border-t border-slate-200 pt-4"
                onSubmit={handleMessageSubmit((values) => sendMessageMutation.mutate(values))}
              >
                <label className="block text-sm text-slate-700">
                  Treść wiadomości
                  <textarea
                    rows={3}
                    className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                    placeholder="Napisz odpowiedź..."
                    {...registerMessage('body', { required: true })}
                  />
                </label>
                <Button type="submit" isLoading={sendMessageMutation.isPending}>
                  Wyślij wiadomość
                </Button>
              </form>
            </>
          ) : (
            <div className="flex flex-1 items-center justify-center text-sm text-slate-500">
              Wybierz wątek, aby wyświetlić historię komunikacji.
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

