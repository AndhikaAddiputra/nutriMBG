import { Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import { useAdminStats } from '../../hooks/useAdminStats';
import { RecentAnalysisItem } from '../../types/admin';

const { Text } = Typography;

export default function RecentAnalysis() {
  const { data, isLoading } = useAdminStats();

  const analyses = data?.recent_analyses || [];

  const columns: ColumnsType<RecentAnalysisItem> = [
    {
      title: 'Tanggal',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('DD MMM YYYY, HH:mm'),
    },
    {
      title: 'Menu',
      dataIndex: 'menu_text',
      key: 'menu_text',
      ellipsis: true,
      render: (text: string) => (
        <Text ellipsis={{ tooltip: text }} style={{ maxWidth: 300 }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Jenjang',
      dataIndex: 'education_level',
      key: 'education_level',
      render: (level: string) => level.replace('_', ' '),
    },
    {
      title: 'Skor',
      dataIndex: 'score_total',
      key: 'score_total',
      sorter: (a: RecentAnalysisItem, b: RecentAnalysisItem) => a.score_total - b.score_total,
      render: (score: number) => {
        let color = 'success';
        if (score < 50) color = 'error';
        else if (score < 80) color = 'warning';
        return <Tag color={color}>{score.toFixed(1)}</Tag>;
      },
    },
    {
      title: 'User ID',
      dataIndex: 'user_id',
      key: 'user_id',
      width: 80,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h3>Analisa Terbaru</h3>
      </div>
      <Table
        columns={columns}
        dataSource={analyses}
        rowKey="id"
        loading={isLoading}
        pagination={{ pageSize: 10, showSizeChanger: false }}
        scroll={{ x: 700 }}
      />
    </div>
  );
}
