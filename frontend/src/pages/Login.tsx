import { useState } from 'react';
import { Form, Input, Button, Card, Typography, Row, Col, message } from 'antd';
import { UserOutlined, LockOutlined, SafetyOutlined, TeamOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { login } from '../api/auth';
import { useAuthStore } from '../store/authStore';

const { Title, Text } = Typography;

export default function Login() {
  const [role, setRole] = useState<'coordinator' | 'admin'>('coordinator');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const setAuth = useAuthStore((state) => state.setAuth);

  const onFinish = async (values: any) => {
    try {
      setLoading(true);
      const res = await login({ email: values.email, password: values.password });
      
      if (res.user.role !== role) {
        message.error(`Akun ini tidak memiliki akses sebagai ${role === 'admin' ? 'Admin' : 'Koordinator'}`);
        setLoading(false);
        return;
      }

      setAuth(res.access_token, res.user);
      message.success('Login berhasil!');
      
      if (res.user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/gizi-meter');
      }
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Gagal login. Cek kembali email dan password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#F5F7FA' }}>
      <Card style={{ width: 400, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={3} style={{ color: '#2E7D32', margin: 0 }}>🥗 NutriMBG</Title>
          <Text type="secondary">Sistem Manajemen Gizi</Text>
        </div>

        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Card 
              hoverable 
              style={{ 
                textAlign: 'center', 
                borderColor: role === 'coordinator' ? '#2E7D32' : undefined,
                background: role === 'coordinator' ? '#E8F5E9' : undefined
              }}
              onClick={() => setRole('coordinator')}
            >
              <TeamOutlined style={{ fontSize: 24, color: role === 'coordinator' ? '#2E7D32' : undefined }} />
              <div style={{ marginTop: 8, fontSize: 12, fontWeight: role === 'coordinator' ? 'bold' : 'normal' }}>Koordinator</div>
            </Card>
          </Col>
          <Col span={12}>
            <Card 
              hoverable 
              style={{ 
                textAlign: 'center', 
                borderColor: role === 'admin' ? '#2E7D32' : undefined,
                background: role === 'admin' ? '#E8F5E9' : undefined
              }}
              onClick={() => setRole('admin')}
            >
              <SafetyOutlined style={{ fontSize: 24, color: role === 'admin' ? '#2E7D32' : undefined }} />
              <div style={{ marginTop: 8, fontSize: 12, fontWeight: role === 'admin' ? 'bold' : 'normal' }}>Admin</div>
            </Card>
          </Col>
        </Row>

        <Form
          name="login"
          initialValues={{ email: role === 'admin' ? 'admin@nutrimbg.id' : 'koordinator@nutrimbg.id', password: 'password123' }}
          onFinish={onFinish}
          layout="vertical"
        >
          <Form.Item
            name="email"
            rules={[{ required: true, message: 'Masukkan email Anda!' }]}
          >
            <Input prefix={<UserOutlined />} placeholder="Email" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Masukkan password Anda!' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" block loading={loading}>
              Masuk
            </Button>
          </Form.Item>
        </Form>
        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>Referensi: Permenkes RI No. 28/2019</Text>
        </div>
      </Card>
    </div>
  );
}
