"""Structured logging 설정"""

import logging
import sys
from typing import Any, Dict
import structlog

from core.config import settings


def setup_logging():
    """Structured logging 설정 초기화"""

    # 표준 라이브러리 로깅 설정
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL),
    )

    # structlog 프로세서 체인 설정
    structlog.configure(
        processors=[
            # 타임스탬프 추가
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # JSON 포맷으로 출력
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # 외부 라이브러리 로깅 레벨 조정
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """구조화된 로거 가져오기"""
    return structlog.get_logger(name)


class LogContext:
    """로깅 컨텍스트 매니저"""

    def __init__(self, **context):
        self.context = context
        self.logger = structlog.get_logger()

    def __enter__(self):
        self.logger = self.logger.bind(**self.context)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def log_prediction(
    logger: structlog.stdlib.BoundLogger,
    admission_id: str,
    predicted_group: str,
    confidence: float,
    latency_ms: float,
    **kwargs,
):
    """예측 로깅 헬퍼"""
    logger.info(
        "prediction_made",
        admission_id=admission_id,
        predicted_group=predicted_group,
        confidence=confidence,
        latency_ms=latency_ms,
        **kwargs,
    )


def log_api_request(
    logger: structlog.stdlib.BoundLogger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: str = None,
    **kwargs,
):
    """API 요청 로깅 헬퍼"""
    log_data = {
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
    }

    if user_id:
        log_data["user_id"] = user_id

    log_data.update(kwargs)

    if status_code >= 500:
        logger.error("api_request", **log_data)
    elif status_code >= 400:
        logger.warning("api_request", **log_data)
    else:
        logger.info("api_request", **log_data)
