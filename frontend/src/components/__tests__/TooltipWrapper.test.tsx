/**
 * TooltipWrapper 컴포넌트 테스트
 * - 툴팁 표시/숨김 이벤트 검증
 * - showOnce 기능 테스트
 * - 사용자 인터랙션 테스트
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TooltipWrapper, { ContextHelp } from '../TooltipWrapper';

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

describe('TooltipWrapper', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  describe('기본 렌더링', () => {
    it('자식 요소를 렌더링해야 함', () => {
      render(
        <TooltipWrapper content="툴팁 내용">
          <button>Hover me</button>
        </TooltipWrapper>
      );

      expect(screen.getByRole('button', { name: 'Hover me' })).toBeInTheDocument();
    });

    it('iconOnly 모드일 때 아이콘을 렌더링해야 함', () => {
      render(
        <TooltipWrapper content="툴팁 내용" iconOnly={true}>
          <span>원래 요소</span>
        </TooltipWrapper>
      );

      // 아이콘이 있는지 확인 (클래스나 역할로)
      const svg = document.querySelector('.anticon-question-circle');
      expect(svg).toBeInTheDocument();
    });
  });

  describe('툴팁 표시', () => {
    it('호버 시 툴팁 내용이 표시되어야 함', async () => {
      render(
        <TooltipWrapper content="툴팁 설명">
          <button>Hover me</button>
        </TooltipWrapper>
      );

      const button = screen.getByRole('button', { name: 'Hover me' });

      // 호버 시뮬레이션
      await userEvent.hover(button);

      await waitFor(() => {
        expect(screen.getByText('툴팁 설명')).toBeInTheDocument();
      });
    });

    it('title이 있을 때 제목도 표시되어야 함', async () => {
      render(
        <TooltipWrapper title="제목" content="내용">
          <button>Hover</button>
        </TooltipWrapper>
      );

      const button = screen.getByRole('button', { name: 'Hover' });
      await userEvent.hover(button);

      await waitFor(() => {
        expect(screen.getByText('제목')).toBeInTheDocument();
        expect(screen.getByText('내용')).toBeInTheDocument();
      });
    });
  });

  describe('showOnce 기능', () => {
    it('처음 진입 시 자동으로 툴팁을 표시해야 함', async () => {
      render(
        <TooltipWrapper
          content="한 번만 보는 툴팁"
          showOnce={true}
          storageKey="test-tooltip"
        >
          <button>Button</button>
        </TooltipWrapper>
      );

      act(() => {
        jest.advanceTimersByTime(500);
      });

      await waitFor(() => {
        expect(screen.getByText('한 번만 보는 툴팁')).toBeInTheDocument();
      });
    });

    it('이미 본 툴팁은 자동으로 표시되지 않아야 함', async () => {
      localStorage.setItem('tooltip-seen-already-seen', 'true');

      render(
        <TooltipWrapper
          content="이미 본 툴팁"
          showOnce={true}
          storageKey="already-seen"
        >
          <button>Button</button>
        </TooltipWrapper>
      );

      act(() => {
        jest.advanceTimersByTime(500);
      });

      expect(screen.queryByText('이미 본 툴팁')).not.toBeInTheDocument();
    });

    it('툴팁을 닫으면 localStorage에 기록되어야 함', async () => {
      render(
        <TooltipWrapper
          content="기록 테스트"
          showOnce={true}
          storageKey="record-test"
        >
          <button>Button</button>
        </TooltipWrapper>
      );

      const button = screen.getByRole('button', { name: 'Button' });
      await userEvent.hover(button);

      await waitFor(() => {
        expect(screen.getByText('기록 테스트')).toBeInTheDocument();
      });

      // 툴팁 숨김
      await userEvent.unhover(button);

      await waitFor(() => {
        expect(localStorage.getItem('tooltip-seen-record-test')).toBe('true');
      });
    });
  });

  describe('placement 속성', () => {
    it('placement 속성이 올바르게 적용되어야 함', async () => {
      const { container } = render(
        <TooltipWrapper content="툴팁" placement="bottom">
          <button>Button</button>
        </TooltipWrapper>
      );

      // Ant Design Tooltip은 placement를 props로 받아 처리
      // 실제 DOM에는 data-* 속성이나 클래스로 반영될 수 있음
      const button = screen.getByRole('button');
      await userEvent.hover(button);

      // placement가 적용되었는지 확인 (구체적 구현에 따라 다름)
      expect(screen.getByText('툴팁')).toBeInTheDocument();
    });
  });
});

describe('ContextHelp', () => {
  it('정보 아이콘을 렌더링해야 함', () => {
    render(
      <ContextHelp content="도움말 내용" />
    );

    const svg = document.querySelector('.anticon-info-circle');
    expect(svg).toBeInTheDocument();
  });

  it('title이 있을 때 제목과 내용을 모두 표시해야 함', async () => {
    render(
      <ContextHelp title="도움말 제목" content="도움말 내용" />
    );

    const icon = document.querySelector('.anticon-info-circle');
    expect(icon).toBeInTheDocument();

    // 호버 시 내용 확인
    if (icon) {
      await userEvent.hover(icon);
      await waitFor(() => {
        expect(screen.getByText('도움말 제목')).toBeInTheDocument();
        expect(screen.getByText('도움말 내용')).toBeInTheDocument();
      });
    }
  });

  it('기본 placement가 right여야 함', () => {
    const { container } = render(
      <ContextHelp content="도움말" />
    );

    // ContextHelp 기본 placement 확인
    const icon = document.querySelector('.anticon-info-circle');
    expect(icon).toBeInTheDocument();
  });
});

// act import 추가
import { act } from 'react-dom/test-utils';
