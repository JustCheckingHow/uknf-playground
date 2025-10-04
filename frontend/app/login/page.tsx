'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { Button } from '@/src/components/ui/Button';
import { Card } from '@/src/components/ui/Card';
import { useAuth } from '@/src/hooks/useAuth';

const schema = z.object({
  email: z.string().email('Podaj poprawny adres e-mail'),
  password: z.string().min(8, 'Hasło musi mieć co najmniej 8 znaków')
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const { login, isLoading } = useAuth();
  const router = useRouter();
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
      router.push('/dashboard');
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
            Poproś administratora podmiotu o dodanie Cię do platformy lub wyślij wniosek o dostęp poprzez formularz kontaktowy w module administracyjnym.
          </p>
        </div>
      </Card>
    </div>
  );
}
