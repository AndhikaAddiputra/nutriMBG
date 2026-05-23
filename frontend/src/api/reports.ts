import client from './client';

export interface TrendDataPoint {
  date: string;
  score: number;
  is_flagged: boolean;
}

export interface TrendResponse {
  component: string;
  data: TrendDataPoint[];
  has_enough_data: boolean;
}

export const getHistoryTrend = async (days: number = 28, component: string = 'all', educationLevel: string = 'SMP'): Promise<TrendResponse[]> => {
  const response = await client.get<TrendResponse[]>('/api/v1/history/trend', {
    params: {
      days,
      component,
      education_level: educationLevel,
    },
  });
  return response.data;
};

export const getWeeklyReport = async (weekStart: string, sppgName: string, district?: string): Promise<Blob> => {
  const params: Record<string, string> = {
    week_start: weekStart,
    sppg_name: sppgName,
  };
  if (district) {
    params.district = district;
  }
  const response = await client.get('/reports/weekly', {
    params,
    responseType: 'blob',
  });
  return response.data;
};
