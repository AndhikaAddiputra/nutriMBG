import client from '../client';
import { AKGOut, AKGCreate, AKGUpdate } from '../../types/admin';

export const getAKGList = async (educationLevel?: string): Promise<AKGOut[]> => {
  const params = educationLevel ? { education_level: educationLevel } : {};
  const response = await client.get<AKGOut[]>('/api/admin/nutrition-akg', { params });
  return response.data;
};

export const createOrUpdateAKG = async (data: AKGCreate): Promise<AKGOut> => {
  const response = await client.post<AKGOut>('/api/admin/nutrition-akg', data);
  return response.data;
};

export const updateAKG = async (id: number, data: AKGUpdate): Promise<AKGOut> => {
  const response = await client.put<AKGOut>(`/api/admin/nutrition-akg/${id}`, data);
  return response.data;
};
