"""FastAPI 메인 애플리케이션 - Smart HIM Optimizer"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import traceback

from core.config import settings
from core.logging_config import setup_logging, get_logger
from core.monitoring import MetricsMiddleware, metrics_endpoint

# Structured logging 설정
setup_logging()
logger = get_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI 기반 보건의료정보 수익 최적화 시스템",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus 메트릭 수집 미들웨어
app.add_middleware(MetricsMiddleware)


# Startup 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 초기화"""
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 시작 중...")

    # 데이터베이스 초기화
    try:
        from database.base import init_db

        await init_db()
        logger.info("데이터베이스 초기화 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise

    # RAG 시스템 초기화
    try:
        from rag.embedding import embedding_service

        embedding_service.init_chroma()
        logger.info("RAG 시스템 초기화 완료")
    except Exception as e:
        logger.warning(f"RAG 시스템 초기화 실패: {e}")

    logger.info("서비스 시작 완료")


# Health Check
@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Prometheus 메트릭 엔드포인트
@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    return await metrics_endpoint()


# 포함할 라우터
from api.v1 import auth, admissions, documents, predictions, dashboard

app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["인증"])
app.include_router(admissions.router, prefix=settings.API_V1_PREFIX, tags=["입원 관리"])
app.include_router(documents.router, prefix=settings.API_V1_PREFIX, tags=["문서 관리"])
app.include_router(predictions.router, prefix=settings.API_V1_PREFIX, tags=["AI 예측"])
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX, tags=["대시보드"])


# 글로벌 예외 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(f"Unhandled exception: {str(exc)}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "낶부 서버 오류가 발생했습니다"
            if not settings.DEBUG
            else str(exc),
            "status_code": 500,
        },
    )
