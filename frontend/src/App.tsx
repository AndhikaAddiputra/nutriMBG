import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect } from 'react';

import { theme } from './styles/theme';
import { useAuthStore } from './store/authStore';

import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { RoleGuard } from './components/auth/RoleGuard';
import MainLayout from './components/layout/MainLayout';

import Landing from './pages/Landing';
import Login from './pages/Login';
import GiziMeter from './pages/GiziMeter';
import Dashboard from './pages/Dashboard';
import Laporan from './pages/Laporan';
import UserManagement from './pages/Dashboard/UserManagement';
import FoodManagement from './pages/Dashboard/FoodManagement';
import AKGManagement from './pages/Dashboard/AKGManagement';
import RecentAnalysis from './pages/Dashboard/RecentAnalysis';

const queryClient = new QueryClient();

function App() {
  const restore = useAuthStore((state) => state.restore);

  useEffect(() => {
    restore();
  }, [restore]);

  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={theme}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            
            <Route element={<ProtectedRoute />}>
              <Route element={<MainLayout />}>
                
                {/* Koordinator Routes */}
                <Route element={<RoleGuard roles={['coordinator']} />}>
                  <Route path="/gizi-meter" element={<GiziMeter />} />
                  <Route path="/laporan" element={<Laporan />} />
                </Route>

                {/* Administrator Routes */}
                <Route element={<RoleGuard roles={['admin']} />}>
                  <Route path="/admin" element={<Dashboard />} />
                  <Route path="/admin/users" element={<UserManagement />} />
                  <Route path="/admin/makanan" element={<FoodManagement />} />
                  <Route path="/admin/akg" element={<AKGManagement />} />
                  <Route path="/admin/analisa" element={<RecentAnalysis />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  );
}

export default App;
