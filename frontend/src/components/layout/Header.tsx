import { Layout, Button, Space, Typography, Dropdown } from 'antd';
import { UserOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';

const { Header } = Layout;
const { Text } = Typography;

export default function AppHeader() {
  const navigate = useNavigate();
  const { user, role, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const items = [
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout,
    },
  ];

  return (
    <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 4px rgba(0,0,0,0.05)' }}>
      <div>
        <Text strong style={{ fontSize: 16 }}>{role === 'admin' ? 'Administrator Dashboard' : 'Koordinator Portal'}</Text>
      </div>
      <Space>
        <Dropdown menu={{ items }} placement="bottomRight">
          <Button type="text" icon={<UserOutlined />}>
            {user?.full_name || 'User'}
          </Button>
        </Dropdown>
      </Space>
    </Header>
  );
}
