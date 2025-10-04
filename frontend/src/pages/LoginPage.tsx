'use client';

import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useAuth } from '@/hooks/useAuth';

const schema = z.object({
  email: z.string().email('Podaj poprawny adres e-mail'),
  password: z.string().min(8, 'Hasło musi mieć co najmniej 8 znaków')
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const navigate = useNavigate();
  const {
    register,
    handleSubmit,
    formState: { errors }
  } = useForm<FormValues>({
    resolver: zodResolver(schema)
  });

  const onSubmit = async (values: FormValues) => {
    const success = await login(values.email, values.password);
    if (success) {
      navigate('/dashboard');
    }
  };

  return (
    <div className="mx-auto max-w-md">
      <Card className="space-y-6">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Logowanie do platformy</h1>
          <p className="text-sm text-slate-600">
            Użyj służbowego adresu e-mail, aby uzyskać dostęp do modułów UKNF. Logowanie wymaga aktywnego konta.
          </p>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
          <label className="block text-sm">
            <span className="text-slate-700">Adres e-mail</span>
            <input
              type="email"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              autoComplete="email"
              {...register('email')}
            />
            {errors.email && <span className="mt-1 block text-xs text-red-600">{errors.email.message}</span>}
          </label>

          <label className="block text-sm">
            <span className="text-slate-700">Hasło</span>
            <input
              type="password"
              className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-primary focus:outline-none"
              autoComplete="current-password"
              {...register('password')}
            />
            {errors.password && <span className="mt-1 block text-xs text-red-600">{errors.password.message}</span>}
          </label>

          <Button type="submit" className="w-full" isLoading={isLoading}>
            Zaloguj się
          </Button>
        </form>

        <div className="rounded-md bg-slate-50 p-4 text-xs text-slate-600">
          <p className="font-semibold text-slate-700">Pierwszy raz w systemie?</p>
          <p className="mt-1 leading-relaxed">
            <Link to="/register" className="font-semibold text-primary hover:underline">
              Złóż wniosek o utworzenie konta
            </Link>{' '}
            i odbierz link aktywacyjny na e-mail. Jeżeli masz już link, przejdź do{' '}
            <Link to="/activate" className="font-semibold text-primary hover:underline">
              aktywacji konta
            </Link>
            .
          </p>
        </div>
      </Card>
    </div>
  );
}
