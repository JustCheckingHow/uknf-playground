'use client';

import { useEffect, useMemo } from 'react';
import { Controller, useFieldArray, useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import axios from 'axios';
import { toast } from 'sonner';

import { Button } from '@/src/components/ui/Button';
import { Card } from '@/src/components/ui/Card';
import { Badge } from '@/src/components/ui/Badge';
import { apiClient } from '@/src/lib/api';
import { useAuth } from '@/src/hooks/useAuth';
import type {
  AccessRequest,
  AccessRequestLine,
  AccessRequestStatus,
  RegulatedEntity
} from '@/src/types';

const permissionValues = ['reporting', 'cases', 'entity_admin'] as const;

const permissionOptions = [
  { value: permissionValues[0], label: 'Sprawozdawczość' },
  { value: permissionValues[1], label: 'Sprawy' },
  { value: permissionValues[2], label: 'Administrator podmiotu' }
] as const;

type PermissionCode = (typeof permissionValues)[number];

const emailSchema = z
  .string()
  .trim()
  .optional()
  .transform((value) => value ?? '')
  .refine((value) => value === '' || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value), 'Podaj poprawny adres e-mail');

const lineSchema = z.object({
  entity_id: z.string().min(1, 'Wybierz podmiot'),
  contact_email: emailSchema,
  permission_codes: z.array(z.enum(permissionValues)).min(1, 'Wybierz co najmniej jedno uprawnienie')
});

const formSchema = z.object({
  justification: z.string().trim().min(10, 'Uzasadnienie powinno zawierać co najmniej 10 znaków.'),
  lines: z.array(lineSchema).min(1, 'Dodaj minimum jedną linię uprawnień')
});

type FormValues = z.infer<typeof formSchema>;

function mapRequestToForm(request: AccessRequest): FormValues {
  return {
    justification: request.justification || '',
    lines: request.lines.map((line) => ({
      entity_id: String(line.entity.id),
      contact_email: line.contact_email || line.entity.contact_email || '',
      permission_codes: line.permissions.map((perm) => perm.code as PermissionCode)
    }))
  };
}

function toErrorMessage(value: unknown): string {
  if (!value) {
    return 'Wystąpił błąd walidacji.';
  }
  if (Array.isArray(value)) {
    return value.join(' ');
  }
  if (typeof value === 'string') {
    return value;
  }
  return JSON.stringify(value);
}

const statusToLabel: Record<AccessRequestStatus, string> = {
  draft: 'Roboczy',
  new: 'Nowy',
  approved: 'Zaakceptowany',
  blocked: 'Zablokowany',
  updated: 'Zaktualizowany'
};

const statusToTone: Record<AccessRequestStatus, 'default' | 'info' | 'success' | 'warning' | 'danger'> = {
  draft: 'default',
  new: 'info',
  approved: 'success',
  blocked: 'danger',
  updated: 'warning'
};

const nextActorLabels = {
  requester: 'Wnioskodawca',
  entity_admin: 'Administrator podmiotu',
  uknf: 'UKNF',
  none: 'Brak'
} as const;

const lineStatusLabels = {
  pending: 'Oczekujące',
  approved: 'Zaakceptowane',
  blocked: 'Zablokowane',
  needs_update: 'Wymaga aktualizacji'
} as const;

type LineStatus = keyof typeof lineStatusLabels;

type FormLineErrorKey = `lines.${number}.${'entity_id' | 'contact_email' | 'permission_codes'}`;

