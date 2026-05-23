import { Layout } from 'antd';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import AppHeader from './Header';
import AppFooter from './Footer';

const { Content } = Layout;

export default function MainLayout() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <AppHeader />
        <Content style={{ margin: '24px 16px', padding: 24, background: '#F5F7FA', borderRadius: 8 }}>
          <Outlet />
        </Content>
        <AppFooter />
      </Layout>
    </Layout>
  );
}
