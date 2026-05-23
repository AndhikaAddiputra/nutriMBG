import { useMutation, useQueryClient } from '@tanstack/react-query';
import { classifyMenu } from '../api/ai';
import { message } from 'antd';

export function useClassify() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: classifyMenu,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['riwayat'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Gagal melakukan klasifikasi menu.');
    }
  });
}