export default function AccessRequestsPage() {
  const queryClient = useQueryClient();
  const { refreshProfile } = useAuth();

  const accessRequestQuery = useQuery({
    queryKey: ['access-request', 'my-active'],
    queryFn: async () => {
      const response = await apiClient.get<AccessRequest>('/auth/access-requests/my-active/');
      return response.data;
    }
  });

  const entitiesQuery = useQuery({
    queryKey: ['entities'],
    queryFn: async () => {
      const response = await apiClient.get<{ results?: RegulatedEntity[] } | RegulatedEntity[]>('/auth/entities/');
      const payload = Array.isArray(response.data) ? response.data : response.data.results ?? [];
      return payload;
    }
  });

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      justification: '',
      lines: []
    }
  });

  const {
    control,
    handleSubmit,
    reset,
    setError,
    watch,
    formState: { errors }
  } = form;

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'lines'
  });

  const accessRequest = accessRequestQuery.data;

  useEffect(() => {
    if (accessRequest) {
      reset(mapRequestToForm(accessRequest));
    }
  }, [accessRequest, reset]);

  const watchedLines = watch('lines');
  const selectedEntityIds = watchedLines.map((line) => line.entity_id).filter(Boolean);

  const lineByEntityId = useMemo(() => {
    if (!accessRequest) {
      return new Map<number, AccessRequestLine>();
    }
    return new Map(accessRequest.lines.map((line) => [line.entity.id, line]));
  }, [accessRequest]);

  const saveMutation = useMutation({
    mutationFn: async (values: FormValues) => {
      if (!accessRequest) {
        throw new Error('Brak aktywnego wniosku.');
      }
      const payload = {
        justification: values.justification,
        lines: values.lines.map((line) => ({
          entity_id: Number(line.entity_id),
          contact_email: line.contact_email || undefined,
          permission_codes: line.permission_codes
        }))
      };
      const response = await apiClient.patch<AccessRequest>(`/auth/access-requests/${accessRequest.id}/`, payload);
      return response.data;
    },
    onSuccess: async (data) => {
      queryClient.setQueryData(['access-request', 'my-active'], data);
      reset(mapRequestToForm(data));
      toast.success('Zapisano zmiany wniosku.');
    },
    onError: (error) => {
      if (axios.isAxiosError(error) && error.response?.status === 400 && error.response.data) {
        const data = error.response.data as Record<string, unknown>;
        if (data.justification) {
          setError('justification', { type: 'server', message: toErrorMessage(data.justification) });
        }
        if (Array.isArray(data.lines)) {
          data.lines.forEach((item, index) => {
            if (item && typeof item === 'object') {
              const record = item as Record<string, unknown>;
              const entityMessage = record.entity_id ?? record.entity;
              if (entityMessage) {
                setError(`lines.${index}.entity_id` as FormLineErrorKey, {
                  type: 'server',
                  message: toErrorMessage(entityMessage)
                });
              }
              if (record.contact_email) {
                setError(`lines.${index}.contact_email` as FormLineErrorKey, {
                  type: 'server',
                  message: toErrorMessage(record.contact_email)
                });
              }
              if (record.permission_codes || record.permissions) {
                setError(`lines.${index}.permission_codes` as FormLineErrorKey, {
                  type: 'server',
                  message: toErrorMessage(record.permission_codes ?? record.permissions)
                });
              }
            }
          });
        }
        toast.error('Formularz zawiera błędy. Popraw wskazane pola.');
      } else {
        toast.error('Nie udało się zapisać wniosku. Spróbuj ponownie później.');
      }
    }
  });

  const submitMutation = useMutation({
    mutationFn: async () => {
      if (!accessRequest) {
        throw new Error('Brak aktywnego wniosku.');
      }
      const response = await apiClient.post<AccessRequest>(`/auth/access-requests/${accessRequest.id}/submit/`);
      return response.data;
    },
    onSuccess: async (data) => {
      queryClient.setQueryData(['access-request', 'my-active'], data);
      toast.success('Wniosek został przekazany do akceptacji.');
      await refreshProfile();
    },
    onError: () => {
      toast.error('Nie udało się przekazać wniosku. Upewnij się, że wszystkie pola są poprawne.');
    }
  });

  const handleSave = handleSubmit(async (values) => {
    await saveMutation.mutateAsync(values);
  });

  const handleSubmitForSending = handleSubmit(async (values) => {
    await saveMutation.mutateAsync(values);
    await submitMutation.mutateAsync();
  });

  const isLoading = accessRequestQuery.isLoading || entitiesQuery.isLoading;
  const entities = entitiesQuery.data ?? [];
  const canSubmit = accessRequest ? ['draft', 'updated'].includes(accessRequest.status) : false;
  const isSubmittingRequest = submitMutation.isPending || saveMutation.isPending;

  if (isLoading && !accessRequest) {
    return (
      <Card className="space-y-2">
        <h1 className="text-lg font-semibold text-slate-900">Wnioski o dostęp</h1>
        <p className="text-sm text-slate-600">Ładowanie danych wniosku...</p>
      </Card>
    );
  }

  if (!accessRequest) {
    return (
      <Card className="space-y-2">
        <h1 className="text-lg font-semibold text-slate-900">Wnioski o dostęp</h1>
        <p className="text-sm text-slate-600">Nie znaleziono aktywnego wniosku.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-lg font-semibold text-slate-900">Wniosek o dostęp</h1>
            <p className="text-sm text-slate-600">Numer referencyjny: {accessRequest.reference_code}</p>
          </div>
          <Badge tone={statusToTone[accessRequest.status]}>Status: {statusToLabel[accessRequest.status]}</Badge>
        </div>
        <div className="grid gap-3 text-sm text-slate-700 md:grid-cols-2">
          <div>
            <p className="font-medium text-slate-800">Wnioskodawca</p>
            <p>
              {accessRequest.requester_first_name} {accessRequest.requester_last_name}
            </p>
            <p>{accessRequest.requester_email}</p>
            <p>{accessRequest.requester_phone || 'Brak numeru telefonu'}</p>
            <p>PESEL: {accessRequest.requester_pesel_masked || 'nieuzupełniony'}</p>
          </div>
          <div>
            <p className="font-medium text-slate-800">Dalsze kroki</p>
            <p>Kolejny decydent: {nextActorLabels[accessRequest.next_actor]}</p>
            {accessRequest.decided_by && (
              <p>Ostatnia decyzja: {accessRequest.decided_by.name} ({accessRequest.decided_by.email})</p>
            )}
            {accessRequest.submitted_at && (
              <p>Złożono: {new Date(accessRequest.submitted_at).toLocaleString('pl-PL')}</p>
            )}
            {accessRequest.decided_at && (
              <p>Zaktualizowano: {new Date(accessRequest.decided_at).toLocaleString('pl-PL')}</p>
            )}
          </div>
        </div>
      </Card>

      <Card className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">Linie uprawnień i uzasadnienie</h2>
          <Button
            variant="outline"
            type="button"
            onClick={() =>
              append({
                entity_id: '',
                contact_email: '',
                permission_codes: []
              })
            }
          >
            Dodaj podmiot
          </Button>
        </div>
        <form className="space-y-6" onSubmit={handleSave}>
          <label className="block text-sm">
            <span className="text-slate-700">Uzasadnienie wniosku</span>
            <textarea
              className="mt-1 w-full min-h-[120px] rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              {...form.register('justification')}
            />
            {errors.justification && (
              <span className="mt-1 block text-xs text-red-600">{errors.justification.message}</span>
            )}
          </label>

          <div className="space-y-4">
            {fields.map((field, index) => {
              const lineEntityId = watchedLines[index]?.entity_id;
              const existingLine = lineEntityId ? lineByEntityId.get(Number(lineEntityId)) : undefined;
              return (
                <Card key={field.id} className="space-y-4 border border-slate-200 bg-slate-50/60">
                  <div className="flex items-center justify-between">
                    <div className="space-y-1 text-sm">
                      <p className="font-semibold text-slate-800">Linia uprawnień #{index + 1}</p>
                      {existingLine && (
                        <Badge
                          tone={
                            existingLine.status === 'approved'
                              ? 'success'
                              : existingLine.status === 'blocked'
                              ? 'danger'
                              : 'info'
                          }
                        >
                          {lineStatusLabels[existingLine.status as LineStatus]}
                        </Badge>
                      )}
                    </div>
                    <Button variant="ghost" type="button" onClick={() => remove(index)}>
                      Usuń
                    </Button>
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <Controller
                      control={control}
                      name={`lines.${index}.entity_id`}
                      render={({ field: controllerField }) => (
                        <label className="text-sm">
                          <span className="text-slate-700">Podmiot nadzorowany</span>
                          <select
                            className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                            value={controllerField.value}
                            onChange={(event) => controllerField.onChange(event.target.value)}
                          >
                            <option value="">— Wybierz podmiot —</option>
                            {entities.map((entity) => (
                              <option
                                key={entity.id}
                                value={String(entity.id)}
                                disabled={
                                  controllerField.value !== String(entity.id) && selectedEntityIds.includes(String(entity.id))
                                }
                              >
                                {entity.name} ({entity.registration_number})
                              </option>
                            ))}
                          </select>
                          {errors.lines?.[index]?.entity_id && (
                            <span className="mt-1 block text-xs text-red-600">
                              {errors.lines[index]?.entity_id?.message}
                            </span>
                          )}
                        </label>
                      )}
                    />

                    <label className="text-sm">
                      <span className="text-slate-700">E-mail kontaktowy podmiotu</span>
                      <input
                        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
                        {...form.register(`lines.${index}.contact_email` as const)}
                      />
                      {errors.lines?.[index]?.contact_email && (
                        <span className="mt-1 block text-xs text-red-600">
                          {errors.lines[index]?.contact_email?.message}
                        </span>
                      )}
                    </label>
                  </div>

                  <div className="space-y-2">
                    <p className="text-sm font-medium text-slate-700">Wnioskowane uprawnienia</p>
                    <Controller
                      control={control}
                      name={`lines.${index}.permission_codes`}
                      render={({ field: controllerField }) => (
                        <div className="grid gap-2 md:grid-cols-3">
                          {permissionOptions.map((option) => {
                            const isChecked = controllerField.value?.includes(option.value) ?? false;
                            return (
                              <label key={option.value} className="flex items-center gap-2 text-sm text-slate-700">
                                <input
                                  type="checkbox"
                                  className="h-4 w-4 rounded border-slate-300"
                                  checked={isChecked}
                                  onChange={(event) => {
                                    const next = new Set(controllerField.value ?? []);
                                    if (event.target.checked) {
                                      next.add(option.value);
                                    } else {
                                      next.delete(option.value);
                                    }
                                    controllerField.onChange(Array.from(next));
                                  }}
                                />
                                {option.label}
                              </label>
                            );
                          })}
                        </div>
                      )}
                    />
                    {errors.lines?.[index]?.permission_codes && (
                      <span className="block text-xs text-red-600">
                        {errors.lines[index]?.permission_codes?.message as string}
                      </span>
                    )}
                  </div>

                  {existingLine?.decision_notes && (
                    <p className="rounded-md bg-white p-3 text-xs text-slate-600">
                      Ostatnia decyzja: {existingLine.decision_notes}
                    </p>
                  )}
                </Card>
              );
            })}
            {fields.length === 0 && (
              <p className="text-sm text-slate-500">Dodaj przynajmniej jedną linię, aby określić podmiot i uprawnienia.</p>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" isLoading={saveMutation.isPending}>
              Zapisz szkic
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleSubmitForSending}
              disabled={!canSubmit || isSubmittingRequest}
              isLoading={isSubmittingRequest}
            >
              Przekaż do akceptacji
            </Button>
          </div>
        </form>
      </Card>

      <Card className="space-y-3">
        <h2 className="text-lg font-semibold text-slate-900">Historia zmian</h2>
        <div className="space-y-3">
          {accessRequest.history.length === 0 && (
            <p className="text-sm text-slate-600">Historia wniosku będzie widoczna po zapisaniu zmian.</p>
          )}
          {accessRequest.history.map((entry) => (
            <div key={entry.id} className="rounded-md border border-slate-200 bg-white p-3 text-sm text-slate-700">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-slate-800">{entry.action}</p>
                <span className="text-xs text-slate-500">{new Date(entry.created_at).toLocaleString('pl-PL')}</span>
              </div>
              <p className="text-xs text-slate-500">
                {entry.actor ? `${entry.actor.name} (${entry.actor.email})` : 'System'}
              </p>
              {(entry.from_status || entry.to_status) && (
                <p className="text-xs text-slate-500">
                  Status: {entry.from_status ? statusToLabel[entry.from_status as AccessRequestStatus] : '—'} →{' '}
                  {entry.to_status ? statusToLabel[entry.to_status as AccessRequestStatus] : '—'}
                </p>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
