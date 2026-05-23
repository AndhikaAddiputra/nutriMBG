import client from '../client';
import { DashboardStats } from '../../types/admin';

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await client.get<DashboardStats>('/api/admin/stats');
  return response.data;
};
