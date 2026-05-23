import { useState } from 'react';
import { Table, Button, Space, Input, Modal, Form, InputNumber, message, Tooltip } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { getAdminFoods, createFoodItem, updateFoodItem, deleteFoodItem } from '../../api/admin/foods';
import { FoodItemOut, FoodItemCreate, FoodItemUpdate } from '../../types/admin';

export default function FoodManagement() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingFood, setEditingFood] = useState<FoodItemOut | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['admin-foods', page, search],
    queryFn: () => getAdminFoods(page, 20, search || undefined),
  });

  const createMutation = useMutation({
    mutationFn: createFoodItem,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-foods'] }); message.success('Bahan berhasil ditambahkan'); },
    onError: () => message.error('Gagal menambahkan bahan'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: FoodItemUpdate }) => updateFoodItem(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-foods'] }); message.success('Bahan berhasil diperbarui'); },
    onError: () => message.error('Gagal memperbarui bahan'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteFoodItem,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-foods'] }); message.success('Bahan berhasil dihapus'); },
    onError: () => message.error('Gagal menghapus bahan'),
  });

  const openCreate = () => {
    setEditingFood(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (food: FoodItemOut) => {
    setEditingFood(food);
    form.setFieldsValue(food);
    setModalOpen(true);
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: 'Hapus bahan makanan?',
      content: 'Bahan akan dinonaktifkan (soft-delete).',
      okText: 'Hapus',
      okType: 'danger',
      cancelText: 'Batal',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingFood) {
      updateMutation.mutate({ id: editingFood.id, data: values });
    } else {
      createMutation.mutate(values as FoodItemCreate);
    }
    setModalOpen(false);
  };

  const columns: ColumnsType<FoodItemOut> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Nama Bahan', dataIndex: 'name', key: 'name', ellipsis: true },
    { title: 'Sumber', dataIndex: 'source', key: 'source', width: 80 },
    { title: 'Protein (g)', dataIndex: 'protein', key: 'protein', width: 100, render: (v: number) => v.toFixed(1) },
    { title: 'Karbo (g)', dataIndex: 'carbohydrate', key: 'carbohydrate', width: 100, render: (v: number) => v.toFixed(1) },
    { title: 'Lemak (g)', dataIndex: 'fat', key: 'fat', width: 100, render: (v: number) => v.toFixed(1) },
    { title: 'Serat (g)', dataIndex: 'fiber', key: 'fiber', width: 100, render: (v: number) => v.toFixed(1) },
    { title: 'Zat Besi (mg)', dataIndex: 'iron', key: 'iron', width: 110, render: (v: number) => v.toFixed(2) },
    { title: 'Vit A (mcg)', dataIndex: 'vitamin_a', key: 'vitamin_a', width: 110, render: (v: number) => v.toFixed(1) },
    {
      title: 'Aksi',
      key: 'action',
      width: 100,
      render: (_: unknown, record: FoodItemOut) => (
        <Space size="small">
          <Tooltip title="Edit">
            <Button type="link" icon={<EditOutlined />} onClick={() => openEdit(record)} />
          </Tooltip>
          <Tooltip title="Hapus">
            <Button type="link" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)} />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h3>Manajemen Bahan Makanan (TKPI)</h3>
        <Space>
          <Input
            placeholder="Cari bahan..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            style={{ width: 220 }}
            allowClear
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Tambah Bahan
          </Button>
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={data?.items}
        rowKey="id"
        loading={isLoading}
        pagination={{
          current: page,
          pageSize: 20,
          total: data?.total,
          onChange: setPage,
          showSizeChanger: false,
        }}
        scroll={{ x: 900 }}
      />
      <Modal
        title={editingFood ? 'Edit Bahan Makanan' : 'Tambah Bahan Makanan'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={520}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="Nama Bahan" rules={[{ required: true, message: 'Nama wajib diisi' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="source" label="Sumber">
            <Input placeholder="DKBM" />
          </Form.Item>
          <Form.Item name="protein" label="Protein (g)" rules={[{ required: true, message: 'Wajib diisi' }]}>
            <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="carbohydrate" label="Karbohidrat (g)" rules={[{ required: true, message: 'Wajib diisi' }]}>
            <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="fat" label="Lemak (g)" rules={[{ required: true, message: 'Wajib diisi' }]}>
            <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="fiber" label="Serat (g)" rules={[{ required: true, message: 'Wajib diisi' }]}>
            <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="iron" label="Zat Besi (mg)" rules={[{ required: true, message: 'Wajib diisi' }]}>
            <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="vitamin_a" label="Vitamin A (mcg)" rules={[{ required: true, message: 'Wajib diisi' }]}>
            <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
