import { useEffect } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';
import { LogOut } from 'lucide-react';

import { DashboardSidebar } from '@/components/layout/DashboardSidebar';
import { Button } from '@/components/ui/Button';
import { useAuth } from '@/hooks/useAuth';

export function DashboardLayout() {
  const { user, logout, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !user) {
      navigate('/login', { replace: true });
    }
  }, [isLoading, navigate, user]);

  if (isLoading || !user) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">
        Ładowanie profilu użytkownika...
      </div>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-[260px_1fr]">
      <DashboardSidebar />
      <div className="space-y-4">
        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-3 shadow-sm">
          <div>
            <p className="text-sm font-semibold text-slate-800">Witaj, {user.first_name || user.email}</p>
            <p className="text-xs text-slate-500">Rola: {user.role_display}</p>
          </div>
          <Button variant="outline" onClick={logout} className="gap-2 text-sm">
            <LogOut size={16} /> Wyloguj się
          </Button>
        </div>
        <Outlet />
      </div>
    </div>
  );
}
