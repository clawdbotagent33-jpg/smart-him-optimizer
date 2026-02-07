/**
 * 사용자 온보딩 가이드 컴포넌트
 * 첫 방문시 각 페이지의 주요 기능을 안내
 */
import React, { useState, useEffect } from 'react';
import { Tour, Button, Typography } from 'antd';
import {
  QuestionCircleOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

export interface TourStep {
  selector: () => HTMLElement | null;
  title: string;
  description: string;
  placement?: 'top' | 'bottom' | 'left' | 'right';
}

interface UserOnboardingProps {
  steps: TourStep[];
  storageKey: string;
  onComplete?: () => void;
}

const UserOnboarding: React.FC<UserOnboardingProps> = ({
  steps,
  storageKey,
  onComplete,
}) => {
  const [current, setCurrent] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    // 로컬 스토리지에서 가이드 완료 여부 확인
    const hasCompleted = localStorage.getItem(storageKey);
    if (!hasCompleted) {
      // 약간의 지연 후 가이드 시작 (DOM이 렌더링될 때까지 대기)
      const timer = setTimeout(() => {
        setOpen(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [storageKey]);

  const handleComplete = () => {
    localStorage.setItem(storageKey, 'completed');
    setOpen(false);
    onComplete?.();
  };

  const tourSteps = steps.map((step) => ({
    target: step.selector,
    title: step.title,
    description: step.description,
    placement: step.placement || 'top',
  }));

  return (
    <>
      {/* 가이드 재시작 버튼 - 항상 표시 */}
      <Button
        type="text"
        icon={<QuestionCircleOutlined />}
        onClick={() => setOpen(true)}
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          zIndex: 1000,
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        }}
      >
        가이드 보기
      </Button>

      <Tour
        open={open}
        onClose={handleComplete}
        current={current}
        onChange={setCurrent}
        steps={tourSteps}
        indicatorsRender={(current, total) => (
          <Text type="secondary">
            {current + 1} / {total}
          </Text>
        )}
        type="primary"
      />
    </>
  );
};

export default UserOnboarding;
