'use client';

import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { isAxiosError } from 'axios';
import { toast } from 'sonner';

import { Button } from '@/src/components/ui/Button';
import { Card } from '@/src/components/ui/Card';
import { apiClient } from '@/src/lib/api';

const passwordSchema = z
  .string()
  .min(12, 'Hasło musi mieć co najmniej 12 znaków')
  .refine((value) => /[A-Z]/.test(value), 'Hasło musi zawierać przynajmniej jedną wielką literę')
  .refine((value) => /[a-z]/.test(value), 'Hasło musi zawierać przynajmniej jedną małą literę')
  .refine((value) => /\d/.test(value), 'Hasło musi zawierać przynajmniej jedną cyfrę')
  .refine((value) => /[^\w\s]/.test(value), 'Hasło musi zawierać znak specjalny');

const schema = z
  .object({
    password: passwordSchema,
    password_confirm: z.string(),
    uid: z.string().min(1, 'Brak identyfikatora użytkownika'),
    token: z.string().min(1, 'Brak tokenu aktywacyjnego')
  })
  .refine((data) => data.password === data.password_confirm, {
    message: 'Hasła muszą być identyczne',
    path: ['password_confirm']
  });

type FormValues = z.infer<typeof schema>;

function ActivateForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const {
    register,
    handleSubmit,
    setValue,
    setError,
    formState: { errors, isSubmitting }
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      password: '',
      password_confirm: '',
      uid: '',
      token: ''
    }
  });

  useEffect(() => {
    const uid = searchParams.get('uid');
    const token = searchParams.get('token');
    if (uid) {
      setValue('uid', uid);
    }
    if (token) {
      setValue('token', token);
    }
  }, [searchParams, setValue]);

  const onSubmit = handleSubmit(async (values) => {
    try {
      await apiClient.post('/auth/activate', values);
      toast.success('Konto zostało aktywowane. Możesz się zalogować.');
      router.push('/login');
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 400 && error.response.data) {
        const data = error.response.data as Record<string, string | string[]>;
        let generalError: string | null = null;
        Object.entries(data).forEach(([field, message]) => {
          const joined = Array.isArray(message) ? message.join(' ') : message;
          if (field === 'password' || field === 'password_confirm' || field === 'uid' || field === 'token') {
            setError(field as keyof FormValues, { message: joined });
          } else {
            generalError = joined;
          }
        });
        if (generalError) {
          toast.error(generalError);
        }
      } else {
        toast.error('Aktywacja konta nie powiodła się. Sprawdź dane i spróbuj ponownie.');
      }
    }
  });

  return (
    <div className="mx-auto max-w-xl space-y-6">
      <Card className="space-y-6">
        <div className="space-y-2">
          <h1 className="text-xl font-semibold text-slate-900">Aktywacja konta</h1>
          <p className="text-sm text-slate-600">
            Ustaw hasło do swojego konta. Wymaga to podania identyfikatora oraz tokenu z wiadomości e-mail przesłanej
            po rejestracji.
          </p>
        </div>
        <form className="space-y-4" onSubmit={onSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">
              <span className="text-slate-700">Identyfikator użytkownika (UID)</span>
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                {...register('uid')}
              />
              {errors.uid && <span className="mt-1 block text-xs text-red-600">{errors.uid.message}</span>}
            </label>

            <label className="text-sm">
              <span className="text-slate-700">Token aktywacyjny</span>
              <input
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
                {...register('token')}
              />
              {errors.token && <span className="mt-1 block text-xs text-red-600">{errors.token.message}</span>}
            </label>
          </div>

          <label className="text-sm">
            <span className="text-slate-700">Hasło</span>
            <input
              type="password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              {...register('password')}
              autoComplete="new-password"
            />
            {errors.password && <span className="mt-1 block text-xs text-red-600">{errors.password.message}</span>}
          </label>

          <label className="text-sm">
            <span className="text-slate-700">Powtórz hasło</span>
            <input
              type="password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              {...register('password_confirm')}
              autoComplete="new-password"
            />
            {errors.password_confirm && (
              <span className="mt-1 block text-xs text-red-600">{errors.password_confirm.message}</span>
            )}
          </label>

          <Button type="submit" className="w-full md:w-auto" isLoading={isSubmitting}>
            Aktywuj konto
          </Button>
        </form>
      </Card>

      <Card>
        <div className="space-y-3 text-sm text-slate-600">
          <p className="font-semibold text-slate-800">Wskazówki dotyczące hasła</p>
          <ul className="list-disc space-y-2 pl-5">
            <li>Hasło musi mieć co najmniej 12 znaków.</li>
            <li>Powinno zawierać małe i wielkie litery, cyfrę oraz znak specjalny.</li>
            <li>Unikaj haseł wykorzystywanych w innych systemach.</li>
          </ul>
          <p className="text-xs text-slate-500">
            Link aktywacyjny jest ważny przez ograniczony czas. Po jego wygaśnięciu poproś administratora o wygenerowanie
            nowego.
          </p>
        </div>
      </Card>
    </div>
  );
}

export default function ActivatePage() {
  return (
    <Suspense fallback={<div className="py-10 text-center text-sm text-slate-500">Wczytywanie danych aktywacyjnych…</div>}>
      <ActivateForm />
    </Suspense>
  );
}
