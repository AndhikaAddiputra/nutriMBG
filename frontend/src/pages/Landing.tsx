import { Layout, Typography, Button, Row, Col, Card } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Header, Content, Footer } = Layout;
const { Title, Paragraph, Text } = Typography;

export default function Landing() {
  const navigate = useNavigate();

  return (
    <Layout style={{ minHeight: '100vh', background: '#FFFFFF' }}>
      <Header style={{ 
        background: '#FFFFFF', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        padding: '0 50px',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <div style={{ color: '#2E7D32', fontSize: '24px', fontWeight: 'bold' }}>🥗 NutriMBG</div>
        <Button type="primary" size="large" onClick={() => navigate('/login')}>
          Masuk ke Sistem
        </Button>
      </Header>

      <Content>
        {/* Hero Section */}
        <div style={{ padding: '100px 50px', textAlign: 'center', background: '#F5F7FA' }}>
          <Row justify="center">
            <Col xs={24} md={16}>
              <Title style={{ fontSize: '48px', color: '#1B5E20', marginBottom: '24px' }}>
                Sistem Manajemen Gizi Nasional
              </Title>
              <Paragraph style={{ fontSize: '20px', color: '#666', marginBottom: '40px' }}>
                Platform terintegrasi untuk validasi, analisis, dan rekomendasi komposisi 
                Makan Bergizi Gratis (MBG) berbasis standar kesehatan nasional.
              </Paragraph>
              <Button type="primary" size="large" style={{ height: '50px', padding: '0 40px', fontSize: '18px' }} onClick={() => navigate('/login')}>
                Mulai Analisis Menu
              </Button>
            </Col>
          </Row>
        </div>

        {/* Info Section */}
        <div style={{ padding: '80px 50px' }}>
          <Row gutter={[32, 32]} justify="center">
            <Col xs={24} md={8}>
              <Card bordered={false} style={{ height: '100%', background: '#F9F9F9' }}>
                <Title level={4} style={{ color: '#2E7D32' }}>Analisis Presisi</Title>
                <Paragraph>
                  Melakukan kalkulasi otomatis kandungan protein, karbohidrat, lemak, serat, 
                  hingga mikronutrien seperti zat besi dan vitamin A dari deskripsi menu Anda.
                </Paragraph>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card bordered={false} style={{ height: '100%', background: '#F9F9F9' }}>
                <Title level={4} style={{ color: '#2E7D32' }}>Standar AKG</Title>
                <Paragraph>
                  Hasil analisis divalidasi langsung terhadap Angka Kecukupan Gizi (AKG) 
                  sesuai kategori jenjang pendidikan (SD, SMP, SMA).
                </Paragraph>
              </Card>
            </Col>
            <Col xs={24} md={8}>
              <Card bordered={false} style={{ height: '100%', background: '#F9F9F9' }}>
                <Title level={4} style={{ color: '#2E7D32' }}>Katalog Lokal</Title>
                <Paragraph>
                  Memberikan rekomendasi menu alternatif yang memanfaatkan bahan makanan 
                  tersedia di wilayah kabupaten/kota masing-masing.
                </Paragraph>
              </Card>
            </Col>
          </Row>
        </div>

        {/* Regulatory Section */}
        <div style={{ padding: '60px 50px', textAlign: 'center', borderTop: '1px solid #f0f0f0' }}>
          <Text type="secondary" style={{ fontSize: '16px' }}>
            Berdasarkan Peraturan Menteri Kesehatan Republik Indonesia Nomor 28 Tahun 2019 
            tentang Angka Kecukupan Gizi yang Dianjurkan untuk Masyarakat Indonesia.
          </Text>
        </div>
      </Content>

      <Footer style={{ textAlign: 'center', background: '#1B5E20', color: 'rgba(255,255,255,0.65)', padding: '24px 50px' }}>
        NutriMBG © 2026 • Sistem Informasi Gizi Terpadu
      </Footer>
    </Layout>
  );
}
