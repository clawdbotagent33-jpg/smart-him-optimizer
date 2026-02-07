/**
 * 대시보드 페이지
 */
import React, { useState } from 'react';
import {
  Row,
  Col,
  Select,
  Spin,
  Card,
  Table,
  Typography,
  Space,
} from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useQuery } from '@tanstack/react-query';
import DashboardCard from '../components/DashboardCard';
import GroupDistributionChart from '../components/GroupDistributionChart';
import { dashboardApi } from '../services/api';
import dayjs from 'dayjs';

const { Title } = Typography;

const DashboardPage: React.FC = () => {
  const [department, setDepartment] = useState<string | undefined>();
  const [days, setDays] = useState(30);

  const { data: metrics, isLoading } = useQuery({
    queryKey: ['dashboard', 'summary', department, days],
    queryFn: () => dashboardApi.getSummary(department, days),
  });

  const { data: groupDistribution } = useQuery({
    queryKey: ['dashboard', 'group-distribution', department, days],
    queryFn: () => dashboardApi.getGroupDistribution(department, days),
  });

  const { data: topDiagnoses } = useQuery({
    queryKey: ['dashboard', 'top-diagnoses', days],
    queryFn: () => dashboardApi.getTopDiagnoses(10, days),
  });

  const { data: denialAnalytics } = useQuery({
    queryKey: ['dashboard', 'denials', days],
    queryFn: () => dashboardApi.getDenialAnalytics(undefined, undefined),
  });

  const groupChartData = groupDistribution?.dates?.map((date: string, index: number) => ({
    date: dayjs(date).format('MM/DD'),
    A: groupDistribution.series.A[index],
    B: groupDistribution.series.B[index],
    C: groupDistribution.series.C[index],
  }));

  const diagnosesColumns = [
    {
      title: '진단코드',
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '건수',
      dataIndex: 'count',
      key: 'count',
    },
    {
      title: '평균 가중치',
      dataIndex: 'avg_weight',
      key: 'avg_weight',
      render: (value: number) => value.toFixed(3),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>대시보드</Title>
        <Space>
          <Select
            placeholder="부서 선택"
            style={{ width: 150 }}
            allowClear
            onChange={setDepartment}
          >
            <Select.Option value="내과">내과</Select.Option>
            <Select.Option value="외과">외과</Select.Option>
            <Select.Option value="정형외과">정형외과</Select.Option>
            <Select.Option value="신경과">신경과</Select.Option>
          </Select>
          <Select
            defaultValue={30}
            style={{ width: 100 }}
            onChange={(value) => setDays(value)}
          >
            <Select.Option value={7}>7일</Select.Option>
            <Select.Option value={30}>30일</Select.Option>
            <Select.Option value={90}>90일</Select.Option>
          </Select>
        </Space>
      </div>

      <Spin spinning={isLoading}>
        {/* 주요 지표 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <DashboardCard
              title="총 입원건수"
              value={metrics?.totalAdmissions || 0}
              suffix="건"
            />
          </Col>
          <Col span={6}>
            <DashboardCard
              title="평균 CMI"
              value={metrics?.averageCmi?.toFixed(3) || '0.000'}
              color="#52c41a"
            />
          </Col>
          <Col span={6}>
            <DashboardCard
              title="A그룹 비율"
              value={metrics?.aGroupRatio || 0}
              suffix="%"
              color="#1890ff"
            />
          </Col>
          <Col span={6}>
            <DashboardCard
              title="삭감율"
              value={metrics?.denialRate?.toFixed(1) || '0.0'}
              suffix="%"
              color="#cf1322"
            />
          </Col>
        </Row>

        {/* 차트 영역 */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={12}>
            <Card title="그룹별 분포">
              <GroupDistributionChart
                data={metrics?.groupDistribution || {}}
              />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="일별 그룹 추이">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={groupChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="A" fill="#52c41a" name="A그룹" />
                  <Bar dataKey="B" fill="#1890ff" name="B그룹" />
                  <Bar dataKey="C" fill="#faad14" name="C그룹" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </Col>
        </Row>

        {/* 상위 진단 */}
        <Row gutter={16}>
          <Col span={24}>
            <Card title="상위 진단별 통계">
              <Table
                columns={diagnosesColumns}
                dataSource={topDiagnoses?.diagnoses || []}
                rowKey="code"
                size="small"
                pagination={false}
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default DashboardPage;
