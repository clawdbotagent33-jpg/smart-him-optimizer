/**
 * 그룹 분포 차트 컴포넌트
 */
import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

interface GroupDistributionChartProps {
  data: {
    A?: number;
    B?: number;
    C?: number;
  };
  loading?: boolean;
}

const COLORS = {
  A: '#52c41a',  // 녹색 - 전문질병군
  B: '#1890ff',  // 파란색 - 일반질병군
  C: '#faad14',  // 주황색 - 심층질병군
};

const GROUP_NAMES = {
  A: 'A그룹 (전문)',
  B: 'B그룹 (일반)',
  C: 'C그룹 (심층)',
};

const GroupDistributionChart: React.FC<GroupDistributionChartProps> = ({ data, loading }) => {
  const chartData = Object.entries(data)
    .filter(([_, value]) => value > 0)
    .map(([key, value]) => ({
      name: GROUP_NAMES[key as keyof typeof GROUP_NAMES],
      value: value as number,
      group: key,
    }));

  if (loading || chartData.length === 0) {
    return (
      <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        데이터가 없습니다
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
        >
          {chartData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={COLORS[entry.group as keyof typeof COLORS]}
            />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default GroupDistributionChart;
