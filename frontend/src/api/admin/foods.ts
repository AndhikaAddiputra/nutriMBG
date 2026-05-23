import client from '../client';
import {
  FoodItemOut,
  FoodItemPage,
  FoodItemCreate,
  FoodItemUpdate,
} from '../../types/admin';

export const getAdminFoods = async (
  page: number = 1,
  perPage: number = 20,
  search?: string,
  includeInactive?: boolean
): Promise<FoodItemPage> => {
  const response = await client.get<FoodItemPage>('/api/admin/food-items', {
    params: { page, per_page: perPage, search, include_inactive: includeInactive },
  });
  return response.data;
};

export const createFoodItem = async (data: FoodItemCreate): Promise<FoodItemOut> => {
  const response = await client.post<FoodItemOut>('/api/admin/food-items', data);
  return response.data;
};

export const updateFoodItem = async (id: number, data: FoodItemUpdate): Promise<FoodItemOut> => {
  const response = await client.put<FoodItemOut>(`/api/admin/food-items/${id}`, data);
  return response.data;
};

export const deleteFoodItem = async (id: number): Promise<void> => {
  await client.delete(`/api/admin/food-items/${id}`);
};
