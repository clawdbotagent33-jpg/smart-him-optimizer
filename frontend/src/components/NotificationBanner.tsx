/**
 * 알림 배너 컴포넌트
 * 중요 공지사항이나 시스템 메시지를 표시
 */
import React, { useState, useEffect } from 'react';
import { Alert, Button } from 'antd';
import { CloseOutlined } from '@ant-design/icons';

export interface NotificationBannerProps {
  /**
   * 배너 메시지 타입
   */
  type?: 'success' | 'info' | 'warning' | 'error';
  /**
   * 배너 제목
   */
  message?: string;
  /**
   * 배너 내용
   */
  description: string;
  /**
   * 닫기 버튼 표시 여부
   */
  closable?: boolean;
  /**
   * 한 번만 보고 닫은 후 다시 표시하지 않을지 여부
   */
  showOnce?: boolean;
  /**
   * showOnce가 true일 때 사용할 고유 키
   */
  storageKey?: string;
  /**
   * 배너 하단 액션 버튼
   */
  action?: React.ReactNode;
  /**
   * 자동으로 닫히는 시간 (밀리초), 0이면 자동 닫힘 없음
   */
  autoClose?: number;
}

const NotificationBanner: React.FC<NotificationBannerProps> = ({
  type = 'info',
  message,
  description,
  closable = true,
  showOnce = false,
  storageKey,
  action,
  autoClose = 0,
}) => {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    if (showOnce && storageKey) {
      const hasClosed = localStorage.getItem(`banner-closed-${storageKey}`);
      if (hasClosed === 'true') {
        setVisible(false);
      }
    }
  }, [showOnce, storageKey]);

  useEffect(() => {
    if (autoClose > 0 && visible) {
      const timer = setTimeout(() => {
        handleClose();
      }, autoClose);
      return () => clearTimeout(timer);
    }
  }, [autoClose, visible]);

  const handleClose = () => {
    setVisible(false);
    if (showOnce && storageKey) {
      localStorage.setItem(`banner-closed-${storageKey}`, 'true');
    }
  };

  if (!visible) return null;

  return (
    <Alert
      type={type}
      message={message}
      description={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>{description}</span>
          {action}
        </div>
      }
      closable={closable}
      onClose={handleClose}
      style={{ marginBottom: 16 }}
      showIcon
    />
  );
};

export default NotificationBanner;
