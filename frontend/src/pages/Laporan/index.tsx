import { 
  Table, 
  Button, 
  Typography, 
  Space, 
  Card, 
  Row, 
  Col, 
  DatePicker, 
  Input, 
  Select, 
  message,
  Spin
} from 'antd';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import dayjs from 'dayjs';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Dot
} from 'recharts';
import { getHistoryTrend, getWeeklyReport } from '../../api/reports';
import { useAuthStore } from '../../store/authStore';

const { Title, Paragraph, Text } = Typography;

const COMPONENT_LABELS: Record<string, string> = {
  composite: 'Skor Komposit',
  protein: 'Protein',
  carbohydrate: 'Karbohidrat',
  fat: 'Lemak',
  fiber: 'Serat',
  iron: 'Zat Besi',
  vitamin_a: 'Vitamin A',
};

const COMPONENT_COLORS: Record<string, string> = {
  composite: '#2E7D32',
  protein: '#E74C3C',
  carbohydrate: '#3498DB',
  fat: '#F39C12',
  fiber: '#2ECC71',
  iron: '#9B59B6',
  vitamin_a: '#E67E22',
};

const COMPONENT_FILTERS = [
  { label: 'Semua Komponen', value: 'all' },
  ...Object.entries(COMPONENT_LABELS).map(([value, label]) => ({ label, value })),
];

const EDUCATION_LEVELS = [
  { label: 'SD Kelas 1–3', value: 'SD_1_3' },
  { label: 'SD Kelas 4–6', value: 'SD_4_6' },
  { label: 'SMP', value: 'SMP' },
  { label: 'SMA', value: 'SMA' },
];

