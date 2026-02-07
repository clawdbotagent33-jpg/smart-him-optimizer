/**
 * 대시보드 페이지
 */
import React, { useState, useRef } from 'react';
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
import UserOnboarding from '../components/UserOnboarding';
import NotificationBanner from '../components/NotificationBanner';
import { ContextHelp } from '../components/TooltipWrapper';
import { dashboardApi } from '../services/api';
import dayjs from 'dayjs';

const { Title } = Typography;

const DashboardPage: React.FC = () => {
  const [department, setDepartment] = useState<string | undefined>();
  const [days, setDays] = useState(30);

  // 온보딩 투어를 위한 ref들
  const departmentSelectRef = useRef<HTMLDivElement>(null);
  const daysSelectRef = useRef<HTMLDivElement>(null);
  const metricsRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<HTMLDivElement>(null);

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
      title: (
        <span>
          진단코드
          <ContextHelp
            content="ICD-10 진단코드를 기준으로 상위 10개 진단을 표시합니다."
          />
        </span>
      ),
      dataIndex: 'code',
      key: 'code',
    },
    {
      title: '건수',
      dataIndex: 'count',
      key: 'count',
    },
    {
      title: (
        <span>
          평균 가중치
          <ContextHelp
            content="진단별 조정 가중치(CMW)의 평균값입니다. 높을수록 중증도가 높음을 의미합니다."
          />
        </span>
      ),
      dataIndex: 'avg_weight',
      key: 'avg_weight',
      render: (value: number) => value.toFixed(3),
    },
  ];

  // 온보딩 투어 스텝 정의
  const tourSteps = [
    {
      selector: () => departmentSelectRef.current,
      title: '부서 필터',
      description: '특정 부서의 데이터만 보고 싶다면 부서를 선택하세요. 전체 데이터를 보려면 선택하지 않아도 됩니다.',
      placement: 'bottom' as const,
    },
    {
      selector: () => daysSelectRef.current,
      title: '기간 선택',
      description: '7일, 30일, 90일 중 원하는 기간을 선택하여 데이터를 확인할 수 있습니다.',
      placement: 'bottom' as const,
    },
    {
      selector: () => metricsRef.current,
      title: '주요 지표',
      description: '총 입원건수, 평균 CMI, A그룹 비율, 삭감율을 한눈에 확인할 수 있습니다.',
      placement: 'top' as const,
    },
    {
      selector: () => chartRef.current,
      title: '그룹별 분포 및 추이',
      description: '환자군 그룹(A/B/C)의 분포와 일별 추이를 시각화하여 보여줍니다.',
      placement: 'top' as const,
    },
  ];

  return (
    <div>
      {/* 환영 배너 - 첫 방문시 표시 */}
      <NotificationBanner
        type="info"
        message="HIM 옵티마이저에 오신 것을 환영합니다!"
        description="오른쪽 하단의 '가이드 보기' 버튼을 클릭하면 각 기능에 대한 안내를 받을 수 있습니다."
        showOnce
        storageKey="dashboard-welcome"
        action={
          <a href="#" onClick={(e) => { e.preventDefault(); window.open('/docs/user-guide', '_blank'); }}>
            사용자 가이드 보기
          </a>
        }
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={4}>
          대시보드
          <ContextHelp content="환자군 분류 및 입원 건수, 삭감율 등 주요 지표를 한눈에 확인할 수 있는 메인 화면입니다." />
        </Title>
        <Space>
          <div ref={departmentSelectRef}>
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
          </div>
          <div ref={daysSelectRef}>
            <Select
              defaultValue={30}
              style={{ width: 100 }}
              onChange={(value) => setDays(value)}
            >
              <Select.Option value={7}>7일</Select.Option>
              <Select.Option value={30}>30일</Select.Option>
              <Select.Option value={90}>90일</Select.Option>
            </Select>
          </div>
        </Space>
      </div>

      <Spin spinning={isLoading}>
        {/* 주요 지표 */}
        <Row gutter={16} style={{ marginBottom: 24 }} ref={metricsRef}>
          <Col span={6}>
            <DashboardCard
              title="총 입원건수"
              value={metrics?.totalAdmissions || 0}
              suffix="건"
            />
          </Col>
          <Col span={6}>
            <DashboardCard
              title={
                <span>
                  평균 CMI
                  <ContextHelp content="Case Mix Index로, 환자군의 중증도를 나타내는 지표입니다. 높을수록 중증 환자가 많음을 의미합니다." />
                </span>
              }
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
        <Row gutter={16} style={{ marginBottom: 24 }} ref={chartRef}>
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

      {/* 온보딩 투어 */}
      <UserOnboarding
        steps={tourSteps}
        storageKey="dashboard-tour-completed"
      />
    </div>
  );
};

export default DashboardPage;
