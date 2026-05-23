import { Card, Typography, Divider, Alert, Table, List } from 'antd';
import { ScoreGauge } from '../../components/gizi/ScoreGauge';
import { NutrientBar } from '../../components/gizi/NutrientBar';
import { ClassifyResponse } from '../../types/menu';

const { Title, Text } = Typography;

interface ResultCardProps {
  data: ClassifyResponse | null;
  recommendations: string[];
  loadingRecs: boolean;
}

const NUTRIENT_LABELS: Record<string, string> = {
  protein: 'Protein',
  carbohydrate: 'Karbohidrat',
  fat: 'Lemak',
  fiber: 'Serat',
  iron: 'Zat Besi',
  vitamin_a: 'Vitamin A',
};

const NUTRIENT_ICONS: Record<string, string> = {
  protein: '',
  carbohydrate: '',
  fat: '',
  fiber: '',
  iron: '',
  vitamin_a: '',
};

export default function ResultCard({ data, recommendations, loadingRecs }: ResultCardProps) {
  if (!data) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#999' }}>
          Masukkan deskripsi menu untuk melihat hasil analisa.
        </div>
      </Card>
    );
  }

  const ingredientColumns = [
    { title: 'Bahan', dataIndex: 'name', key: 'name' },
    { title: 'Berat (g)', dataIndex: 'weight_gram', key: 'weight_gram', render: (val: number) => val.toFixed(1) },
  ];

  return (
    <Card title="Hasil Analisa Gizi">
      <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 24 }}>
        <ScoreGauge score={data.score} />
      </div>

      <Title level={5}>Parsing Menu</Title>
      <Table 
        dataSource={data.items} 
        columns={ingredientColumns} 
        pagination={false} 
        size="small" 
        rowKey="name"
        style={{ marginBottom: 16 }}
      />

      {data.unmatched_items.length > 0 && (
        <Alert
          message="Item tidak ditemukan di database TKPI sehingga tidak dihitung:"
          description={data.unmatched_items.join(', ')}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Divider>Ringkasan Kecukupan Gizi</Divider>
      {Object.entries(NUTRIENT_LABELS).map(([key, label]) => (
        <NutrientBar 
          key={key}
          label={label} 
          icon={NUTRIENT_ICONS[key]} 
          percent={data.ratios[key] * 100} 
        />
      ))}

      <Divider>Rekomendasi Menu</Divider>
      <List
        loading={loadingRecs}
        dataSource={recommendations}
        renderItem={(item) => (
          <List.Item>
            <Text>• {item}</Text>
          </List.Item>
        )}
        locale={{ emptyText: 'Belum ada rekomendasi yang dihasilkan.' }}
      />
    </Card>
  );
}
