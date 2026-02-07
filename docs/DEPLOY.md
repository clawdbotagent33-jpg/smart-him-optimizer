# 배포 가이드

Smart HIM Optimizer 프로덕션 배포 가이드

## 📋 목차

1. [사전 준비](#사전-준비)
2. [서버 요구사항](#서버-요구사항)
3. [환경 설정](#환경-설정)
4. [Docker Compose 배포](#docker-compose-배포)
5. [SSL 인증서 설정](#ssl-인증서-설정)
6. [모니터링 설정](#모니터링-설정)
7. [백업 및 복구](#백업-및-복구)
8. [트러블슈팅](#트러블슈팅)

## 사전 준비

### 필요한 도구
- SSH 접근 권한
- Docker 및 Docker Compose 설치
- Git

### 저장소 클론

```bash
cd /opt
git clone https://github.com/your-org/smart-him-optimizer.git
cd smart-him-optimizer
```

## 서버 요구사항

### 최소 사양
- **CPU**: 4코어
- **RAM**: 8GB
- **디스크**: 100GB SSD
- **OS**: Ubuntu 22.04 LTS

### 권장 사양
- **CPU**: 8코어 이상
- **RAM**: 16GB 이상
- **디스크**: 200GB SSD
- **GPU**: NVIDIA GPU (LLM 사용 시)

### 포트
- 80 (HTTP)
- 443 (HTTPS)
- 5432 (PostgreSQL, 낮부용)
- 8000 (Backend API)
- 3000 (Frontend, 개발용)

## 환경 설정

### 1. Backend 환경 변수

```bash
cd backend
cp .env.example .env
vim .env
```

**필수 설정값:**

```env
# 데이터베이스 (반드시 변경!)
DATABASE_URL=postgresql+asyncpg://him_admin:STRONG_PASSWORD@postgres:5432/smart_him_db
POSTGRES_PASSWORD=STRONG_PASSWORD

# 보안 (반드시 변경!)
SECRET_KEY=$(openssl rand -base64 32)
ANONYMIZATION_KEY=$(openssl rand -base64 32)

# 환경
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=["https://your-domain.com"]
```

### 2. Frontend 환경 변수

```bash
cd frontend
cp .env.production .env
vim .env
```

```env
REACT_APP_API_URL=https://your-domain.com/api/v1
REACT_APP_ENV=production
```

## Docker Compose 배포

### 1. Docker 네트워크 생성

```bash
docker network create smart-him-network
```

### 2. 서비스 시작

```bash
# 프로덕션 모드로 시작
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 로그 확인
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 3. 데이터베이스 마이그레이션

```bash
# 컨테이너 접속
docker-compose exec backend bash

# 마이그레이션 실행
alembic upgrade head

# 초기 데이터 시드 (선택사항)
python scripts/seed_data.py
```

### 4. 헬스 체크

```bash
# Backend 헬스 체크
curl http://localhost:8000/health

# 전체 시스템 체크
curl http://localhost:80/health
```

## SSL 인증서 설정

### Let's Encrypt 사용

```bash
# Certbot 설치
sudo apt update
sudo apt install certbot python3-certbot-nginx

# 인증서 발급
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 자동 갱신 확인
sudo certbot renew --dry-run
```

### 수동 인증서 설정

```bash
# 인증서 파일 준비
# - fullchain.pem
# - privkey.pem

# Nginx 설정
cp nginx/nginx-ssl.conf nginx/nginx.conf
vim nginx/nginx.conf  # 도메인 수정

# 인증서 복사
mkdir -p nginx/ssl
cp /path/to/fullchain.pem nginx/ssl/
cp /path/to/privkey.pem nginx/ssl/

# Nginx 재시작
docker-compose restart nginx
```

## 모니터링 설정

### Prometheus + Grafana (선택사항)

```bash
# monitoring 디렉토리로 이동
cd monitoring

# 모니터링 스택 시작
docker-compose up -d

# Grafana 접속
# URL: http://your-domain.com:3001
# 기본 계정: admin/admin
```

### 알림 설정

1. Grafana에서 Alerting 메뉴 접속
2. Notification channels 설정
3. Alert rules 설정:
   - API 응답 시간 > 2초
   - 에러율 > 5%
   - 디스크 사용량 > 80%
   - 메모리 사용량 > 90%

## 백업 및 복구

### 자동 백업 스크립트

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/smart-him/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# 데이터베이스 백업
docker-compose exec -T postgres pg_dump -U him_admin smart_him_db > $BACKUP_DIR/database.sql

# RAG 데이터 백업
cp -r data/chroma $BACKUP_DIR/

# 업로드 파일 백업
cp -r data/uploads $BACKUP_DIR/

# 압축
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

# 오래된 백업 삭제 (30일 이상)
find /backup/smart-him -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### cron 설정

```bash
# 매일 새벽 2시에 백업
0 2 * * * /opt/smart-him-optimizer/scripts/backup.sh >> /var/log/smart-him-backup.log 2>&1
```

### 복구 절차

```bash
# 1. 서비스 중지
docker-compose down

# 2. 데이터베이스 복구
docker-compose up -d postgres
sleep 10
docker-compose exec -T postgres psql -U him_admin smart_him_db < backup.sql

# 3. 서비스 시작
docker-compose up -d
```

## 업데이트 배포

### 무중단 배포

```bash
# 1. 최신 코드 가져오기
git pull origin main

# 2. 이미지 빌드
docker-compose build

# 3. 새 버전 시작
docker-compose up -d

# 4. 헬스 체크
curl http://localhost/health

# 5. 이전 컨테이너 정리
docker system prune -f
```

### 롤백

```bash
# 이전 버전으로 롤백
git log --oneline  # 커밋 확인
git checkout <commit-hash>
docker-compose up -d --build
```

## 트러블슈팅

### 서비스 시작 실패

```bash
# 로그 확인
docker-compose logs <service-name>

# 컨테이너 상태 확인
docker-compose ps

# 리소스 사용량 확인
docker stats
```

### 데이터베이스 연결 문제

```bash
# PostgreSQL 로그 확인
docker-compose logs postgres

# 네트워크 연결 확인
docker network inspect smart-him-network

# 데이터베이스 연결 테스트
docker-compose exec backend python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql+asyncpg://him_admin:password@postgres:5432/smart_him_db')
print('Connection successful')
"
```

### 메모리 부족

```bash
# 메모리 사용량 확인
free -h
docker system df

# 불필요한 이미지/컨테이너 삭제
docker system prune -a

# 스왑 설정 (필요시)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### SSL 인증서 문제

```bash
# 인증서 확인
openssl x509 -in nginx/ssl/fullchain.pem -text -noout

# 인증서 갱신
sudo certbot renew

# Nginx 설정 테스트
docker-compose exec nginx nginx -t
```

## 보안 체크리스트

- [ ] 기본 비밀번호 변경
- [ ] 환경 변수 파일 권한 설정 (600)
- [ ] 방화벽 설정 (UFW/iptables)
- [ ] SSL/TLS 인증서 적용
- [ ] fail2ban 설치 및 설정
- [ ] 정기적인 보안 업데이트
- [ ] 로그 모니터링 활성화
- [ ] 백업 암호화

## 연락처

- **기술 지원**: tech-support@him-optimizer.local
- **긴급 연락**: 010-1234-5678

---

**마지막 업데이트**: 2026-02-08
