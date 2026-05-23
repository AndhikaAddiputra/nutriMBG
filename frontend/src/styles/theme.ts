import type { ThemeConfig } from 'antd';

export const theme: ThemeConfig = {
  token: {
    colorPrimary: '#2E7D32',       // Hijau MBG
    colorSuccess: '#4CAF50',
    colorWarning: '#FF9800',
    colorError: '#F44336',
    colorInfo: '#2196F3',
    borderRadius: 8,
    fontFamily: "'Inter', -apple-system, sans-serif",
  },
  components: {
    Layout: {
      siderBg: '#1B5E20',
      headerBg: '#FFFFFF',
      bodyBg: '#F5F7FA',
    },
    Menu: {
      darkItemBg: '#1B5E20',
      darkItemSelectedBg: '#2E7D32',
    },
  },
};
