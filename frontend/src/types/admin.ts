export interface DashboardStats {
  total_users: number;
  total_foods: number;
  total_analyses: number;
  total_akg_entries: number;
  average_score: number;
  today_analyses: number;
  recent_analyses: RecentAnalysisItem[];
}

export interface RecentAnalysisItem {
  id: number;
  user_id: number;
  menu_text: string;
  education_level: string;
  score_total: number;
  created_at: string;
}

export interface AdminUser {
  id: number;
  full_name: string;
  email: string;
  role: string;
  province: string;
  kabupaten: string;
  default_education_level: string;
  is_active: boolean;
}

export interface AdminUserPage {
  items: AdminUser[];
  total: number;
  page: number;
  per_page: number;
}

export interface AdminUserCreate {
  full_name: string;
  email: string;
  password: string;
  role: string;
  province: string;
  kabupaten: string;
  default_education_level: string;
}

export interface AdminUserUpdate {
  full_name?: string;
  email?: string;
  password?: string;
  role?: string;
  province?: string;
  kabupaten?: string;
  default_education_level?: string;
  is_active?: boolean;
}

export interface FoodItemOut {
  id: number;
  name: string;
  source: string;
  protein: number;
  carbohydrate: number;
  fat: number;
  fiber: number;
  iron: number;
  vitamin_a: number;
  is_active: boolean;
}

export interface FoodItemPage {
  items: FoodItemOut[];
  total: number;
  page: number;
  per_page: number;
}

export interface FoodItemCreate {
  name: string;
  source?: string;
  protein: number;
  carbohydrate: number;
  fat: number;
  fiber: number;
  iron: number;
  vitamin_a: number;
}

export interface FoodItemUpdate {
  name?: string;
  source?: string;
  protein?: number;
  carbohydrate?: number;
  fat?: number;
  fiber?: number;
  iron?: number;
  vitamin_a?: number;
}

export interface AKGOut {
  id: number;
  education_level: string;
  nutrient_code: string;
  target_value: number;
  unit: string;
  source: string;
}

export interface AKGCreate {
  education_level: string;
  nutrient_code: string;
  target_value: number;
  unit?: string;
  source?: string;
}

export interface AKGUpdate {
  target_value?: number;
  unit?: string;
  source?: string;
}

export const NUTRIENT_CODES = ['protein', 'carbohydrate', 'fat', 'fiber', 'iron', 'vitamin_a'] as const;

export const EDUCATION_LEVELS = ['SD_1_3', 'SD_4_6', 'SMP', 'SMA'] as const;

export const NUTRIENT_LABELS: Record<string, string> = {
  protein: 'Protein (g)',
  carbohydrate: 'Karbohidrat (g)',
  fat: 'Lemak (g)',
  fiber: 'Serat (g)',
  iron: 'Zat Besi (mg)',
  vitamin_a: 'Vitamin A (mcg)',
};
