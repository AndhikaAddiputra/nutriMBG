import { useState } from 'react';
import { Typography, Row, Col, message } from 'antd';
import MenuForm, { GiziFormValues } from './MenuForm';
import ResultCard from './ResultCard';
import { classifyMenu, recommendMenu, fetchFoods } from '../../api/ai';
import { ClassifyResponse } from '../../types/menu';

const { Title, Paragraph } = Typography;

export default function GiziMeter() {
  const [data, setData] = useState<ClassifyResponse | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingRecs, setLoadingRecs] = useState(false);

  const handleSubmit = async (values: GiziFormValues) => {
    setLoading(true);
    setData(null);
    setRecommendations([]);
    
    try {
      // 1. Classify Menu
      const result = await classifyMenu({
        text: values.text,
        education_level: values.education_level,
        kabupaten: values.kabupaten === 'Semua Kabupaten' ? undefined : values.kabupaten,
      });
      setData(result);

      // 2. Fetch Foods for local catalog
      setLoadingRecs(true);
      const foods = await fetchFoods(values.kabupaten);
      const localCatalog = foods.map(f => f.name);

      // 3. Get Recommendations
      const recResult = await recommendMenu({
        deficiencies: result.labels,
        local_catalog: localCatalog,
        count: values.recommend_count
      });
      setRecommendations(recResult.recommendations);
      
    } catch (err: any) {
      message.error(err.response?.data?.detail || 'Gagal memproses analisa gizi.');
    } finally {
      setLoading(false);
      setLoadingRecs(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>NutriMBG</Title>
        <Paragraph type="secondary">
          Validasi dan rekomendasi gizi untuk Makan Bergizi Gratis (MBG).
        </Paragraph>
      </div>

      <Row gutter={24}>
        <Col xs={24} lg={10} style={{ marginBottom: 24 }}>
          <MenuForm onSubmit={handleSubmit} loading={loading} />
        </Col>
        <Col xs={24} lg={14}>
          <ResultCard 
            data={data} 
            recommendations={recommendations} 
            loadingRecs={loadingRecs} 
          />
        </Col>
      </Row>
    </div>
  );
}
