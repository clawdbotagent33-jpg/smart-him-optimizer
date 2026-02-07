/**
 * 입원 관리 페이지
 */
import React, { useState } from 'react';
import {
  Table,
  Button,
  Input,
  Space,
  Modal,
  Upload,
  message,
  Tag,
  Drawer,
  Descriptions,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { admissionsApi, predictionsApi, Admission, type CsvUploadResponse } from '../services/api';
import PredictionResultCard from '../components/PredictionResultCard';
import type { UploadProps } from 'antd';

const { Search } = Input;

const AdmissionsPage: React.FC = () => {
  const [searchText, setSearchText] = useState('');
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [predictionDrawerOpen, setPredictionDrawerOpen] = useState(false);
  const [selectedAdmission, setSelectedAdmission] = useState<Admission | null>(null);
  const [predictionResult, setPredictionResult] = useState<any>(null);

  const queryClient = useQueryClient();

  const { data: admissions, isLoading } = useQuery({
    queryKey: ['admissions'],
    queryFn: () => admissionsApi.list(),
  });

  const uploadMutation = useMutation({
    mutationFn: admissionsApi.uploadCsv,
    onSuccess: (data: CsvUploadResponse) => {
      message.success(`${data.rows_processed}건의 데이터를 처리했습니다`);
      setUploadModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ['admissions'] });
    },
    onError: (error: any) => {
      message.error(`업로드 실패: ${error.message}`);
    },
  });

  const predictMutation = useMutation({
    mutationFn: (data: any) => predictionsApi.predictComprehensive(data),
    onSuccess: (response) => {
      setPredictionResult(response);
    },
  });

  const handleUpload: UploadProps['customRequest'] = (options) => {
    const { file } = options;
    uploadMutation.mutate(file as File);
  };

  const handlePredict = (admission: Admission) => {
    setSelectedAdmission(admission);
    setPredictionResult(null);
    setPredictionDrawerOpen(true);

    predictMutation.mutate({
      principalDiagnosis: admission.principalDiagnosis,
      secondaryDiagnoses: admission.secondaryDiagnoses || [],
      procedures: admission.procedures || [],
      age: admission.lengthOfStay,
      department: admission.department,
      lengthOfStay: admission.lengthOfStay,
    });
  };

  const columns = [
    {
      title: '입원 ID',
      dataIndex: 'admissionId',
      key: 'admissionId',
      sorter: (a: Admission, b: Admission) =>
        a.admissionId.localeCompare(b.admissionId),
    },
    {
      title: '부서',
      dataIndex: 'department',
      key: 'department',
      width: 100,
    },
    {
      title: '주진단',
      dataIndex: 'principalDiagnosis',
      key: 'principalDiagnosis',
      width: 100,
    },
    {
      title: '그룹',
      dataIndex: 'drgGroup',
      key: 'drgGroup',
      width: 80,
      render: (group: string) => {
        const color = group === 'A' ? 'success' : group === 'B' ? 'processing' : 'warning';
        return <Tag color={color}>{group || '미분류'}</Tag>;
      },
    },
    {
      title: '가중치',
      dataIndex: 'drgWeight',
      key: 'drgWeight',
      width: 80,
      render: (value: number) => value?.toFixed(3) || '-',
    },
    {
      title: '재원일수',
      dataIndex: 'lengthOfStay',
      key: 'lengthOfStay',
      width: 80,
      render: (value: number) => value || '-',
    },
    {
      title: '입원일',
      dataIndex: 'admissionDate',
      key: 'admissionDate',
      render: (date: string) => new Date(date).toLocaleDateString('ko-KR'),
    },
    {
      title: '작업',
      key: 'actions',
      width: 150,
      render: (_: any, record: Admission) => (
        <Space>
          <Button
            size="small"
            icon={<FileTextOutlined />}
            onClick={() => handlePredict(record)}
          >
            예측
          </Button>
        </Space>
      ),
    },
  ];

  const filteredAdmissions = admissions?.filter((item: Admission) =>
    item.admissionId.toLowerCase().includes(searchText.toLowerCase()) ||
    item.principalDiagnosis?.toLowerCase().includes(searchText.toLowerCase()) ||
    item.department?.toLowerCase().includes(searchText.toLowerCase())
  ) || [];

  const isPending = predictMutation.status === 'pending';
  const uploadPending = uploadMutation.status === 'pending';

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 16,
        }}
      >
        <Search
          placeholder="입원 ID, 진단, 부서 검색..."
          allowClear
          style={{ width: 300 }}
          onChange={(e) => setSearchText(e.target.value)}
        />
        <Space>
          <Button
            type="primary"
            icon={<UploadOutlined />}
            onClick={() => setUploadModalOpen(true)}
          >
            CSV 업로드
          </Button>
        </Space>
      </div>

      <Table
        columns={columns}
        dataSource={filteredAdmissions}
        loading={isLoading}
        rowKey="id"
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
        }}
        pagination={{ pageSize: 20 }}
      />

      {/* CSV 업로드 모달 */}
      <Modal
        title="EMR CSV 데이터 업로드"
        open={uploadModalOpen}
        onCancel={() => setUploadModalOpen(false)}
        footer={null}
      >
        <Upload.Dragger
          accept=".csv"
          multiple={false}
          customRequest={handleUpload}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">CSV 파일을 이곳에 드래그하거나 클릭하여 업로드</p>
          <p className="ant-upload-hint">
            환자별 입원 데이터가 포함된 CSV 파일을 업로드해주세요
          </p>
        </Upload.Dragger>
      </Modal>

      {/* 예측 결과 서랍 */}
      <Drawer
        title={`예측 결과: ${selectedAdmission?.admissionId || ''}`}
        open={predictionDrawerOpen}
        onClose={() => setPredictionDrawerOpen(false)}
        width={600}
      >
        {selectedAdmission && (
          <Descriptions column={1} bordered size="small" style={{ marginBottom: 16 }}>
            <Descriptions.Item label="주진단">{selectedAdmission.principalDiagnosis}</Descriptions.Item>
            <Descriptions.Item label="부진단">
              {selectedAdmission.secondaryDiagnoses?.join(', ') || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="처치">
              {selectedAdmission.procedures?.join(', ') || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="현재 그룹">
              <Tag color={selectedAdmission.drgGroup === 'A' ? 'success' : 'default'}>
                {selectedAdmission.drgGroup || '미분류'}그룹
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}

        {isPending ? (
          <div style={{ textAlign: 'center', padding: 40 }}>AI 예측 중...</div>
        ) : predictionResult ? (
          <PredictionResultCard result={predictionResult} />
        ) : null}
      </Drawer>
    </div>
  );
};

export default AdmissionsPage;
