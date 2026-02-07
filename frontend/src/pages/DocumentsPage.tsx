/**
 * 문서 관리 페이지
 */
import React, { useState } from 'react';
import {
  Button,
  Upload,
  Modal,
  Input,
  Space,
  Card,
  Tag,
  List,
  Typography,
  Divider,
  Row,
  Col,
  Statistic,
} from 'antd';
import {
  UploadOutlined,
  FileTextOutlined,
  SearchOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../services/api';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

const DocumentsPage: React.FC = () => {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [ragModalOpen, setRagModalOpen] = useState(false);
  const [question, setQuestion] = useState('');
  const [ragAnswer, setRagAnswer] = useState<any>(null);
  const [fileList, setFileList] = useState<any[]>([]);

  const queryClient = useQueryClient();

  const { data: stats } = useQuery({
    queryKey: ['documents', 'stats'],
    queryFn: documentsApi.getStats,
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, docType }: { file: File; docType: string }) =>
      documentsApi.upload(file, docType),
    onSuccess: () => {
      setUploadModalOpen(false);
      setFileList([]);
      queryClient.invalidateQueries({ queryKey: ['documents', 'stats'] });
    },
  });

  const ragQueryMutation = useMutation({
    mutationFn: (q: string) => documentsApi.query(q),
    onSuccess: (data) => {
      setRagAnswer(data);
    },
  });

  const handleUpload = () => {
    if (fileList.length === 0) return;

    const file = fileList[0].originFileObj;
    const docType = (document.getElementById('docTypeSelect') as HTMLSelectElement)?.value;

    uploadMutation.mutate({ file, docType });
  };

  const handleRagQuery = () => {
    if (!question.trim()) return;

    setRagAnswer(null);
    ragQueryMutation.mutate(question);
  };

  const docTypes = [
    { value: 'k_drg_guideline', label: 'K-DRG 가이드라인' },
    { value: 'kcd9_guideline', label: 'KCD-9 규정' },
    { value: 'manual_memo', label: '수기 메모' },
    { value: 'guideline', label: '업무 지침' },
    { value: 'performance_metric', label: '평가 지표' },
  ];

  const uploadPending = uploadMutation.status === 'pending';
  const ragPending = ragQueryMutation.status === 'pending';

  return (
    <div>
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <Title level={4} style={{ margin: 0 }}>
          문서 관리
        </Title>
        <Space>
          <Button icon={<SearchOutlined />} onClick={() => setRagModalOpen(true)}>
            RAG 질의
          </Button>
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModalOpen(true)}>
            문서 업로드
          </Button>
        </Space>
      </div>

      {/* 통계 카드 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="등록 문서 수"
              value={stats?.document_count || 0}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="시스템 상태"
              value={stats?.status === 'active' ? '정상' : '오류'}
              valueStyle={{ color: stats?.status === 'active' ? '#52c41a' : '#cf1322' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="벡터 청크 수"
              value={stats?.chunk_count || 0}
            />
          </Card>
        </Col>
      </Row>

      {/* 문서 유형별 가이드 */}
      <Card title="RAG 학습 데이터 관리">
        <List
          grid={{ gutter: 16, column: 2 }}
          dataSource={docTypes}
          renderItem={(item) => (
            <List.Item>
              <Card size="small" title={item.label}>
                <Text type="secondary">
                  {item.value === 'k_drg_guideline' && 'K-DRG v4.7 분류 기준 및 코딩 가이드'}
                  {item.value === 'kcd9_guideline' && 'KCD-9 질병 분류 및 코딩 규정'}
                  {item.value === 'manual_memo' && '관리사 수기 메모 및 노하우'}
                  {item.value === 'guideline' && '원내 업무 지침 및 프로세스'}
                  {item.value === 'performance_metric' && '성과 지표 및 평가 기준'}
                </Text>
              </Card>
            </List.Item>
          )}
        />
      </Card>

      {/* 문서 업로드 모달 */}
      <Modal
        title="문서 업로드"
        open={uploadModalOpen}
        onCancel={() => setUploadModalOpen(false)}
        onOk={handleUpload}
        confirmLoading={uploadPending}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <div>
            <Text>문서 유형:</Text>
            <select id="docTypeSelect" style={{ width: '100%', marginTop: 8, padding: 8 }}>
              {docTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>
          <Upload.Dragger
            fileList={fileList}
            onChange={({ fileList }) => setFileList(fileList)}
            beforeUpload={() => false}
            accept=".pdf,.docx,.txt,.png,.jpg"
            maxCount={1}
          >
            <p className="ant-upload-drag-icon">
              <UploadOutlined />
            </p>
            <p className="ant-upload-text">클릭하거나 파일을 드래그하세요</p>
            <p className="ant-upload-hint">PDF, DOCX, TXT, 이미지 파일 지원</p>
          </Upload.Dragger>
        </Space>
      </Modal>

      {/* RAG 질의 모달 */}
      <Modal
        title="RAG 기반 지식 검색"
        open={ragModalOpen}
        onCancel={() => setRagModalOpen(false)}
        footer={null}
        width={700}
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <TextArea
            rows={3}
            placeholder="K-DRG, KCD-9, 코딩 규정 등에 대해 질문해주세요"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
          />
          <Button
            type="primary"
            icon={<RobotOutlined />}
            onClick={handleRagQuery}
            loading={ragPending}
            block
          >
            질의하기
          </Button>

          {ragAnswer && (
            <Card title="답변" size="small">
              <Paragraph>{ragAnswer.answer}</Paragraph>
              <Divider />
              <Text strong>출처:</Text>
              <List
                size="small"
                dataSource={ragAnswer.sources}
                renderItem={(source: any) => (
                  <List.Item>
                    <Tag color="blue">{source.doc_type || '문서'}</Tag>
                    <Text>{source.source}</Text>
                  </List.Item>
                )}
              />
            </Card>
          )}
        </Space>
      </Modal>
    </div>
  );
};

export default DocumentsPage;
