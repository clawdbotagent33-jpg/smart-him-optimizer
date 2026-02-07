/**
 * 예측 결과 카드 컴포넌트
 */
import React from 'react';
import { Card, Alert, Tag, Progress, List, Typography } from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { PredictionResponse } from '../services/api';

const { Text, Paragraph } = Typography;

interface PredictionResultCardProps {
  result: PredictionResponse;
  loading?: boolean;
}

const PredictionResultCard: React.FC<PredictionResultCardProps> = ({ result, loading }) => {
  const { groupPrediction, denialRisk, recommendations } = result;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'HIGH':
        return 'error';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'success';
      default:
        return 'default';
    }
  };

  const getGroupColor = (group: string) => {
    switch (group) {
      case 'A':
        return 'success';
      case 'B':
        return 'processing';
      case 'C':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Card loading={loading} title="AI 예측 결과">
      {/* 예측 그룹 */}
      <div style={{ marginBottom: 16 }}>
        <Text strong>예측 K-DRG 그룹: </Text>
        <Tag color={getGroupColor(groupPrediction.predictedGroup)} style={{ fontSize: 16 }}>
          {groupPrediction.predictedGroup}그룹
        </Tag>
        <Text type="secondary"> (신뢰도: {(groupPrediction.confidence * 100).toFixed(1)}%)</Text>
      </div>

      {/* A그룹 전환 가능성 */}
      {groupPrediction.predictedGroup !== 'A' && (
        <div style={{ marginBottom: 16 }}>
          <Text strong>A그룹 전환 가능성: </Text>
          <Progress
            percent={Math.round(groupPrediction.aGroupProbability * 100)}
            status={groupPrediction.canUpgrade ? 'active' : 'exception'}
          />
        </div>
      )}

      {/* 삭감 위험도 */}
      <div style={{ marginBottom: 16 }}>
        <Alert
          message={`청구 삭감 위험도: ${denialRisk.riskLevel}`}
          description={
            <div>
              <Text>위험 확률: {(denialRisk.denialProbability * 100).toFixed(1)}%</Text>
              {denialRisk.riskFactors.length > 0 && (
                <List
                  size="small"
                  header="위험 요인:"
                  dataSource={denialRisk.riskFactors}
                  renderItem={(item) => <List.Item>{item}</List.Item>}
                />
              )}
            </div>
          }
          type={getRiskColor(denialRisk.riskLevel) as 'error' | 'warning' | 'success' | 'info'}
          showIcon
        />
      </div>

      {/* 권고사항 */}
      {recommendations.length > 0 && (
        <div>
          <Text strong>권고사항:</Text>
          <List
            dataSource={recommendations}
            renderItem={(item) => (
              <List.Item>
                {item.includes('가능성') ? (
                  <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                ) : (
                  <WarningOutlined style={{ color: '#faad14', marginRight: 8 }} />
                )}
                {item}
              </List.Item>
            )}
          />
        </div>
      )}

      {/* 업그레이드 제안 */}
      {result.upgradeSuggestions && result.upgradeSuggestions.length > 0 && (
        <div style={{ marginTop: 16, padding: 12, background: '#f0f2f5', borderRadius: 8 }}>
          <Text strong>A그룹 전환 제안:</Text>
          <List
            size="small"
            style={{ marginTop: 8 }}
            dataSource={result.upgradeSuggestions}
            renderItem={(item) => (
              <List.Item>
                <Tag color={item.priority === 'high' ? 'red' : item.priority === 'medium' ? 'orange' : 'blue'}>
                  {item.priority}
                </Tag>
                {item.description}
              </List.Item>
            )}
          />
        </div>
      )}
    </Card>
  );
};

export default PredictionResultCard;
