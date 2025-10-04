'use client';

import { useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Controller, useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { isAxiosError } from 'axios';
import { toast } from 'sonner';
import Select from 'react-select';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { apiClient } from '@/lib/api';
import type { User } from '@/types';
import { select2Styles, type SelectOption } from '@/components/ui/select2Styles';
import { USER_TYPE_SELECT_OPTIONS } from '@/lib/userTypes';

const schema = z.object({
  first_name: z
    .string()
    .min(2, 'Imię musi zawierać co najmniej 2 znaki')
    .max(150, 'Imię jest zbyt długie'),
  last_name: z
    .string()
    .min(2, 'Nazwisko musi zawierać co najmniej 2 znaki')
    .max(150, 'Nazwisko jest zbyt długie'),
  email: z.string().email('Podaj poprawny adres e-mail'),
  phone_number: z
    .string()
    .trim()
    .min(7, 'Numer telefonu musi zawierać co najmniej 7 znaków')
    .regex(/^[0-9+ ]+$/, 'Dozwolone są tylko cyfry, spacje oraz znak +'),
  pesel: z
    .string()
    .trim()
    .regex(/^\d{11}$/, 'PESEL musi składać się z 11 cyfr'),
  user_type: z.enum(['bank', 'fundusz_inwestycyjny', 'inne'], {
    required_error: 'Wybierz typ instytucji'
  }),
  role: z.enum(['entity_admin', 'submitter'])
});

type FormValues = z.infer<typeof schema>;

interface RegistrationResponse {
  detail: string;
  user: User;
}

export default function RegisterPage() {
  const [lastRegisteredUser, setLastRegisteredUser] = useState<{ email: string; peselMasked?: string } | null>(null);
  const {
    register,
    handleSubmit,
    reset,
    setError,
    control,
    formState: { errors, isSubmitting }
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      role: 'entity_admin',
      user_type: 'bank'
    }
  });

  const roleOptions = useMemo(
    () => [
      {
        value: 'entity_admin',
        title: 'Administrator podmiotu',
        description: 'Zarządza użytkownikami w podmiocie i odpowiada za konfigurację profilu.'
      },
      {
        value: 'submitter',
        title: 'Pracownik raportujący',
        description: 'Wysyła sprawozdania i dokumenty do UKNF w imieniu podmiotu.'
      }
    ],
    []
  );

  const onSubmit = handleSubmit(async (values) => {
    try {
      const response = await apiClient.post<RegistrationResponse>('/auth/register', values);
      setLastRegisteredUser({ email: response.data.user.email, peselMasked: response.data.user.pesel_masked });
      toast.success('Link aktywacyjny został wysłany na podany adres e-mail.');
      reset({
        role: values.role,
        user_type: values.user_type,
        email: '',
        first_name: '',
        last_name: '',
        pesel: '',
        phone_number: ''
      });
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 400 && error.response.data) {
        const data = error.response.data as Record<string, string | string[]>;
        let generalError: string | null = null;
        Object.entries(data).forEach(([field, message]) => {
          const joined = Array.isArray(message) ? message.join(' ') : message;
          if (
            field === 'first_name' ||
            field === 'last_name' ||
            field === 'email' ||
            field === 'phone_number' ||
            field === 'pesel' ||
            field === 'user_type' ||
            field === 'role'
          ) {
            setError(field as keyof FormValues, { message: joined });
          } else {
            generalError = joined;
          }
        });
        if (generalError) {
          toast.error(generalError);
        }
      } else {
        toast.error('Nie udało się zarejestrować użytkownika. Spróbuj ponownie później.');
      }
    }
  });

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <Card className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-xl font-semibold text-slate-900">Rejestracja użytkownika zewnętrznego</h1>
          <p className="text-sm text-slate-600">
            Wypełnij formularz, aby utworzyć konto dla podmiotu nadzorowanego. Po przesłaniu otrzymasz mail z linkiem do
            aktywacji i ustawienia hasła.
          </p>
        </div>
        <form className="space-y-5" onSubmit={onSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="text-slate-700">Imię</span>
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                {...register('first_name')}
                autoComplete="given-name"
              />
              {errors.first_name && (
                <span className="mt-1 block text-xs text-red-600">{errors.first_name.message}</span>
              )}
            </label>

            <label className="text-sm">
              <span className="text-slate-700">Nazwisko</span>
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                {...register('last_name')}
                autoComplete="family-name"
              />
              {errors.last_name && (
                <span className="mt-1 block text-xs text-red-600">{errors.last_name.message}</span>
              )}
            </label>

            <label className="text-sm">
              <span className="text-slate-700">Adres e-mail</span>
              <input
                type="email"
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                {...register('email')}
                autoComplete="email"
              />
              {errors.email && <span className="mt-1 block text-xs text-red-600">{errors.email.message}</span>}
            </label>

            <label className="text-sm">
              <span className="text-slate-700">Telefon kontaktowy</span>
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                {...register('phone_number')}
                autoComplete="tel"
              />
              {errors.phone_number && (
                <span className="mt-1 block text-xs text-red-600">{errors.phone_number.message}</span>
              )}
            </label>
          </div>

          <label className="block text-sm">
            <span className="text-slate-700">PESEL</span>
            <input
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              {...register('pesel')}
              inputMode="numeric"
              autoComplete="off"
              maxLength={11}
            />
            <span className="mt-1 block text-xs text-slate-500">
              Numer jest wykorzystywany wyłącznie do weryfikacji i widoczny w systemie w formie maskowanej.
            </span>
            {errors.pesel && <span className="mt-1 block text-xs text-red-600">{errors.pesel.message}</span>}
          </label>

          <Controller
            name="user_type"
            control={control}
            render={({ field }) => (
              <label className="block text-sm">
                <span className="text-slate-700">Typ instytucji</span>
                <Select<SelectOption>
                  className="mt-1"
                  classNamePrefix="select2"
                  inputId="registration-user-type"
                  instanceId="registration-user-type"
                  options={USER_TYPE_SELECT_OPTIONS}
                  value={USER_TYPE_SELECT_OPTIONS.find((option) => option.value === field.value) ?? null}
                  onChange={(option) => field.onChange(option?.value ?? 'bank')}
                  onBlur={field.onBlur}
                  styles={select2Styles}
                  isSearchable
                />
                {errors.user_type && (
                  <span className="mt-1 block text-xs text-red-600">{errors.user_type.message}</span>
                )}
              </label>
            )}
          />

          <fieldset className="space-y-3">
            <legend className="text-sm font-medium text-slate-700">Rola w systemie</legend>
            <div className="grid gap-3 md:grid-cols-2">
              {roleOptions.map((option) => (
                <label
                  key={option.value}
                  className="flex cursor-pointer gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm transition hover:border-primary"
                >
                  <input
                    type="radio"
                    value={option.value}
                    className="mt-1"
                    {...register('role')}
                  />
                  <span>
                    <span className="block font-semibold text-slate-800">{option.title}</span>
                    <span className="mt-1 block text-xs text-slate-600">{option.description}</span>
                  </span>
                </label>
              ))}
            </div>
            {errors.role && <span className="block text-xs text-red-600">{errors.role.message}</span>}
          </fieldset>

          <Button type="submit" className="w-full md:w-auto" isLoading={isSubmitting}>
            Wyślij wniosek o konto
          </Button>
        </form>
      </Card>

      <Card>
        <div className="space-y-3 text-sm text-slate-600">
          <p className="font-semibold text-slate-800">Co dalej?</p>
          <ol className="list-decimal space-y-2 pl-5">
            <li>Sprawdź skrzynkę e-mail i kliknij w link aktywacyjny.</li>
            <li>Ustaw hasło spełniające wymogi bezpieczeństwa (min. 12 znaków).</li>
            <li>Zaloguj się do platformy i wybierz podmiot, z którym pracujesz.</li>
          </ol>
          <p>
            Masz już link aktywacyjny?{' '}
            <Link to="/activate" className="font-semibold text-primary hover:underline">
              Aktywuj konto
            </Link>
            .
          </p>
          {lastRegisteredUser && (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-4 text-xs text-slate-600">
              <p className="font-semibold text-slate-700">Ostatnio zgłoszony użytkownik</p>
              <p className="mt-1">Adres e-mail: {lastRegisteredUser.email}</p>
              {lastRegisteredUser.peselMasked && <p>PESEL (maskowany): {lastRegisteredUser.peselMasked}</p>}
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}
