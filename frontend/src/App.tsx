import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';

import { RootLayout } from '@/layouts/RootLayout';
import { DashboardLayout } from '@/layouts/DashboardLayout';
import { QueryProvider } from '@/providers/QueryProvider';
import { AuthProvider } from '@/providers/AuthProvider';

import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/LoginPage';
import RegisterPage from '@/pages/RegisterPage';
import ActivatePage from '@/pages/ActivatePage';
import DashboardHomePage from '@/pages/dashboard/DashboardHomePage';
import ReportsPage from '@/pages/dashboard/ReportsPage';
import MessagesPage from '@/pages/dashboard/MessagesPage';
import AnnouncementsPage from '@/pages/dashboard/AnnouncementsPage';
import LibraryPage from '@/pages/dashboard/LibraryPage';
import AccessRequestsPage from '@/pages/dashboard/AccessRequestsPage';
import SettingsPage from '@/pages/dashboard/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <QueryProvider>
        <AuthProvider>
          <Toaster richColors position="top-right" />
          <Routes>
            <Route element={<RootLayout />}>
              <Route index element={<HomePage />} />
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
              <Route path="activate" element={<ActivatePage />} />

              <Route path="dashboard" element={<DashboardLayout />}>
                <Route index element={<DashboardHomePage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="messages" element={<MessagesPage />} />
                <Route path="announcements" element={<AnnouncementsPage />} />
                <Route path="library" element={<LibraryPage />} />
                <Route path="access-requests" element={<AccessRequestsPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>
            </Route>
          </Routes>
        </AuthProvider>
      </QueryProvider>
    </BrowserRouter>
  );
}
