import client from './client';
import { LoginRequest, LoginResponse } from '../types/auth';

export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await client.post<LoginResponse>('/api/v1/auth/login', data);
  return response.data;
};
