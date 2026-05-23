import client from '../client';
import {
  AdminUser,
  AdminUserPage,
  AdminUserCreate,
  AdminUserUpdate,
} from '../../types/admin';

export const getAdminUsers = async (
  page: number = 1,
  perPage: number = 20,
  search?: string,
  includeInactive?: boolean
): Promise<AdminUserPage> => {
  const response = await client.get<AdminUserPage>('/api/admin/users', {
    params: { page, per_page: perPage, search, include_inactive: includeInactive },
  });
  return response.data;
};

export const createAdminUser = async (data: AdminUserCreate): Promise<AdminUser> => {
  const response = await client.post<AdminUser>('/api/admin/users', data);
  return response.data;
};

export const updateAdminUser = async (id: number, data: AdminUserUpdate): Promise<AdminUser> => {
  const response = await client.put<AdminUser>(`/api/admin/users/${id}`, data);
  return response.data;
};

export const deleteAdminUser = async (id: number): Promise<void> => {
  await client.delete(`/api/admin/users/${id}`);
};
