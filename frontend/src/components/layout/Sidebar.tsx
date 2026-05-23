import { Layout, Menu } from 'antd';
import { 
  HomeOutlined, 
  BarChartOutlined, 
  FileTextOutlined, 
  SettingOutlined,
  UserOutlined,
  CoffeeOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const { Sider } = Layout;

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const role = useAuthStore((state) => state.role);

  const koordinatorItems = [
    { key: '/gizi-meter', icon: <BarChartOutlined />, label: 'GiziMeter' },
    { key: '/laporan', icon: <FileTextOutlined />, label: 'Laporan' },
  ];

  const adminItems = [
    { key: '/admin', icon: <HomeOutlined />, label: 'Dashboard' },
    { key: '/admin/users', icon: <UserOutlined />, label: 'Pengguna' },
    { key: '/admin/makanan', icon: <CoffeeOutlined />, label: 'Makanan' },
    { key: '/admin/akg', icon: <DatabaseOutlined />, label: 'AKG' },
    { key: '/admin/analisa', icon: <SettingOutlined />, label: 'Analisa Terbaru' },
  ];

  const items = role === 'admin' ? adminItems : koordinatorItems;

  return (
    <Sider width={250} style={{ minHeight: '100vh', background: '#1B5E20' }}>
      <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 20, fontWeight: 'bold' }}>
        🥗 NutriMBG
      </div>
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[location.pathname]}
        items={items}
        onClick={({ key }) => navigate(key)}
        style={{ background: '#1B5E20' }}
      />
    </Sider>
  );
}
