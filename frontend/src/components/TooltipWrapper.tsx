/**
 * 툴팱 래퍼 컴포넌트
 * 사용자 친화적 툴팁을 제공하는 재사용 가능 컴포넌트
 */
import React, { useState } from 'react';
import { Tooltip, Button } from 'antd';
import { InfoCircleOutlined, CloseOutlined } from '@ant-design/icons';

export interface TooltipWrapperProps {
  /**
   * 툴팁을 표시할 자식 요소
   */
  children: React.ReactElement;
  /**
   * 툴팁 제목
   */
  title?: string;
  /**
   * 툴팁 내용
   */
  content: string | React.ReactNode;
  /**
   * 툴팁 위치
   */
  placement?: 'top' | 'bottom' | 'left' | 'right' | 'topLeft' | 'topRight' | 'bottomLeft' | 'bottomRight';
  /**
   * 아이콘만 표시할지 여부
   */
  iconOnly?: boolean;
  /**
   * 한 번만 보고 다시는 보지 않을지 여부 (localStorage 사용)
   */
  showOnce?: boolean;
  /**
   * showOnce가 true일 때 사용할 고유 키
   */
  storageKey?: string;
}

const TooltipWrapper: React.FC<TooltipWrapperProps> = ({
  children,
  title,
  content,
  placement = 'top',
  iconOnly = false,
  showOnce = false,
  storageKey,
}) => {
  const [visible, setVisible] = useState(false);

  // showOnce가 true인 경우 localStorage 확인
  useEffect(() => {
    if (showOnce && storageKey) {
      const hasSeen = localStorage.getItem(`tooltip-seen-${storageKey}`);
      if (!hasSeen) {
        // 처음 진입 시 툴팁 자동 표시
        const timer = setTimeout(() => setVisible(true), 500);
        return () => clearTimeout(timer);
      }
    }
  }, [showOnce, storageKey]);

  const handleVisibleChange = (newVisible: boolean) => {
    setVisible(newVisible);
    if (!newVisible && showOnce && storageKey) {
      localStorage.setItem(`tooltip-seen-${storageKey}`, 'true');
    }
  };

  const tooltipContent = (
    <div>
      {title && <div style={{ fontWeight: 'bold', marginBottom: 4 }}>{title}</div>}
      <div>{content}</div>
    </div>
  );

  if (iconOnly) {
    return (
      <Tooltip
        placement={placement}
        title={tooltipContent}
        visible={visible}
        onVisibleChange={handleVisibleChange}
      >
        <InfoCircleOutlined style={{ margin: '0 8px', color: '#1890ff', cursor: 'help' }} />
      </Tooltip>
    );
  }

  return (
    <Tooltip
      placement={placement}
      title={tooltipContent}
      visible={visible}
      onVisibleChange={handleVisibleChange}
    >
      {children}
    </Tooltip>
  );
};

/**
 * 문맥 도움말 컴포넌트
 * 라벨 옆에 정보 아이콘을 표시하여 상세 설명 제공
 */
export const ContextHelp: React.FC<{
  title?: string;
  content: string | React.ReactNode;
  placement?: TooltipWrapperProps['placement'];
}> = ({ title, content, placement = 'right' }) => {
  return (
    <Tooltip placement={placement} title={title ? <><strong>{title}</strong><br />{content}</> : content}>
      <InfoCircleOutlined style={{ marginLeft: 4, color: '#8c8c8c', cursor: 'help' }} />
    </Tooltip>
  );
};

export default TooltipWrapper;
