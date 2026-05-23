import { Form, Input, Button, Card, Select, Slider, Row, Col } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { fetchKabupatens } from '../../api/ai';
import { useAuthStore } from '../../store/authStore';

const { TextArea } = Input;

export interface GiziFormValues {
  text: string;
  education_level: string;
  kabupaten: string;
  recommend_count: number;
}

interface MenuFormProps {
  onSubmit: (values: GiziFormValues) => void;
  loading: boolean;
}

const EDUCATION_LEVELS = [
  { label: 'SD Kelas 1–3', value: 'SD_1_3' },
  { label: 'SD Kelas 4–6', value: 'SD_4_6' },
  { label: 'SMP', value: 'SMP' },
  { label: 'SMA', value: 'SMA' },
];

export default function MenuForm({ onSubmit, loading }: MenuFormProps) {
  const [form] = Form.useForm();
  const user = useAuthStore((s) => s.user);
  const defaultKab = user?.kabupaten || 'Semua Kabupaten';

  const { data: kabupatens = [] } = useQuery({
    queryKey: ['kabupatens'],
    queryFn: fetchKabupatens,
    staleTime: 300000,
  });

  const kabOptions = ['Semua Kabupaten', ...kabupatens];

  return (
    <Card title="Analisa Gizi Menu">
      <Form
        form={form}
        layout="vertical"
        onFinish={onSubmit}
        initialValues={{ 
          education_level: 'SMP', 
          kabupaten: defaultKab,
          recommend_count: 3 
        }}
      >
        <Form.Item
          name="text"
          label="Deskripsi menu harian"
          rules={[{ required: true, message: 'Masukkan deskripsi menu' }]}
        >
          <TextArea 
            placeholder="Contoh: Nasi putih 150g, ayam goreng 1 potong, sayur bayam 1 mangkok" 
            rows={5} 
            maxLength={500}
          />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="education_level"
              label="Jenjang pendidikan"
              rules={[{ required: true }]}
            >
              <Select options={EDUCATION_LEVELS} />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="kabupaten"
              label="Kabupaten"
              rules={[{ required: true }]}
            >
              <Select options={kabOptions.map(k => ({ label: k, value: k }))} />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="recommend_count"
          label="Jumlah rekomendasi menu"
        >
          <Slider min={1} max={5} marks={{ 1: '1', 5: '5' }} />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0 }}>
          <Button 
            type="primary" 
            htmlType="submit" 
            size="large" 
            block 
            icon={<SearchOutlined />} 
            loading={loading}
          >
            Analisa Menu
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
}
