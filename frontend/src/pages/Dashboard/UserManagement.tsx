import { useState } from 'react';
import { Table, Button, Space, Tag, Input, Modal, Form, Select, message, Tooltip } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ColumnsType } from 'antd/es/table';
import { getAdminUsers, createAdminUser, updateAdminUser, deleteAdminUser } from '../../api/admin/users';
import { AdminUser, AdminUserCreate, AdminUserUpdate, EDUCATION_LEVELS } from '../../types/admin';

export default function UserManagement() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['admin-users', page, search],
    queryFn: () => getAdminUsers(page, 20, search || undefined, true),
  });

  const createMutation = useMutation({
    mutationFn: createAdminUser,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-users'] }); message.success('Pengguna berhasil dibuat'); },
    onError: () => message.error('Gagal membuat pengguna'),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: AdminUserUpdate }) => updateAdminUser(id, data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-users'] }); message.success('Pengguna berhasil diperbarui'); },
    onError: () => message.error('Gagal memperbarui pengguna'),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAdminUser,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['admin-users'] }); message.success('Pengguna berhasil dihapus'); },
    onError: () => message.error('Gagal menghapus pengguna'),
  });

  const openCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (user: AdminUser) => {
    setEditingUser(user);
    form.setFieldsValue(user);
    setModalOpen(true);
  };

  const handleDelete = (id: number) => {
    Modal.confirm({
      title: 'Hapus pengguna?',
      content: 'Pengguna akan dinonaktifkan (soft-delete).',
      okText: 'Hapus',
      okType: 'danger',
      cancelText: 'Batal',
      onOk: () => deleteMutation.mutate(id),
    });
  };

  const handleSubmit = async () => {
    const values = await form.validateFields();
    if (editingUser) {
      updateMutation.mutate({ id: editingUser.id, data: values });
    } else {
      createMutation.mutate(values as AdminUserCreate);
    }
    setModalOpen(false);
  };

  const columns: ColumnsType<AdminUser> = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: 'Nama', dataIndex: 'full_name', key: 'full_name' },
    { title: 'Email', dataIndex: 'email', key: 'email' },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'blue' : 'green'}>
          {role === 'admin' ? 'ADMIN' : 'KOORDINATOR'}
        </Tag>
      ),
    },
    {
      title: 'Kabupaten',
      dataIndex: 'kabupaten',
      key: 'kabupaten',
      responsive: ['lg' as const],
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'error'}>{active ? 'Aktif' : 'Nonaktif'}</Tag>
      ),
    },
    {
      title: 'Aksi',
      key: 'action',
      width: 140,
      render: (_: unknown, record: AdminUser) => (
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
        <h3>Manajemen Pengguna</h3>
        <Space>
          <Input
            placeholder="Cari nama atau email..."
            prefix={<SearchOutlined />}
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            style={{ width: 220 }}
            allowClear
          />
          <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
            Tambah Pengguna
          </Button>
        </Space>
      </div>
      <Table
        columns={columns}
        dataSource={data?.items}
        rowKey="id"
        loading={isLoading || createMutation.isPending || updateMutation.isPending}
        pagination={{
          current: page,
          pageSize: 20,
          total: data?.total,
          onChange: setPage,
          showSizeChanger: false,
        }}
        scroll={{ x: 600 }}
      />
      <Modal
        title={editingUser ? 'Edit Pengguna' : 'Tambah Pengguna'}
        open={modalOpen}
        onOk={handleSubmit}
        onCancel={() => setModalOpen(false)}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={520}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="full_name" label="Nama Lengkap" rules={[{ required: true, message: 'Nama wajib diisi' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email', message: 'Email valid wajib diisi' }]}>
            <Input />
          </Form.Item>
          {!editingUser && (
            <Form.Item name="password" label="Password" rules={[{ required: true, message: 'Password wajib diisi' }]}>
              <Input.Password />
            </Form.Item>
          )}
          <Form.Item name="role" label="Role" rules={[{ required: true, message: 'Role wajib dipilih' }]}>
            <Select options={[
              { label: 'Koordinator', value: 'coordinator' },
              { label: 'Admin', value: 'admin' },
            ]} />
          </Form.Item>
          <Form.Item name="province" label="Provinsi">
            <Input />
          </Form.Item>
          <Form.Item name="kabupaten" label="Kabupaten/Kota">
            <Input />
          </Form.Item>
          <Form.Item name="default_education_level" label="Jenjang Pendidikan Default">
            <Select options={EDUCATION_LEVELS.map(l => ({ label: l.replace('_', ' '), value: l }))} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
