import client from './client';
import { 
  ClassifyRequest, 
  ClassifyResponse, 
  RecommendRequest, 
  RecommendResponse,
  FoodItem
} from '../types/menu';

export const classifyMenu = async (data: ClassifyRequest): Promise<ClassifyResponse> => {
  const response = await client.post<ClassifyResponse>('/api/v1/ai/classify', data);
  return response.data;
};

export const recommendMenu = async (data: RecommendRequest): Promise<RecommendResponse> => {
  const response = await client.post<RecommendResponse>('/api/v1/ai/recommend', data);
  return response.data;
};

export const fetchFoods = async (kabupaten?: string): Promise<FoodItem[]> => {
  const params = kabupaten && kabupaten !== 'Semua Kabupaten' ? { kabupaten } : {};
  const response = await client.get<FoodItem[]>('/api/v1/reference/foods', { params });
  return response.data;
};

export const fetchKabupatens = async (): Promise<string[]> => {
  const response = await client.get<string[]>('/api/v1/reference/kabupatens');
  return response.data;
};
