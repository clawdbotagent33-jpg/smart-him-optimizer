# Smart HIM Optimizer 2026

## 빠른 시작

### 1. 환경 설정

```bash
# Backend
cd backend
cp .env.example .env
# .env 파일编辑

# Frontend
cd frontend
cp .env.example .env
```

### 2. Docker 시작

```bash
docker-compose up -d
```

### 3. 데이터베이스 초기화

```bash
docker-compose exec backend python -c "from database.base import init_db; import asyncio; asyncio.run(init_db())"
```

### 4. ML 모델 학습 (선택)

```bash
docker-compose exec backend python ml/training/train_a_group_classifier.py
docker-compose exec backend python ml/training/train_denial_predictor.py
```

### 5. 접속

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 개발

### Backend 개발

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### Frontend 개발

```bash
cd frontend
npm install
npm start
```

## 보안 주의사항

1. .env 파일의 비밀번호를 반드시 변경하세요
2. production 모드에서 DEBUG=false로 설정하세요
3. SECRET_KEY를 안전한 값으로 변경하세요
4. 데이터베이스 접근을 제한하세요
