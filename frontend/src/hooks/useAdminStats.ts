import { useQuery } from '@tanstack/react-query';
import { getDashboardStats } from '../api/admin/stats';
import { useAuthStore } from '../store/authStore';

export function useAdminStats() {
  const role = useAuthStore((state) => state.role);

  return useQuery({
    queryKey: ['admin-stats'],
    queryFn: getDashboardStats,
    enabled: role === 'admin',
    refetchInterval: 30000, // Background refetch every 30s
  });
}
