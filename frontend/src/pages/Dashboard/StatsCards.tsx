import { Row, Col, Card, Statistic } from 'antd';
import { 
  BarChartOutlined, 
  TeamOutlined, 
  CoffeeOutlined, 
  DatabaseOutlined,
  StarOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { useAdminStats } from '../../hooks/useAdminStats';

export default function StatsCards() {
  const { data, isLoading } = useAdminStats();

  return (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col xs={24} sm={12} lg={4}>
        <Card>
          <Statistic
            title="Total Analisa"
            value={data?.total_analyses || 0}
            prefix={<BarChartOutlined />}
            loading={isLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={4}>
        <Card>
          <Statistic
            title="Pengguna Aktif"
            value={data?.total_users || 0}
            prefix={<TeamOutlined />}
            loading={isLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={4}>
        <Card>
          <Statistic
            title="Menu Terdaftar"
            value={data?.total_foods || 0}
            prefix={<CoffeeOutlined />}
            loading={isLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={4}>
        <Card>
          <Statistic
            title="Data AKG"
            value={data?.total_akg_entries || 0}
            prefix={<DatabaseOutlined />}
            loading={isLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={4}>
        <Card>
          <Statistic
            title="Rata-rata Skor"
            value={data?.average_score || 0}
            precision={1}
            prefix={<StarOutlined />}
            suffix="%"
            loading={isLoading}
          />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={4}>
        <Card>
          <Statistic
            title="Hari Ini"
            value={data?.today_analyses || 0}
            prefix={<CalendarOutlined />}
            loading={isLoading}
          />
        </Card>
      </Col>
    </Row>
  );
}
