export interface User {
  id: number;
  full_name: string;
  email: string;
  role: 'coordinator' | 'admin';
  kabupaten?: string;
  is_active: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}
