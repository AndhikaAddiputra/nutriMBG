import { Typography, Tabs } from 'antd';
import StatsCards from './StatsCards';
import RecentAnalysis from './RecentAnalysis';
import UserManagement from './UserManagement';
import FoodManagement from './FoodManagement';
import AKGManagement from './AKGManagement';

const { Title, Paragraph } = Typography;

export default function Dashboard() {
  const items = [
    { key: '1', label: 'Analisa Terbaru', children: <RecentAnalysis /> },
    { key: '2', label: 'Pengguna', children: <UserManagement /> },
    { key: '3', label: 'Makanan', children: <FoodManagement /> },
    { key: '4', label: 'AKG', children: <AKGManagement /> },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>Dashboard Admin</Title>
        <Paragraph type="secondary">
          Ringkasan statistik sistem dan manajemen data NutriMBG.
        </Paragraph>
      </div>

      <StatsCards />

      <div style={{ background: '#fff', padding: 24, borderRadius: 8 }}>
        <Tabs defaultActiveKey="1" items={items} />
      </div>
    </div>
  );
}
