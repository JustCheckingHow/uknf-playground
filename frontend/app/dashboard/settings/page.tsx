'use client';

import type { ComponentProps } from 'react';
import { useEffect } from 'react';
import { Controller, useForm } from 'react-hook-form';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { Button } from '@/src/components/ui/Button';
import { Card } from '@/src/components/ui/Card';
import { apiClient } from '@/src/lib/api';
import { useAuth } from '@/src/hooks/useAuth';

interface NotificationPreferences {
  notify_via_email: boolean;
  notify_via_sms: boolean;
  daily_digest: boolean;
  weekly_digest: boolean;
}

interface PasswordPolicy {
  min_length: number;
  require_uppercase: boolean;
  require_lowercase: boolean;
  require_numbers: boolean;
  require_special: boolean;
  password_expiry_days: number;
  reuse_history: number;
  lockout_threshold: number;
  lockout_duration_minutes: number;
}

const notificationDefaults: NotificationPreferences = {
  notify_via_email: true,
  notify_via_sms: false,
  daily_digest: true,
  weekly_digest: false
};

export default function SettingsPage() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const preferencesQuery = useQuery({
    queryKey: ['notification-preferences'],
    queryFn: async () => {
      const response = await apiClient.get<NotificationPreferences>('/auth/preferences');
      return response.data;
    }
  });

  const passwordPolicyQuery = useQuery({
    queryKey: ['password-policy'],
    enabled: Boolean(user?.is_internal),
    queryFn: async () => {
      const response = await apiClient.get<PasswordPolicy>('/admin/password-policy');
      return response.data;
    }
  });

  const preferencesForm = useForm<NotificationPreferences>({
    defaultValues: notificationDefaults
  });

  useEffect(() => {
    if (preferencesQuery.data) {
      preferencesForm.reset(preferencesQuery.data);
    }
  }, [preferencesForm, preferencesQuery.data]);

  const passwordPolicyForm = useForm<PasswordPolicy>({
    defaultValues: {
      min_length: 12,
      require_uppercase: true,
      require_lowercase: true,
      require_numbers: true,
      require_special: true,
      password_expiry_days: 90,
      reuse_history: 5,
      lockout_threshold: 5,
      lockout_duration_minutes: 15
    }
  });

  useEffect(() => {
    if (passwordPolicyQuery.data) {
      passwordPolicyForm.reset(passwordPolicyQuery.data);
    }
  }, [passwordPolicyForm, passwordPolicyQuery.data]);

  const preferencesMutation = useMutation({
    mutationFn: async (values: NotificationPreferences) => {
      await apiClient.put('/auth/preferences', values);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notification-preferences'] })
  });

  const passwordPolicyMutation = useMutation({
    mutationFn: async (values: PasswordPolicy) => {
      await apiClient.put('/admin/password-policy', values);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['password-policy'] })
  });

  return (
    <div className="space-y-6">
      <Card className="space-y-4">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">Powiadomienia</h1>
          <p className="text-sm text-slate-600">Dostosuj sposób otrzymywania informacji o ważnych zdarzeniach.</p>
        </div>
        <form
          className="space-y-3"
          onSubmit={preferencesForm.handleSubmit((values) => preferencesMutation.mutate(values))}
        >
          <Controller
            name="notify_via_email"
            control={preferencesForm.control}
            render={({ field }) => (
              <ToggleField
                label="Powiadomienia e-mail"
                description="Informacje o nowych komunikatach, wiadomościach i sprawach."
                checked={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Controller
            name="notify_via_sms"
            control={preferencesForm.control}
            render={({ field }) => (
              <ToggleField
                label="Powiadomienia SMS"
                description="Wymaga zdefiniowanego służbowego numeru telefonu."
                checked={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Controller
            name="daily_digest"
            control={preferencesForm.control}
            render={({ field }) => (
              <ToggleField
                label="Dzienne podsumowanie"
                description="E-mail z listą zadań oczekujących na Twoją reakcję."
                checked={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Controller
            name="weekly_digest"
            control={preferencesForm.control}
            render={({ field }) => (
              <ToggleField
                label="Cotygodniowy raport"
                description="Podsumowanie aktywności w Twoich sprawach oraz raportach."
                checked={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Button type="submit" isLoading={preferencesMutation.isPending}>
            Zapisz ustawienia powiadomień
          </Button>
        </form>
      </Card>

      {user?.is_internal && (
        <Card className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Polityka haseł</h2>
            <p className="text-sm text-slate-600">
              Parametry wymuszane przy tworzeniu i zmianie haseł użytkowników. Aktualizacje są logowane w dzienniku audytu.
            </p>
          </div>
          <form
            className="grid gap-4 md:grid-cols-2"
            onSubmit={passwordPolicyForm.handleSubmit((values) => passwordPolicyMutation.mutate(values))}
          >
            <NumberField
              label="Minimalna długość"
              {...passwordPolicyForm.register('min_length', { valueAsNumber: true })}
            />
            <NumberField
              label="Wygaśnięcie hasła (dni)"
              {...passwordPolicyForm.register('password_expiry_days', { valueAsNumber: true })}
            />
            <NumberField
              label="Historia haseł"
              {...passwordPolicyForm.register('reuse_history', { valueAsNumber: true })}
            />
            <NumberField
              label="Próg blokady"
              {...passwordPolicyForm.register('lockout_threshold', { valueAsNumber: true })}
            />
            <NumberField
              label="Czas blokady (minuty)"
              {...passwordPolicyForm.register('lockout_duration_minutes', { valueAsNumber: true })}
            />

            <Controller
              name="require_uppercase"
              control={passwordPolicyForm.control}
              render={({ field }) => (
                <ToggleField label="Wymagaj wielkich liter" checked={field.value} onChange={field.onChange} />
              )}
            />
            <Controller
              name="require_lowercase"
              control={passwordPolicyForm.control}
              render={({ field }) => (
                <ToggleField label="Wymagaj małych liter" checked={field.value} onChange={field.onChange} />
              )}
            />
            <Controller
              name="require_numbers"
              control={passwordPolicyForm.control}
              render={({ field }) => <ToggleField label="Wymagaj cyfr" checked={field.value} onChange={field.onChange} />}
            />
            <Controller
              name="require_special"
              control={passwordPolicyForm.control}
              render={({ field }) => (
                <ToggleField label="Wymagaj znaków specjalnych" checked={field.value} onChange={field.onChange} />
              )}
            />
            <div className="md:col-span-2">
              <Button type="submit" isLoading={passwordPolicyMutation.isPending}>
                Aktualizuj politykę haseł
              </Button>
            </div>
          </form>
        </Card>
      )}
    </div>
  );
}

function ToggleField({ label, description, checked, onChange }: { label: string; description?: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <label className="flex items-start gap-3 rounded-lg border border-slate-200 bg-white p-3 text-sm">
      <input
        type="checkbox"
        className="mt-1 h-4 w-4"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
      <span>
        <span className="font-semibold text-slate-800">{label}</span>
        {description && <p className="text-xs text-slate-500">{description}</p>}
      </span>
    </label>
  );
}

function NumberField({ label, ...props }: { label: string } & ComponentProps<'input'>) {
  return (
    <label className="text-sm">
      <span className="text-slate-700">{label}</span>
      <input
        type="number"
        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary"
        {...props}
      />
    </label>
  );
}
