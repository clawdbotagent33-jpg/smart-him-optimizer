# 개발자 가이드

Smart HIM Optimizer 개발을 위한 가이드

## 📋 목차

1. [개발 환경 설정](#개발-환경-설정)
2. [코딩 컨벤션](#코딩-컨벤션)
3. [Git 워크플로우](#git-워크플로우)
4. [테스트 작성](#테스트-작성)
5. [API 개발](#api-개발)
6. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
7. [디버깅](#디버깅)

## 개발 환경 설정

### Backend 개발 환경

```bash
cd backend

# 가상환경 생성
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 개발용 의존성 추가 설치
pip install flake8 black isort mypy pytest pytest-asyncio

# pre-commit 설정 (선택사항)
pre-commit install
```

### Frontend 개발 환경

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm start
```

## 코딩 컨벤션

### Python (Backend)

- **PEP 8** 준수
- **Black** 포맷터 사용
- **isort**로 import 정렬
- **Type hints** 필수

```python
# 좋은 예
from typing import Dict, List, Optional

async def predict_group(
    data: Dict[str, Any],
    admission_id: Optional[str] = None
) -> GroupPredictionResult:
    """K-DRG 그룹 예측
    
    Args:
        data: 입원 데이터
        admission_id: 입원 ID (optional)
        
    Returns:
        GroupPredictionResult: 예측 결과
    """
    if not data.get("principal_diagnosis"):
        raise ValueError("주진단이 필요합니다")
    
    # 예측 로직...
```

### TypeScript (Frontend)

- **ESLint** 규칙 준수
- **Prettier** 포맷터 사용
- **명시적 타입** 선언

```typescript
// 좋은 예
interface PredictionRequest {
  principalDiagnosis: string;
  secondaryDiagnoses?: string[];
  age?: number;
}

const usePrediction = () => {
  const [result, setResult] = useState<PredictionResponse | null>(null);
  
  const predict = useCallback(async (data: PredictionRequest) => {
    const response = await predictionsApi.predictGroup(data);
    setResult(response);
  }, []);
  
  return { result, predict };
};
```

## Git 워크플로우

### 브랜치 전략

```
main
  └── develop
       ├── feature/auth-improvement
       ├── feature/new-dashboard
       └── bugfix/login-error
```

### 커밋 메시지 규칙

```
<type>: <subject>

<body>

<footer>
```

**타입:**
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅
- `refactor`: 코드 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 기타 작업

**예시:**
```
feat: AI 예측 결과 캐싱 기능 추가

- Redis 캐싱 적용
- 캐시 무효화 로직 구현
- 캐시 히트 로깅 추가

Closes #123
```

### Pull Request 규칙

1. PR 템플릿 준수
2. 테스트 통과 확인
3. 코드 리뷰 1인 이상 승인
4. main/develop 브랜치는 직접 푸시 금지

## 테스트 작성

### Backend 테스트

```python
# tests/test_predictions.py
import pytest
from fastapi.testclient import TestClient

class TestPredictionsAPI:
    """예측 API 테스트"""
    
    def test_predict_group_success(self, client: TestClient):
        """그룹 예측 성공 테스트"""
        # Given
        request_data = {
            "principalDiagnosis": "I50",
            "age": 65
        }
        
        # When
        response = client.post("/api/v1/predictions/group", json=request_data)
        
        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["predictedGroup"] in ["A", "B", "C"]
        assert 0 <= data["confidence"] <= 1
    
    @pytest.mark.parametrize("diagnosis,expected_group", [
        ("A01", "A"),
        ("B01", "B"),
        ("C01", "C"),
    ])
    def test_predict_group_by_diagnosis(
        self, client: TestClient, diagnosis: str, expected_group: str
    ):
        """진단 코드별 그룹 예측 테스트"""
        response = client.post(
            "/api/v1/predictions/group",
            json={"principalDiagnosis": diagnosis}
        )
        
        assert response.status_code == 200
        assert response.json()["predictedGroup"] == expected_group
```

### 테스트 실행

```bash
# 모든 테스트 실행
pytest tests/

# 특정 테스트 파일
pytest tests/test_predictions.py

# 커버리지 보고서
pytest --cov=backend --cov-report=html

# 특정 테스트만
pytest -k "test_predict_group"
```

## API 개발

### 새로운 엔드포인트 추가

1. **스키마 정의** (`api/schemas.py`)

```python
class NewFeatureRequest(BaseModel):
    """새 기능 요청"""
    param1: str
    param2: Optional[int] = None

class NewFeatureResponse(CamelModel):
    """새 기능 응답"""
    result: str
    timestamp: datetime
```

2. **라우터 구현** (`api/v1/new_feature.py`)

```python
from fastapi import APIRouter, HTTPException
from api.schemas import NewFeatureRequest, NewFeatureResponse

router = APIRouter()

@router.post("/new-feature", response_model=NewFeatureResponse)
async def create_new_feature(request: NewFeatureRequest):
    """새 기능 엔드포인트"""
    try:
        # 비즈니스 로직
        result = await process_feature(request)
        
        return NewFeatureResponse(
            result=result,
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"처리 중 오류: {str(e)}"
        )
```

3. **메인 앱 등록** (`api/main.py`)

```python
from api.v1 import new_feature

app.include_router(
    new_feature.router,
    prefix=settings.API_V1_PREFIX,
    tags=["새 기능"]
)
```

## 데이터베이스 마이그레이션

### 새로운 마이그레이션 생성

```bash
# Alembic 마이그레이션 생성
alembic revision --autogenerate -m "Add new table"

# 마이그레이션 적용
alembic upgrade head

# 특정 버전으로 이동
alembic downgrade -1
alembic upgrade +1
```

### 모델 변경 시 주의사항

1. **모델 수정** (`database/models.py`)
2. **마이그레이션 생성 및 검토**
3. **개발 환경에서 테스트**
4. **스테이징 환경에서 테스트**
5. **프로덕션 배포**

## 디버깅

### Backend 디버깅

```python
# 로깅 활용
from core.logging_config import get_logger

logger = get_logger(__name__)

async def debug_function():
    logger.debug("디버그 정보", extra={"variable": value})
    
    # 중단점 (pdb)
    import pdb; pdb.set_trace()
```

### Frontend 디버깅

```typescript
// React DevTools 사용
// 브라우저 개발자 도구 > Components 탭

// 콘솔 로깅
console.log('Debug:', { data, state });

// React Query DevTools
// 개발 환경에서 자동 활성화
```

### Docker 디버깅

```bash
# 컨테이너 로그 확인
docker-compose logs -f backend

# 컨테이너 접속
docker-compose exec backend bash
docker-compose exec postgres psql -U him_admin smart_him_db

# 환경 변수 확인
docker-compose exec backend env
```

## 성능 최적화

### 캐싱 적용

```python
from core.cache import cached

@cached(ttl=300, key_prefix="prediction")
async def predict_with_cache(data: dict):
    return await expensive_prediction(data)
```

### 데이터베이스 쿼리 최적화

```python
# N+1 문제 방지
from sqlalchemy.orm import selectinload

results = await session.execute(
    select(Admission)
    .options(selectinload(Admission.patient))
    .where(Admission.id == id)
)

# 인덱스 활용
# 모델에 인덱스 추가
class Admission(Base):
    __tablename__ = "admissions"
    
    admission_id = Column(String, index=True)  # 인덱스 추가
    created_at = Column(DateTime, index=True)  # 인덱스 추가
```

## 유용한 명령어

### Backend

```bash
# 코드 품질 검사
flake8 backend/
black backend/ --check
mypy backend/

# 테스트 커버리지
pytest --cov=backend --cov-report=html
open htmlcov/index.html
```

### Frontend

```bash
# 린트 및 포맷 검사
npm run lint
npm run format:check

# 타입 체크
npx tsc --noEmit

# 테스트
npm test
npm test -- --coverage
```

## 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [SQLAlchemy 문서](https://docs.sqlalchemy.org/)
- [React 문서](https://react.dev/)
- [TypeScript 문서](https://www.typescriptlang.org/)

---

**문의**: dev-team@him-optimizer.local
