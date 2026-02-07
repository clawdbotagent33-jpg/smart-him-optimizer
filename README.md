# Smart HIM Optimizer 2026

[![CI/CD](https://github.com/your-org/smart-him-optimizer/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/smart-him-optimizer/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/your-org/smart-him-optimizer/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/smart-him-optimizer)
[![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org)

AI 기반 보건의료정보 수익 최적화 시스템

## 📋 프로젝트 개요

Smart HIM Optimizer는 공공의료기관의 보건의료정보 수익을 최적화하기 위한 AI 기반 시스템입니다. K-DRG v4.7 및 KCD-9 규정에 대응하며, B그룹(일반질병군)에서 A그룹(전문질병군)으로의 전환율 극대화를 목표로 합니다.

### 🎯 주요 목표

- **수익성**: A그룹 비중 10~15% 상향, CMI 지수 개선
- **정확성**: KCD-9 미준수 삭감률 20% 감소
- **효율성**: 수기 데이터 정리 및 보고서 작성 시간 80% 단축

## 🏗️ 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  React 18 + TypeScript + Ant Design + React Query           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        Nginx                                 │
│                 Reverse Proxy + SSL                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│  FastAPI + SQLAlchemy + Pydantic + AsyncIO                  │
│  - 인증/인가 (JWT)                                          │
│  - AI 예측 (XGBoost + 규칙 기반)                            │
│  - RAG 검색 (ChromaDB/pgvector)                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
│  PostgreSQL (pgvector) + ChromaDB + Redis (Cache)          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 기술 스택

### Backend
- **Python 3.14** - 최신 Python 버전
- **FastAPI** - 고성능 비동기 API 프레임워크
- **SQLAlchemy 2.0** - Async ORM
- **PostgreSQL + pgvector** - 벡터 검색 지원 데이터베이스
- **ChromaDB** - RAG 문서 저장
- **XGBoost/Scikit-learn** - ML 모델

### Frontend
- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안전성
- **Ant Design 5** - UI 컴포넌트
- **React Query v5** - 데이터 페칭 및 캐싱
- **Zustand** - 상태 관리
- **Recharts** - 데이터 시각화

### Infrastructure
- **Docker + Docker Compose** - 컨테이너화
- **GitHub Actions** - CI/CD 파이프라인
- **Prometheus** - 메트릭 수집
- **Structlog** - 구조화된 로깅

## 📦 설치 및 실행

### 사전 요구사항
- Python 3.14
- Node.js 20
- Docker & Docker Compose
- PostgreSQL 16 (pgvector)

### 1. 저장소 클론

```bash
git clone https://github.com/your-org/smart-him-optimizer.git
cd smart-him-optimizer
```

### 2. 환경 설정

```bash
# Backend
cd backend
cp .env.example .env
# .env 파일 수정 (데이터베이스 연결 정보 등)

# Frontend
cd ../frontend
cp .env.example .env
# .env 파일 수정 (API URL 등)
```

### 3. Docker로 실행 (권장)

```bash
# 모든 서비스 시작
docker-compose up -d

# 특정 서비스만 시작
docker-compose up -d postgres backend
```

### 4. 수동 실행 (개발용)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 데이터베이스 초기화
python scripts/init_database.py

# 서버 실행
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm start
```

### 5. 접속

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Prometheus 메트릭**: http://localhost:8000/metrics

## 🧪 테스트

### Backend 테스트
```bash
cd backend
pytest tests/ -v --cov=backend --cov-report=html
```

### Frontend 테스트
```bash
cd frontend
npm test
```

## 📊 모니터링

### Prometheus 메트릭

시스템은 다음과 같은 Prometheus 메트릭을 제공합니다:

- `http_requests_total` - HTTP 요청 총계
- `http_request_duration_seconds` - HTTP 요청 처리 시간
- `predictions_total` - AI 예측 횟수
- `prediction_duration_seconds` - 예측 처리 시간
- `db_queries_total` - 데이터베이스 쿼리 횟수

### 로깅

구조화된 JSON 로깅을 사용합니다:

```python
from core.logging_config import get_logger

logger = get_logger(__name__)
logger.info("prediction_made", 
    admission_id="ADM001",
    predicted_group="A",
    confidence=0.85
)
```

## 🔐 보안

- **비식별화**: AES-256 암호화 (환자 ID, 이름 등)
- **인증**: JWT 기반 인증
- **On-premise**: 외부 API 호출 없이 원내 서버에서 구동
- **접근 제어**: 역할 기반 (관리자, HIM관리사, 의사, 간호사)

## 📝 주요 기능

### 1. 대시보드
- CMI 지표 실시간 모니터링
- 그룹별(A/B/C) 분포 시각화
- 삭감율 추이 분석
- 상위 진단별 통계

### 2. 입원 관리
- CSV 대량 업로드 (ezCaretech EMR export)
- 환자별 비식별화 처리
- 입원 건 상세 조회
- CDI 쿼리 발송

### 3. AI 예측
- K-DRG 그룹 예측 (A/B/C)
- A그룹 전환 가능성 분석
- 청구 삭감 위험도 평가
- 업그레이드 제안 (RAG 기반)

### 4. 문서 관리 (RAG)
- K-DRG v4.7 가이드라인 업로드
- KCD-9 규정 학습
- 수기 메모 디지털화
- 지식 검색 (LLM 기반)

## 🛠️ 개발

### 프로젝트 구조

```
smart-him-optimizer/
├── backend/
│   ├── api/              # FastAPI 엔드포인트
│   ├── core/             # 설정, 보안, 모니터링
│   ├── database/         # DB 모델, 마이그레이션
│   ├── models/           # ML 예측 모델
│   ├── rag/              # RAG 시스템
│   ├── services/         # 비즈니스 로직
│   └── tests/            # 테스트 코드
├── frontend/
│   └── src/
│       ├── components/   # UI 컴포넌트
│       ├── pages/        # 페이지
│       ├── services/     # API 클라이언트
│       └── store/        # 상태 관리
├── ml/
│   └── training/         # 모델 학습 스크립트
├── nginx/                # 리버스 프록시 설정
└── .github/
    └── workflows/        # CI/CD 파이프라인
```

### 브랜치 전략

- `main`: 프로덕션 배포
- `develop`: 개발 브랜치
- `feature/*`: 기능 개발
- `hotfix/*`: 긴급 수정

## 📚 문서

- [API 문서](http://localhost:8000/docs) (Swagger UI)
- [배포 가이드](./docs/DEPLOY.md)
- [개발자 가이드](./docs/DEVELOPMENT.md)
- [API 명세](./docs/API.md)

## 🤝 기여

1. Fork 저장소
2. Feature 브랜치 생성 (`git checkout -b feature/amazing-feature`)
3. 변경사항 커밋 (`git commit -m 'Add amazing feature'`)
4. 브랜치에 Push (`git push origin feature/amazing-feature`)
5. Pull Request 생성

## 📄 라이선스

Copyright (c) 2026 Smart HIM Optimizer Team. All rights reserved.

## 📞 문의

- **Email**: support@him-optimizer.local
- **Issue**: https://github.com/your-org/smart-him-optimizer/issues

---

**대구보훈병원 보건의료정보관리과** 개발
