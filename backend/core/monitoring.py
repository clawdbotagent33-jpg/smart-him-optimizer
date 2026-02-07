"""모니터링 및 메트릭 수집 미들웨어"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from fastapi.responses import Response as FastAPIResponse

logger = logging.getLogger(__name__)

# Prometheus 메트릭 정의
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[
        0.005,
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
    ],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests", "Number of active HTTP requests", ["method"]
)

PREDICTION_COUNT = Counter(
    "predictions_total", "Total predictions made", ["prediction_type", "group"]
)

PREDICTION_LATENCY = Histogram(
    "prediction_duration_seconds",
    "Prediction duration in seconds",
    ["prediction_type"],
    buckets=[0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0],
)

DB_QUERY_COUNT = Counter(
    "db_queries_total", "Total database queries", ["operation", "table"]
)

DB_QUERY_DURATION = Histogram(
    "db_query_duration_seconds",
    "Database query duration in seconds",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Prometheus 메트릭 수집 미들웨어"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 활성 요청 증가
        ACTIVE_REQUESTS.labels(method=request.method).inc()

        # 요청 시작 시간
        start_time = time.time()

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise
        finally:
            # 요청 처리 시간 측정
            duration = time.time() - start_time

            # 엔드포인트 경로 추출 (파라미터 제거)
            endpoint = request.url.path

            # 메트릭 기록
            REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(
                duration
            )

            REQUEST_COUNT.labels(
                method=request.method, endpoint=endpoint, status_code=status_code
            ).inc()

            # 활성 요청 감소
            ACTIVE_REQUESTS.labels(method=request.method).dec()

            # 느린 요청 로깅 (1초 이상)
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {endpoint} took {duration:.3f}s"
                )

        return response


def record_prediction(prediction_type: str, group: str = "unknown"):
    """예측 메트릭 기록"""
    PREDICTION_COUNT.labels(prediction_type=prediction_type, group=group).inc()


def record_prediction_latency(prediction_type: str, duration: float):
    """예측 지연 시간 기록"""
    PREDICTION_LATENCY.labels(prediction_type=prediction_type).observe(duration)


def record_db_query(operation: str, table: str, duration: float):
    """DB 쿼리 메트릭 기록"""
    DB_QUERY_COUNT.labels(operation=operation, table=table).inc()

    DB_QUERY_DURATION.labels(operation=operation).observe(duration)


# 메트릭 엔드포인트
async def metrics_endpoint():
    """Prometheus 메트릭 엔드포인트"""
    return FastAPIResponse(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
