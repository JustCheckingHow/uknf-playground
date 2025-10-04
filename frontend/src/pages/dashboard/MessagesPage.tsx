'use client';

import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Controller, useForm } from 'react-hook-form';
import Select from 'react-select';
import { isAxiosError } from 'axios';
import { toast } from 'sonner';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import type { Message, MessageThread, User, UserGroup } from '@/types';
import { select2Styles, type SelectOption } from '@/components/ui/select2Styles';

function getErrorMessage(error: unknown, fallback: string): string {
  if (isAxiosError(error)) {
    const data = error.response?.data;
    if (typeof data === 'string') {
      return data;
    }
    if (data && typeof data === 'object') {
      const detail = (data as { detail?: unknown }).detail;
      if (typeof detail === 'string') {
        return detail;
      }
      const firstEntry = Object.values(data as Record<string, unknown>)[0];
      if (Array.isArray(firstEntry) && firstEntry.length > 0 && typeof firstEntry[0] === 'string') {
        return firstEntry[0];
      }
    }
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

interface ThreadFilters {
  groupId?: number;
  updatedAfter?: string;
  updatedBefore?: string;
  targetType?: TargetType;
}

interface MessageForm {
  body: string;
  attachment?: FileList;
}

type TargetType = 'group' | 'user';

interface BroadcastForm {
  subject: string;
  body: string;
  groupId?: string;
  userId?: string;
  targetType: TargetType;
  attachment?: FileList;
}


function useThreads(filters: ThreadFilters) {
  return useQuery({
    queryKey: ['threads', filters],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (filters.groupId) {
        params.group = String(filters.groupId);
      }
      if (filters.targetType) {
        params.target_type = filters.targetType;
      }
      if (filters.updatedAfter) {
        params.updated_after = filters.updatedAfter;
      }
      if (filters.updatedBefore) {
        params.updated_before = filters.updatedBefore;
      }
      const response = await apiClient.get<MessageThread[]>('/communication/messages/', {
        params
      });
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

function useUserGroups(enabled: boolean) {
  return useQuery({
    queryKey: ['user-groups', 'messaging'],
    enabled,
    queryFn: async () => {
      const response = await apiClient.get<UserGroup[]>('/auth/user-groups/');
      return response.data;
    }
  });
}

function useUsers(enabled: boolean) {
  return useQuery({
    queryKey: ['users', 'messaging'],
    enabled,
    queryFn: async () => {
      const response = await apiClient.get<User[]>('/auth/users/', {
        params: { non_admin: true }
      });
      return response.data;
    }
  });
}

export default function MessagesPage() {
  const [selectedThreadId, setSelectedThreadId] = useState<number | null>(null);
  const [groupFilter, setGroupFilter] = useState<string>('all');
  const [recipientFilter, setRecipientFilter] = useState<TargetType | 'all'>('all');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');
  const queryClient = useQueryClient();
  const { profile } = useAuth();
  const isInternalUser = profile?.user.is_internal ?? false;

  const filters = useMemo<ThreadFilters>(() => {
    const next: ThreadFilters = {};
    if (groupFilter !== 'all') {
      next.groupId = Number(groupFilter);
    }
    if (recipientFilter !== 'all') {
      next.targetType = recipientFilter;
    }
    if (dateFrom) {
      next.updatedAfter = dateFrom;
    }
    if (dateTo) {
      next.updatedBefore = dateTo;
    }
    return next;
  }, [groupFilter, recipientFilter, dateFrom, dateTo]);

  const threadsQuery = useThreads(filters);
  const messagesQuery = useThreadMessages(selectedThreadId ?? undefined);
  const groupsQuery = useUserGroups(isInternalUser);
  const usersQuery = useUsers(isInternalUser);

  const {
    register: registerMessage,
    handleSubmit: handleMessageSubmit,
    reset: resetMessageForm
  } = useForm<MessageForm>({
    defaultValues: { body: '', attachment: undefined }
  });

  const {
    register: registerBroadcast,
    handleSubmit: handleBroadcastSubmit,
    reset: resetBroadcastForm,
    watch: watchBroadcast,
    control: broadcastControl,
    formState: { errors: broadcastErrors }
  } = useForm<BroadcastForm>({
    defaultValues: { subject: '', body: '', targetType: 'group', groupId: '', userId: '', attachment: undefined }
  });

  const targetType = watchBroadcast('targetType') ?? 'group';

  const sendMessageMutation = useMutation({
    mutationFn: async (payload: FormData) => {
      if (!selectedThreadId) throw new Error('Brak wybranego wątku');
      await apiClient.post(`/communication/messages/${selectedThreadId}/messages/`, payload);
    },
    onSuccess: () => {
      if (selectedThreadId) {
        queryClient.invalidateQueries({ queryKey: ['thread', selectedThreadId] });
      }
      resetMessageForm({ body: '', attachment: undefined as unknown as FileList });
      toast.success('Wiadomość została wysłana.');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nie udało się wysłać wiadomości. Spróbuj ponownie.'));
    }
  });

  const broadcastMutation = useMutation({
    mutationFn: async (payload: FormData) => {
      const response = await apiClient.post<MessageThread>('/communication/messages/broadcast/', payload);
      return response.data;
    },
    onSuccess: (thread) => {
      setSelectedThreadId(thread.id);
      queryClient.invalidateQueries({ queryKey: ['threads'] });
      queryClient.setQueryData<Message[]>(['thread', thread.id], thread.messages);
      resetBroadcastForm({
        subject: '',
        body: '',
        targetType: 'group',
        groupId: '',
        userId: '',
        attachment: undefined as unknown as FileList
      });
      toast.success('Komunikat został wysłany.');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, 'Nie udało się wysłać komunikatu. Sprawdź dane i spróbuj ponownie.'));
    }
  });

  const threads = threadsQuery.data ?? [];
  const messages = messagesQuery.data ?? [];
  const userGroups = groupsQuery.data ?? [];
  const users = usersQuery.data ?? [];
  const availableGroups = useMemo(() => {
    if (isInternalUser) {
      return userGroups;
    }
    const map = new Map<number, { id: number; name: string }>();
    threads.forEach((thread) => {
      if (thread.target_group) {
        map.set(thread.target_group.id, thread.target_group);
      }
    });
    return Array.from(map.values());
  }, [isInternalUser, threads, userGroups]);
  const groupFilterOptions = useMemo<SelectOption[]>(() => {
    return [
      { value: 'all', label: 'Wszystkie grupy' },
      ...availableGroups.map((group) => ({ value: String(group.id), label: group.name }))
    ];
  }, [availableGroups]);
  const recipientFilterOptions = useMemo<SelectOption[]>(
    () => [
      { value: 'all', label: 'Wszyscy' },
      { value: 'group', label: 'Grupy' },
      { value: 'user', label: 'Pojedynczy użytkownicy' }
    ],
    []
  );
  const userOptions = useMemo<SelectOption[]>(() => {
    return users.map((user) => {
      const nameParts = [user.first_name, user.last_name].filter(Boolean).join(' ').trim();
      const label = nameParts ? `${nameParts} - ${user.email}` : user.email;
      return {
        value: String(user.id),
        label
      };
    });
  }, [users]);
  const groupOptions = useMemo<SelectOption[]>(() => {
    return availableGroups.map((group) => ({
      value: String(group.id),
      label: group.name
    }));
  }, [availableGroups]);
  const selectedThread = threads.find((thread) => thread.id === selectedThreadId) ?? null;

  useEffect(() => {
    if (selectedThreadId && !threads.some((thread) => thread.id === selectedThreadId)) {
      setSelectedThreadId(null);
    }
  }, [selectedThreadId, threads]);

  return (
    <div className="space-y-4">
      {isInternalUser && (
        <Card className="space-y-3">
          <div className="space-y-1">
            <h2 className="text-lg font-semibold text-slate-900">Wyślij wiadomość</h2>
            <p className="text-xs text-slate-500">
              Wybierz grupę odbiorców lub konkretnego użytkownika. Odpowiedzi wracają tylko do administracji.
            </p>
          </div>
          <form
            className="grid gap-3 md:grid-cols-2"
            onSubmit={handleBroadcastSubmit((values) => {
              const formData = new FormData();
              formData.append('subject', values.subject);
              formData.append('body', values.body);
              formData.append('target_type', values.targetType);
              if (values.targetType === 'group' && values.groupId) {
                formData.append('group', values.groupId);
              }
              if (values.targetType === 'user' && values.userId) {
                formData.append('user', values.userId);
              }
              const attachment = values.attachment?.item(0);
              if (attachment) {
                formData.append('attachment', attachment);
              }
              broadcastMutation.mutate(formData);
            })}
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
            <fieldset className="space-y-2 rounded-md border border-slate-200 p-3 text-sm text-slate-700">
              <legend className="px-1 text-xs font-semibold uppercase text-slate-500">Adresaci</legend>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  value="group"
                  {...registerBroadcast('targetType')}
                />
                Grupa użytkowników
              </label>
              <label className="flex items-center gap-2">
                <input type="radio" value="user" {...registerBroadcast('targetType')} />
                Pojedynczy użytkownik
              </label>
            </fieldset>
            {targetType === 'group' && (
              <label className="block text-sm text-slate-700">
                Grupa docelowa
                <div className="mt-1">
                  <Controller
                    control={broadcastControl}
                    name="groupId"
                    rules={{
                      validate: (value) => (targetType !== 'group' || value) || 'Wybierz grupę'
                    }}
                    render={({ field }) => {
                      const selectedOption =
                        groupOptions.find((option) => option.value === field.value) ?? null;
                      return (
                        <Select<SelectOption>
                          inputId="broadcast-group"
                          instanceId="broadcast-group"
                          className="w-full"
                          classNamePrefix="select2"
                          options={groupOptions}
                          placeholder="Wybierz grupę"
                          isClearable
                          isSearchable
                          isLoading={groupsQuery.isLoading}
                          styles={select2Styles}
                          noOptionsMessage={() => 'Brak wyników'}
                          value={selectedOption}
                          onBlur={field.onBlur}
                          onChange={(option) => field.onChange(option ? option.value : '')}
                        />
                      );
                    }}
                  />
                </div>
                {broadcastErrors.groupId && (
                  <p className="mt-1 text-xs text-red-600">{broadcastErrors.groupId.message}</p>
                )}
              </label>
            )}
            {targetType === 'user' && (
              <label className="block text-sm text-slate-700">
                Adresat wiadomości
                <div className="mt-1">
                  <Controller
                    control={broadcastControl}
                    name="userId"
                    rules={{
                      validate: (value) => (targetType !== 'user' || value) || 'Wybierz użytkownika'
                    }}
                    render={({ field }) => {
                      const selectedOption =
                        userOptions.find((option) => option.value === field.value) ?? null;
                      return (
                        <Select<SelectOption>
                          inputId="broadcast-user"
                          instanceId="broadcast-user"
                          className="w-full"
                          classNamePrefix="select2"
                          options={userOptions}
                          placeholder="Wybierz użytkownika"
                          isClearable
                          isSearchable
                          isLoading={usersQuery.isLoading}
                          styles={select2Styles}
                          noOptionsMessage={() => 'Brak wyników'}
                          value={selectedOption}
                          onBlur={field.onBlur}
                          onChange={(option) => field.onChange(option ? option.value : '')}
                        />
                      );
                    }}
                  />
                </div>
                {broadcastErrors.userId && (
                  <p className="mt-1 text-xs text-red-600">{broadcastErrors.userId.message}</p>
                )}
              </label>
            )}
            <label className="md:col-span-2 block text-sm text-slate-700">
              Treść komunikatu
              <textarea
                rows={4}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                placeholder="Wpisz treść komunikatu, który ma trafić do wybranej grupy"
                {...registerBroadcast('body', { required: true })}
              />
            </label>
            <div className="space-y-2">
              <label className="block text-sm text-slate-700">
                Załącznik (opcjonalnie)
                <input
                  type="file"
                  className="mt-1 w-full text-sm"
                  {...registerBroadcast('attachment')}
                />
              </label>
              <p className="text-xs text-slate-500">
                Obsługiwane są pojedyncze pliki, które zostaną dołączone do wiadomości.
              </p>
            </div>
            <div className="md:col-span-2 flex items-center gap-3">
              <Button type="submit" isLoading={broadcastMutation.isPending}>
                Wyślij wiadomość
              </Button>
              {targetType === 'group' && <Badge tone="info">Do grupy</Badge>}
              {targetType === 'user' && <Badge tone="success">Do użytkownika</Badge>}
            </div>
          </form>
        </Card>
      )}

      <Card className="space-y-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Filtruj wiadomości</h2>
            <p className="text-xs text-slate-500">Zawęź listę wątków według adresatów i daty aktualizacji.</p>
          </div>
          <div className="grid gap-3 md:grid-cols-4">
            <div className="text-xs font-medium text-slate-600">
              <label htmlFor="thread-group-filter" className="block">
                Grupa
              </label>
              <Select<SelectOption>
                inputId="thread-group-filter"
                instanceId="thread-group-filter"
                className="mt-1 w-full"
                classNamePrefix="select2"
                options={groupFilterOptions}
                value={groupFilterOptions.find((option) => option.value === groupFilter) ?? null}
                isClearable
                isSearchable
                styles={select2Styles}
                noOptionsMessage={() => 'Brak wyników'}
                onChange={(option) => setGroupFilter(option?.value ?? 'all')}
              />
            </div>
            <div className="text-xs font-medium text-slate-600">
              <label htmlFor="thread-recipient-filter" className="block">
                Typ odbiorcy
              </label>
              <Select<SelectOption>
                inputId="thread-recipient-filter"
                instanceId="thread-recipient-filter"
                className="mt-1 w-full"
                classNamePrefix="select2"
                options={recipientFilterOptions}
                value={
                  recipientFilterOptions.find((option) => option.value === recipientFilter) ?? null
                }
                isClearable
                isSearchable
                styles={select2Styles}
                noOptionsMessage={() => 'Brak wyników'}
                onChange={(option) =>
                  setRecipientFilter((option?.value as TargetType | 'all') ?? 'all')
                }
              />
            </div>
            <label className="block text-xs font-medium text-slate-600">
              Od daty
              <input
                type="date"
                value={dateFrom}
                onChange={(event) => setDateFrom(event.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
              />
            </label>
            <label className="block text-xs font-medium text-slate-600">
              Do daty
              <input
                type="date"
                value={dateTo}
                onChange={(event) => setDateTo(event.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
              />
            </label>
          </div>
        </div>

        <div className="overflow-hidden rounded-lg border border-slate-200">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th className="px-4 py-3">Temat</th>
                <th className="px-4 py-3">Adresaci</th>
                <th className="px-4 py-3">Ostatnia aktualizacja</th>
                <th className="px-4 py-3">Wiadomości</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {threads.map((thread) => {
                const scopeLabel = thread.target_group
                  ? `Grupa: ${thread.target_group.name}`
                  : thread.target_user
                  ? `Użytkownik: ${thread.target_user.email}`
                  : 'Brak danych';
                const isSelected = selectedThreadId === thread.id;
                return (
                  <tr
                    key={thread.id}
                    onClick={() => setSelectedThreadId(thread.id)}
                    className={`cursor-pointer transition ${
                      isSelected ? 'bg-primary/10 text-primary' : 'hover:bg-primary/5'
                    }`}
                  >
                    <td className="px-4 py-3 text-sm font-medium">{thread.subject}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">{scopeLabel}</td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {new Date(thread.updated_at).toLocaleString('pl-PL')}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{thread.messages.length}</td>
                  </tr>
                );
              })}
              {threads.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-sm text-slate-500">
                    Brak wątków do wyświetlenia przy wybranych filtrach.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="space-y-4">
        {selectedThread ? (
          <>
            <div className="flex flex-col gap-2 border-b border-slate-200 pb-3 md:flex-row md:items-center md:justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-900">{selectedThread.subject}</h3>
                <p className="text-xs text-slate-500">
                  {selectedThread.target_group
                    ? `Grupa: ${selectedThread.target_group.name}`
                    : selectedThread.target_user
                    ? `Adresat: ${selectedThread.target_user.email}`
                    : 'Brak danych'}
                </p>
              </div>
              <div className="flex items-center gap-2 text-xs text-slate-500">
                Ostatnia aktualizacja: {new Date(selectedThread.updated_at).toLocaleString('pl-PL')}
              </div>
            </div>

            <div className="overflow-hidden rounded-lg border border-slate-200">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                  <tr>
                    <th className="px-4 py-3">Nadawca</th>
                    <th className="px-4 py-3">Odbiorca</th>
                    <th className="px-4 py-3">Data</th>
                    <th className="px-4 py-3">Treść</th>
                    <th className="px-4 py-3">Załącznik</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {messages.map((message) => (
                    <tr key={message.id} className="align-top">
                      <td className="px-4 py-3 text-xs text-slate-600">{message.sender?.email ?? 'System'}</td>
                      <td className="px-4 py-3 text-xs text-slate-600">
                        {message.recipient?.email ?? 'Cała grupa'}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-600">
                        {new Date(message.created_at).toLocaleString('pl-PL')}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-700">
                        <span className="block whitespace-pre-wrap">{message.body}</span>
                        {message.is_internal_note && <Badge tone="warning">Notatka wewnętrzna</Badge>}
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-600">
                        {message.attachment ? (
                          <a
                            href={message.attachment.url}
                            className="text-primary underline"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            {message.attachment.name}
                          </a>
                        ) : (
                          '—'
                        )}
                      </td>
                    </tr>
                  ))}
                  {messages.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-4 py-6 text-center text-sm text-slate-500">
                        Brak wiadomości w tym wątku.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <form
              className="space-y-3 border-t border-slate-200 pt-4"
              onSubmit={handleMessageSubmit((values) => {
                const formData = new FormData();
                formData.append('body', values.body);
                const attachment = values.attachment?.item(0);
                if (attachment) {
                  formData.append('attachment', attachment);
                }
                sendMessageMutation.mutate(formData);
              })}
            >
              <label className="block text-sm text-slate-700">
                Treść odpowiedzi
                <textarea
                  rows={3}
                  className="mt-2 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                  placeholder="Napisz odpowiedź..."
                  {...registerMessage('body', { required: true })}
                />
              </label>
              <label className="block text-sm text-slate-700">
                Załącznik (opcjonalnie)
                <input type="file" className="mt-2 w-full text-sm" {...registerMessage('attachment')} />
              </label>
              <Button type="submit" isLoading={sendMessageMutation.isPending}>
                Wyślij odpowiedź
              </Button>
            </form>
          </>
        ) : (
          <div className="flex min-h-[240px] items-center justify-center text-sm text-slate-500">
            Wybierz wątek, aby wyświetlić szczegóły komunikacji.
          </div>
        )}
      </Card>
    </div>
  );
}
