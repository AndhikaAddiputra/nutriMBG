import { Navigate, Outlet } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

interface RoleGuardProps {
  roles: string[];
}

export const RoleGuard = ({ roles }: RoleGuardProps) => {
  const role = useAuthStore((state) => state.role);

  if (!role || !roles.includes(role)) {
    // Redirect to default route for their role or login
    if (role === 'admin') return <Navigate to="/admin" replace />;
    if (role === 'coordinator') return <Navigate to="/gizi-meter" replace />;
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
