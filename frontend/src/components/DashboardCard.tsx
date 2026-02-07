/**
 * 대시보드 카드 컴포넌트
 */
import React from 'react';
import { Card, Statistic } from 'antd';

interface DashboardCardProps {
  title: string | React.ReactNode;
  value: number | string;
  suffix?: string;
  prefix?: React.ReactNode;
  loading?: boolean;
  color?: string;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  value,
  suffix,
  prefix,
  loading = false,
  color = '#1890ff',
}) => {
  return (
    <Card loading={loading} bordered={false} className="dashboard-card">
      <Statistic
        title={title}
        value={value}
        suffix={suffix}
        prefix={prefix}
        valueStyle={{ color }}
      />
    </Card>
  );
};

export default DashboardCard;
