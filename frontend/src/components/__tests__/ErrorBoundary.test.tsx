/**
 * 에러 바운더리 및 이벤트 핸들링 테스트
 * - 런타임 에러 처리
 * - 네트워크 오류 시나리오
 * - 사용자 피드백 제공
 */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider, useQuery } from '@tanstack/react-query';

// 에러 바운더리 컴포넌트
class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div role="alert" data-testid="error-boundary">
            <h2>오류가 발생했습니다</h2>
            <p>{this.state.error?.message}</p>
            <button onClick={() => this.setState({ hasError: false })}>
              다시 시도
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}

// 에러를 발생시키는 컴포넌트
const ThrowError: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow = true }) => {
  if (shouldThrow) {
    throw new Error('테스트 에러');
  }
  return <div>정상 렌더링</div>;
};

describe('ErrorBoundary', () => {
  beforeEach(() => {
    jest.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('에러 캡처', () => {
    it('자식 컴포넌트 에러를 캡처해야 함', () => {
      render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary')).toBeInTheDocument();
      expect(screen.getByText('오류가 발생했습니다')).toBeInTheDocument();
      expect(screen.getByText('테스트 에러')).toBeInTheDocument();
    });

    it('에러 발생 시 fallback 컴포넌트를 렌더링해야 함', () => {
      const customFallback = <div data-testid="custom-fallback">사용자 정의 에러</div>;

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
      expect(screen.getByText('사용자 정의 에러')).toBeInTheDocument();
    });

    it('정상 상태에서는 자식 컴포넌트를 렌더링해야 함', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByText('정상 렌더링')).toBeInTheDocument();
      expect(screen.queryByTestId('error-boundary')).not.toBeInTheDocument();
    });
  });

  describe('에러 복구', () => {
    it('다시 시도 버튼 클릭 시 상태가 초기화되어야 함', async () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError />
        </ErrorBoundary>
      );

      expect(screen.getByTestId('error-boundary')).toBeInTheDocument();

      // 다시 시도 버튼 클릭
      const retryButton = screen.getByRole('button', { name: '다시 시도' });
      await userEvent.click(retryButton);

      // 에러 상태가 초기화되고 정상 컴포넌트를 렌더링
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      );

      expect(screen.getByText('정상 렌더링')).toBeInTheDocument();
      expect(screen.queryByTestId('error-boundary')).not.toBeInTheDocument();
    });
  });

  describe('중첩 에러 바운더리', () => {
    it('가장 가까운 에러 바운더리가 에러를 캡처해야 함', () => {
      const innerFallback = <div data-testid="inner-fallback">내부 에러</div>;
      const outerFallback = <div data-testid="outer-fallback">외부 에러</div>;

      render(
        <ErrorBoundary fallback={outerFallback}>
          <ErrorBoundary fallback={innerFallback}>
            <ThrowError />
          </ErrorBoundary>
        </ErrorBoundary>
      );

      expect(screen.getByTestId('inner-fallback')).toBeInTheDocument();
      expect(screen.queryByTestId('outer-fallback')).not.toBeInTheDocument();
    });
  });
});

describe('네트워크 오류 시나리오', () => {
  const createTestQueryClient = () => {
    return new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          staleTime: Infinity,
        },
      },
    });
  };

  // 실패하는 쿼리를 수행하는 컴포넌트
  const FailingQueryComponent: React.FC = () => {
    const { data, error, isError, isLoading } = useQuery({
      queryKey: ['test-error'],
      queryFn: async () => {
        throw new Error('네트워크 오류');
      },
    });

    if (isLoading) return <div>로딩 중...</div>;
    if (isError) return <div data-testid="query-error">에러: {error.message}</div>;
    return <div>데이터: {data}</div>;
  };

  it('네트워크 오류 시 사용자에게 적절한 메시지를 표시해야 함', async () => {
    const queryClient = createTestQueryClient();

    render(
      <QueryClientProvider client={queryClient}>
        <FailingQueryComponent />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('query-error')).toBeInTheDocument();
      expect(screen.getByText(/네트워크 오류/)).toBeInTheDocument();
    });
  });

  it('재시도 기능을 제공해야 함', async () => {
    const queryClient = createTestQueryClient();

    const TestComponent = () => {
      const { isError, error, refetch } = useQuery({
        queryKey: ['retry-test'],
        queryFn: async () => {
          throw new Error('일시적 오류');
        },
      });

      if (isError) {
        return (
          <div>
            <p data-testid="error-msg">{error.message}</p>
            <button onClick={() => refetch()} data-testid="retry-btn">
              재시도
            </button>
          </div>
        );
      }
      return <div>성공</div>;
    };

    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <TestComponent />
      </QueryClientProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('retry-btn')).toBeInTheDocument();
    });

    // 재시도 버튼이 클릭 가능한지 확인
    const retryBtn = screen.getByTestId('retry-btn');
    expect(retryBtn).toBeEnabled();
  });
});

describe('사용자 인터랙션 에러 처리', () => {
  it('버튼 클릭 에러를 적절히 처리해야 함', async () => {
    const handleError = jest.fn();
    const throwOnAction = () => {
      throw new Error('액션 오류');
    };

    const TestComponent = () => {
      const [error, setError] = React.useState<string | null>(null);

      const handleClick = () => {
        try {
          throwOnAction();
        } catch (e) {
          const message = e instanceof Error ? e.message : '알 수 없는 오류';
          setError(message);
          handleError(message);
        }
      };

      return (
        <div>
          <button onClick={handleClick} data-testid="action-btn">
            액션 실행
          </button>
          {error && <div data-testid="error-display">{error}</div>}
        </div>
      );
    };

    render(<TestComponent />);

    const button = screen.getByTestId('action-btn');
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByTestId('error-display')).toBeInTheDocument();
      expect(screen.getByText('액션 오류')).toBeInTheDocument();
      expect(handleError).toHaveBeenCalledWith('액션 오류');
    });
  });

  it('폼 제출 에러를 적절히 처리해야 함', async () => {
    const TestForm = () => {
      const [status, setStatus] = React.useState<'idle' | 'error' | 'success'>('idle');

      const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
          // 실패하는 API 호출 시뮬레이션
          await Promise.reject(new Error('서버 오류 500'));
        } catch {
          setStatus('error');
        }
      };

      return (
        <form onSubmit={handleSubmit}>
          <button type="submit" data-testid="submit-btn">
            제출
          </button>
          {status === 'error' && (
            <div data-testid="form-error" role="alert">
              제출 중 오류가 발생했습니다. 다시 시도해 주세요.
            </div>
          )}
        </form>
      );
    };

    render(<TestForm />);

    const submitBtn = screen.getByTestId('submit-btn');
    await userEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByTestId('form-error')).toBeInTheDocument();
      expect(screen.getByText(/제출 중 오류가 발생했습니다/)).toBeInTheDocument();
    });
  });
});