export default function Laporan() {
  const user = useAuthStore((s) => s.user);

  const [componentFilter, setComponentFilter] = useState('all');
  const [educationLevel, setEducationLevel] = useState('SMP');
  const [days, setDays] = useState(28);
  const [weekStart, setWeekStart] = useState(dayjs().startOf('week').add(1, 'day'));
  const [sppgName, setSppgName] = useState(user?.kabupaten ? `SPPG ${user.kabupaten}` : 'SPPG Pusat');
  const [isGenerating, setIsGenerating] = useState(false);

  const { data: trendData, isLoading, refetch } = useQuery({
    queryKey: ['history-trend', days, componentFilter, educationLevel],
    queryFn: () => getHistoryTrend(days, componentFilter, educationLevel),
  });

  const handleDownloadPdf = async () => {
    try {
      setIsGenerating(true);
      const district = user?.kabupaten || 'Jakarta Selatan';
      const blob = await getWeeklyReport(weekStart.format('YYYY-MM-DD'), sppgName, district);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `laporan_mingguan_${sppgName.replace(/\s+/g, '_')}_${weekStart.format('YYYY-MM-DD')}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      message.success('Laporan berhasil diunduh!');
    } catch (err) {
      message.error('Gagal membuat laporan PDF.');
    } finally {
      setIsGenerating(false);
    }
  };

  const chartData = (() => {
    if (!trendData || trendData.length === 0) return [];

    const allDates = [...new Set(trendData.flatMap(t => t.data.map(d => d.date)))].sort();

    return allDates.map(date => {
      const point: Record<string, string | number | boolean> = { date: dayjs(date).format('DD MMM') };
      trendData.forEach(series => {
        const found = series.data.find(d => d.date === date);
        point[series.component] = found ? found.score : null;
        point[`${series.component}_flagged`] = found ? found.is_flagged : false;
      });
      return point;
    });
  })();

  const visibleComponents = componentFilter === 'all'
    ? Object.keys(COMPONENT_LABELS)
    : [componentFilter];

  const columns = [
    { 
      title: 'Komponen', 
      dataIndex: 'component', 
      key: 'component',
      render: (text: string) => COMPONENT_LABELS[text] || text,
    },
    { 
      title: 'Hari Data', 
      dataIndex: 'count', 
      key: 'count', 
    },
    { 
      title: 'Rata-rata', 
      dataIndex: 'average', 
      key: 'average',
      render: (val: number) => `${val.toFixed(1)}%`,
    },
    { 
      title: 'Hari Bermasalah 🔴', 
      dataIndex: 'flagged', 
      key: 'flagged',
      render: (val: number) => <Text type={val > 0 ? 'danger' : 'secondary'}>{val}</Text>,
    },
  ];

  const summaryData = trendData?.map(series => ({
    key: series.component,
    component: series.component,
    count: series.data.length,
    average: series.data.reduce((a, b) => a + b.score, 0) / (series.data.length || 1),
    flagged: series.data.filter(p => p.is_flagged).length,
  })) || [];

  const filteredSummaryData = componentFilter === 'all'
    ? summaryData
    : summaryData.filter(s => s.component === componentFilter);

  const CustomDot = (props: any) => {
    const { cx, cy, payload, dataKey } = props;
    if (payload[`${dataKey}_flagged`]) {
      return (
        <svg x={cx - 6} y={cy - 6} width={12} height={12} fill="red">
          <circle cx="6" cy="6" r="6" stroke="darkred" strokeWidth="1" />
        </svg>
      );
    }
    return <Dot {...props} />;
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={2} style={{ margin: 0 }}>Laporan & Tren Gizi</Title>
        <Paragraph type="secondary">
          Pantau tren skor gizi harian dan unduh laporan mingguan PDF.
        </Paragraph>
      </div>

      <Row gutter={24}>
        {/* PDF Generator Card */}
        <Col span={24}>
          <Card title="Unduh Laporan Mingguan (PDF)">
            <Row gutter={16} align="bottom">
              <Col span={6}>
                <div style={{ marginBottom: 8 }}><Text>Tanggal Mulai (Senin)</Text></div>
                <DatePicker 
                  style={{ width: '100%' }} 
                  value={weekStart} 
                  onChange={(date) => date && setWeekStart(date)}
                  picker="week"
                />
              </Col>
              <Col span={8}>
                <div style={{ marginBottom: 8 }}><Text>Nama SPPG</Text></div>
                <Input 
                  value={sppgName} 
                  onChange={(e) => setSppgName(e.target.value)} 
                  placeholder="Contoh: SPPG Jakarta"
                />
              </Col>
              <Col span={6}>
                <Button 
                  type="primary" 
                  icon={<DownloadOutlined />} 
                  onClick={handleDownloadPdf}
                  loading={isGenerating}
                  block
                >
                  Generate & Unduh PDF
                </Button>
              </Col>
            </Row>
          </Card>
        </Col>

        {/* Filters and Chart */}
        <Col span={24} style={{ marginTop: 24 }}>
          <Card 
            title="Tren Skor Gizi Harian" 
            extra={
              <Space>
                <Select 
                  value={componentFilter} 
                  options={COMPONENT_FILTERS} 
                  onChange={setComponentFilter} 
                  style={{ width: 180 }}
                />
                <Select 
                  value={educationLevel} 
                  options={EDUCATION_LEVELS} 
                  onChange={setEducationLevel} 
                  style={{ width: 150 }}
                />
                <Select 
                  value={days} 
                  options={[7, 14, 21, 28].map(d => ({ label: `${d} Hari`, value: d }))} 
                  onChange={setDays}
                  style={{ width: 120 }}
                />
                <Button icon={<ReloadOutlined />} onClick={() => refetch()} />
              </Space>
            }
          >
            {isLoading ? (
              <div style={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Spin size="large" />
              </div>
            ) : chartData.length < 7 ? (
              <div style={{ height: 400, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Text type="secondary">Butuh minimal 7 hari data untuk menampilkan grafik tren. Saat ini tersedia {chartData.length} hari.</Text>
              </div>
            ) : (
              <>
                <div style={{ height: 400, width: '100%' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                      <XAxis dataKey="date" />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Legend />
                      {visibleComponents.map(comp => (
                        <Line 
                          key={comp}
                          type="monotone" 
                          dataKey={comp} 
                          name={COMPONENT_LABELS[comp] || comp} 
                          stroke={COMPONENT_COLORS[comp] || '#8884d8'} 
                          strokeWidth={2}
                          dot={<CustomDot dataKey={comp} />}
                          connectNulls
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </div>
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    <span style={{ color: 'red', fontWeight: 'bold' }}>●</span> Titik merah menunjukkan tanggal dengan skor di bawah rata-rata secara signifikan (outlier).
                  </Text>
                </div>
              </>
            )}
          </Card>
        </Col>

        {/* Summary Table */}
        <Col span={24} style={{ marginTop: 24 }}>
          <Table 
            title={() => <Title level={5} style={{ margin: 0 }}>Ringkasan per Komponen</Title>}
            columns={columns} 
            dataSource={filteredSummaryData} 
            pagination={false} 
            loading={isLoading}
          />
        </Col>
      </Row>
    </Space>
  );
}
