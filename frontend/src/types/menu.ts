export interface ParsedIngredient {
  name: string;
  weight_gram: number;
}

export interface ClassifyRequest {
  text: string;
  education_level: string;
  kabupaten?: string;
}

export interface ClassifyResponse {
  analysis_id: number;
  items: ParsedIngredient[];
  totals: Record<string, number>;
  ratios: Record<string, number>;
  labels: Record<string, string>;
  score: number;
  unmatched_items: string[];
}

export interface FoodItem {
  id: number;
  name: string;
  protein: number;
  carbohydrate: number;
  fat: number;
  fiber: number;
  iron: number;
  vitamin_a: number;
}

export interface RecommendRequest {
  deficiencies: Record<string, string>;
  local_catalog: string[];
  count: number;
}

export interface RecommendResponse {
  recommendations: string[];
}
