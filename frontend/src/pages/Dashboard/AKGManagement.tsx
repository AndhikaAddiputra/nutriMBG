import { useState, useMemo } from 'react';
import { Table, Button, Modal, Form, InputNumber, Select, message, Tooltip, Tabs, Card } from 'antd';
import { EditOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { getAKGList, updateAKG } from '../../api/admin/akg';
import {
  AKGOut,
  AKGUpdate,
  EDUCATION_LEVELS,
  NUTRIENT_CODES,
  NUTRIENT_LABELS,
} from '../../types/admin';

const LEVEL_LABELS: Record<string, string> = {
  SD_1_3: 'SD Kelas 1–3',
  SD_4_6: 'SD Kelas 4–6',
  SMP: 'SMP',
  SMA: 'SMA',
};

interface AKGRow {
  key: string;
  education_level: string;
  [nutrient: string]: number | string;
}

export default function AKGManagement() {
  const queryClient = useQueryClient();
  const [activeLevel, setActiveLevel] = useState<string>('SMP');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAKG, setEditingAKG] = useState<AKGOut | null>(null);
  const [editForm] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['admin-akg'],
    queryFn: () => getAKGList(),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: AKGUpdate }) => updateAKG(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-akg'] }); message.success('AKG berhasil diperbarui'); },
    onError: () => message.error('Gagal memperbarui AKG'),
  });

  const openEdit = (akg: AKGOut) => {
    setEditingAKG(akg);
    editForm.setFieldsValue({ target_value: akg.target_value, unit: akg.unit });
    setModalOpen(true);
  };

  const handleEditSubmit = async () => {
    const values = await editForm.validateFields();
    if (editingAKG) {
      updateMutation.mutate({ id: editingAKG.id, data: values });
    }
    setModalOpen(false);
  };

  const allData = useMemo(() => {
    if (!data) return [];

    return EDUCATION_LEVELS.map((level) => {
      const row: AKGRow = { key: level, education_level: level };
      const levelData = data.filter((a) => a.education_level === level);
      NUTRIENT_CODES.forEach((code) => {
        const found = levelData.find((a) => a.nutrient_code === code);
        row[code] = found?.target_value ?? 0;
      });
      return row;
    });
  }, [data]);

  const akgByLevel = useMemo(() => {
    if (!data) return [];
    return data.filter((a) => a.education_level === activeLevel);
  }, [data, activeLevel]);

  const pivotColumns: ColumnsType<AKGRow> = [
    { title: 'Jenjang', dataIndex: 'education_label', key: 'education_label' },
    ...NUTRIENT_CODES.map((code) => ({
      title: NUTRIENT_LABELS[code],
      dataIndex: code,
      key: code,
      render: (v: number) => v.toFixed?.(v % 1 === 0 ? 0 : 1) ?? v,
    })),
  ];

  const tableColumns: ColumnsType<AKGOut> = [
    { title: 'Nutrisi', dataIndex: 'nutrient_code', key: 'nutrient_code',
      render: (code: string) => NUTRIENT_LABELS[code] || code,
    },
    { title: 'Target', dataIndex: 'target_value', key: 'target_value',
      render: (v: number) => v.toFixed(1),
    },
    { title: 'Satuan', dataIndex: 'unit', key: 'unit' },
    {
      title: 'Aksi',
      key: 'action',
      width: 80,
      render: (_: unknown, record: AKGOut) => (
        <Tooltip title="Edit">
          <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)} />
        </Tooltip>
      ),
    },
  ];

  const tabItems = EDUCATION_LEVELS.map((level) => ({
    key: level,
    label: LEVEL_LABELS[level],
  }));

  return (
    <div>
      <div style={{ marginBottom: 16 }}>
        <h3>Manajemen Angka Kecukupan Gizi (AKG)</h3>
      </div>

      {/* Pivot table by education level */}
      <Card title="Ringkasan per Jenjang" style={{ marginBottom: 24 }}>
        <Table
          columns={pivotColumns}
          dataSource={allData.map((r) => ({ ...r, education_label: LEVEL_LABELS[r.education_level] }))}
          rowKey="key"
          pagination={false}
          loading={isLoading}
          scroll={{ x: 700 }}
        />
      </Card>

      {/* Detail per level */}
      <Card
        title="Detail AKG"
        extra={
          <Tabs activeKey={activeLevel} onChange={setActiveLevel} items={tabItems} />
        }
      >
        <Table
          columns={tableColumns}
          dataSource={akgByLevel}
          rowKey="id"
          pagination={false}
          loading={isLoading}
        />
      </Card>

      <Modal
        title="Edit AKG"
        open={modalOpen}
        onOk={handleEditSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={updateMutation.isPending}
      >
        <Form form={editForm} layout="vertical">
          <Form.Item name="target_value" label="Nilai Target" rules={[{ required: true, message: 'Wajib diisi' }]}>
            <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="unit" label="Satuan">
            <Select options={[
              { label: 'gram (g)', value: 'g' },
              { label: 'miligram (mg)', value: 'mg' },
              { label: 'microgram (mcg)', value: 'mcg' },
              { label: 'kilokalori (kcal)', value: 'kcal' },
            ]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
