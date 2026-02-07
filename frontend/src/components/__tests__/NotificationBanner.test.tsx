/**
 * NotificationBanner 컴포넌트 테스트
 * - 사용자 이벤트 핸들링 검증
 * - localStorage 통합 테스트
 * - 자동 닫힘 기능 테스트
 */
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import NotificationBanner from '../NotificationBanner';

// localStorage 모킹
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => { store[key] = value; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('NotificationBanner', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('기본 렌더링', () => {
    it('메시지와 설명을 올바르게 표시해야 함', () => {
      render(
        <NotificationBanner
          type="info"
          message="테스트 메시지"
          description="테스트 설명"
        />
      );

      expect(screen.getByText('테스트 메시지')).toBeInTheDocument();
      expect(screen.getByText('테스트 설명')).toBeInTheDocument();
    });

    it('각 타입별로 올바른 스타일을 적용해야 함', () => {
      const { rerender } = render(
        <NotificationBanner type="success" description="성공 메시지" />
      );
      expect(screen.getByRole('alert')).toHaveClass('ant-alert-success');

      rerender(<NotificationBanner type="warning" description="경고 메시지" />);
      expect(screen.getByRole('alert')).toHaveClass('ant-alert-warning');

      rerender(<NotificationBanner type="error" description="에러 메시지" />);
      expect(screen.getByRole('alert')).toHaveClass('ant-alert-error');
    });
  });

  describe('닫기 기능', () => {
    it('닫기 버튼 클릭 시 배너가 사라져야 함', async () => {
      render(
        <NotificationBanner
          description="테스트"
          closable={true}
        />
      );

      const closeButton = screen.getByRole('button', { name: /close/i });
      await userEvent.click(closeButton);

      await waitFor(() => {
        expect(screen.queryByText('테스트')).not.toBeInTheDocument();
      });
    });

    it('closable=false일 때 닫기 버튼이 표시되지 않아야 함', () => {
      render(
        <NotificationBanner
          description="테스트"
          closable={false}
        />
      );

      const closeButton = screen.queryByRole('button', { name: /close/i });
      expect(closeButton).not.toBeInTheDocument();
    });
  });

  describe('localStorage showOnce 기능', () => {
    it('처음 방문 시 배너가 표시되어야 함', () => {
      render(
        <NotificationBanner
          description="한 번만 보는 메시지"
          showOnce={true}
          storageKey="test-banner"
        />
      );

      expect(screen.getByText('한 번만 보는 메시지')).toBeInTheDocument();
    });

    it('이미 닫은 배너는 다시 표시되지 않아야 함', () => {
      // 이전에 닫은 기록이 있다고 가정
      localStorage.setItem('banner-closed-test-banner-2', 'true');

      render(
        <NotificationBanner
          description="다시 보지 않을 메시지"
          showOnce={true}
          storageKey="test-banner-2"
        />
      );

      expect(screen.queryByText('다시 보지 않을 메시지')).not.toBeInTheDocument();
    });

    it('닫기 버튼 클릭 시 localStorage에 기록되어야 함', async () => {
      render(
        <NotificationBanner
          description="localStorage 테스트"
          showOnce={true}
          storageKey="test-storage"
        />
      );

      expect(localStorage.getItem('banner-closed-test-storage')).toBeNull();

      const closeButton = screen.getByRole('button', { name: /close/i });
      await userEvent.click(closeButton);

      expect(localStorage.getItem('banner-closed-test-storage')).toBe('true');
    });
  });

  describe('자동 닫힘 기능', () => {
    it('autoClose 시간이 지나면 자동으로 닫혀야 함', async () => {
      render(
        <NotificationBanner
          description="자동 닫힘 테스트"
          autoClose={3000}
        />
      );

      expect(screen.getByText('자동 닫힘 테스트')).toBeInTheDocument();

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      await waitFor(() => {
        expect(screen.queryByText('자동 닫힘 테스트')).not.toBeInTheDocument();
      });
    });

    it('autoClose=0이면 자동으로 닫히지 않아야 함', async () => {
      render(
        <NotificationBanner
          description="자동 닫힘 없음"
          autoClose={0}
        />
      );

      act(() => {
        jest.advanceTimersByTime(10000);
      });

      expect(screen.getByText('자동 닫힘 없음')).toBeInTheDocument();
    });
  });

  describe('액션 버튼', () => {
    it('액션 버튼이 렌더링되어야 함', () => {
      render(
        <NotificationBanner
          description="메시지"
          action={<button type="button">액션</button>}
        />
      );

      expect(screen.getByRole('button', { name: '액션' })).toBeInTheDocument();
    });

    it('액션 버튼 클릭 핸들러가 작동해야 함', async () => {
      const handleClick = jest.fn();
      render(
        <NotificationBanner
          description="메시지"
          action={<button type="button" onClick={handleClick}>액션</button>}
        />
      );

      const actionButton = screen.getByRole('button', { name: '액션' });
      await userEvent.click(actionButton);

      expect(handleClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('접근성', () => {
    it('적절한 ARIA 역할을 가져야 함', () => {
      render(
        <NotificationBanner
          type="error"
          description="에러 메시지"
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('경고 타입은 alert 역할을 가져야 함', () => {
      render(
        <NotificationBanner
          type="warning"
          description="경고 메시지"
        />
      );

      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });
});
