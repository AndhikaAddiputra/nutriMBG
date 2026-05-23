import { Layout, Typography } from 'antd';

const { Footer } = Layout;
const { Text } = Typography;

export default function AppFooter() {
  return (
    <Footer style={{ textAlign: 'center', background: '#fff', borderTop: '1px solid #f0f0f0' }}>
      <Text type="secondary">Referensi: Permenkes RI No. 28/2019 tentang Angka Kecukupan Gizi</Text>
    </Footer>
  );
}
