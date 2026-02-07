# API 명세서

Smart HIM Optimizer REST API 명세

## 🔐 인증

모든 API 요청은 JWT 토큰 인증이 필요합니다 (일부 퍼블릭 엔드포인트 제외).

### 토큰 획득

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### 토큰 사용

```bash
Authorization: Bearer <access_token>
```

## 📊 인증 API

### 로그인

```http
POST /api/v1/auth/login
```

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "accessToken": "eyJhbGciOiJIUzI1NiIs...",
  "tokenType": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@him.local",
    "name": "시스템 관리자",
    "role": "admin",
    "department": "정보팀",
    "isActive": true,
    "createdAt": "2026-02-08T00:00:00"
  }
}
```

### 현재 사용자 정보

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### 로그아웃

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

## 🤖 예측 API

### 그룹 예측

K-DRG 그룹(A/B/C) 예측

```http
POST /api/v1/predictions/group
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "principalDiagnosis": "I50",
  "secondaryDiagnoses": ["E11", "I10"],
  "procedures": ["처치1"],
  "age": 65,
  "gender": "M",
  "department": "내과",
  "lengthOfStay": 5,
  "clinicalNotes": "심부전 증상"
}
```

**Response:**
```json
{
  "predictedGroup": "A",
  "confidence": 0.75,
  "drgCode": "A001",
  "upgradeSuggestions": [
    "합병증 상세 기록 추가",
    "중증도 등급 재평가"
  ]
}
```

### 삭감 위험 예측

```http
POST /api/v1/predictions/denial-risk
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "principalDiagnosis": "I50",
  "secondaryDiagnoses": ["E11"],
  "age": 65,
  "lengthOfStay": 5
}
```

**Response:**
```json
{
  "riskLevel": "LOW",
  "riskScore": 0.15,
  "denialReasons": [],
  "recommendations": ["기록完整性 확인"]
}
```

### 종합 예측

그룹 예측 + 삭감 위험 + 업그레이드 제안

```http
POST /api/v1/predictions/comprehensive
Authorization: Bearer <token>
Content-Type: application/json
```

**Query Parameters:**
- `admission_id` (optional): 입원 ID

**Request:**
```json
{
  "principalDiagnosis": "I50",
  "secondaryDiagnoses": ["E11"],
  "age": 65,
  "department": "내과",
  "lengthOfStay": 5
}
```

**Response:**
```json
{
  "admissionId": "temp",
  "groupPrediction": {
    "predictedGroup": "A",
    "confidence": 0.75,
    "drgCode": "A001",
    "upgradeSuggestions": ["합병증 상세 기록 추가"]
  },
  "denialRisk": {
    "riskLevel": "LOW",
    "riskScore": 0.15,
    "denialReasons": [],
    "recommendations": ["기록完整性 확인"]
  },
  "estimatedCmi": 1.0,
  "potentialCmi": 1.3,
  "revenueImpact": 300000
}
```

### 일괄 예측

```http
POST /api/v1/predictions/batch
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
[
  {
    "principalDiagnosis": "I50",
    "age": 65
  },
  {
    "principalDiagnosis": "A01",
    "age": 70
  }
]
```

**Response:**
```json
{
  "results": [
    {
      "admissionId": "batch_0",
      "predictedGroup": "B",
      "confidence": 0.6,
      "drgCode": "B001"
    }
  ],
  "count": 2
}
```

### 규정 준수 검증

```http
POST /api/v1/predictions/compliance
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "principalDiagnosis": "I50"
}
```

**Response:**
```json
{
  "isCompliant": true,
  "issues": [],
  "recommendations": []
}
```

## 🏥 입원 관리 API

### 입원 목록 조회

```http
GET /api/v1/admissions
Authorization: Bearer <token>
```

**Query Parameters:**
- `department` (optional): 부서 필터
- `startDate` (optional): 시작일 (YYYY-MM-DD)
- `endDate` (optional): 종료일 (YYYY-MM-DD)
- `page` (optional): 페이지 번호 (기본값: 1)
- `limit` (optional): 페이지 크기 (기본값: 20)

**Response:**
```json
[
  {
    "id": 1,
    "admissionId": "ADM001",
    "admissionDate": "2026-02-01T10:00:00",
    "department": "내과",
    "principalDiagnosis": "I50",
    "drgGroup": "A",
    "drgWeight": 1.3,
    "lengthOfStay": 5
  }
]
```

### 입원 상세 조회

```http
GET /api/v1/admissions/{admissionId}
Authorization: Bearer <token>
```

### CSV 업로드

```http
POST /api/v1/admissions/upload-csv
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request:**
- `file`: CSV 파일

**Response:**
```json
{
  "success": true,
  "message": "CSV 업로드 완료",
  "rowsProcessed": 100,
  "errors": [],
  "warnings": ["일부 필드 누락"]
}
```

## 📈 대시보드 API

### 요약 통계

```http
GET /api/v1/dashboard/summary
Authorization: Bearer <token>
```

**Query Parameters:**
- `department` (optional): 부서 필터
- `days` (optional): 조회 기간 (기본값: 30)

**Response:**
```json
{
  "totalAdmissions": 200,
  "averageCmi": 1.15,
  "groupDistribution": {
    "A": 45,
    "B": 120,
    "C": 35
  },
  "denialRate": 8.5,
  "aGroupRatio": 22.5
}
```

### 그룹 분포 추이

```http
GET /api/v1/dashboard/group-distribution
Authorization: Bearer <token>
```

**Response:**
```json
{
  "dates": ["2026-01-08", "2026-01-09", "..."],
  "series": {
    "A": [1, 2, 3],
    "B": [3, 4, 5],
    "C": [1, 1, 2]
  }
}
```

### 상위 진단

```http
GET /api/v1/dashboard/top-diagnoses
Authorization: Bearer <token>
```

**Query Parameters:**
- `limit` (optional): 반환 개수 (기본값: 10)
- `days` (optional): 조회 기간

**Response:**
```json
[
  {
    "diagnosisCode": "I50",
    "diagnosisName": "심부전",
    "count": 25,
    "percentage": 12.5
  }
]
```

## 📄 문서 관리 API

### 문서 업로드

```http
POST /api/v1/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Request:**
- `file`: PDF/Word/Excel 파일
- `docType`: 문서 유형 (manual, guideline, memo)

**Response:**
```json
{
  "documentId": 1,
  "title": "K-DRG v4.7 가이드",
  "docType": "guideline",
  "chunksCreated": 10
}
```

### 문서 검색 (RAG)

```http
POST /api/v1/documents/query
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**
```json
{
  "question": "심부전의 K-DRG 분류 기준은?",
  "contextType": "general",
  "useLlm": true
}
```

**Response:**
```json
{
  "question": "심부전의 K-DRG 분류 기준은?",
  "answer": "심부전(I50)은 주로 순환기계 질환으로 분류되며...",
  "sources": [
    {
      "documentId": 1,
      "title": "K-DRG v4.7 가이드",
      "content": "관련 내용...",
      "score": 0.95
    }
  ]
}
```

## ❌ 에러 응답

### 에러 형식

```json
{
  "success": false,
  "error": "에러 메시지",
  "statusCode": 400,
  "details": {
    "field": ["에러 상세"]
  }
}
```

### HTTP 상태 코드

| 코드 | 의미 | 설명 |
|------|------|------|
| 200 | OK | 요청 성공 |
| 201 | Created | 생성 성공 |
| 400 | Bad Request | 잘못된 요청 |
| 401 | Unauthorized | 인증 실패 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 422 | Validation Error | 유효성 검증 실패 |
| 500 | Internal Server Error | 서버 오류 |

## 📊 메트릭 엔드포인트

### Prometheus 메트릭

```http
GET /metrics
```

**Response:** (Prometheus 형식)
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/dashboard/summary",status_code="200"} 42

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{method="GET",endpoint="/api/v1/dashboard/summary",le="0.1"} 38
```

## 🔍 헬스 체크

```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "appName": "Smart HIM Optimizer 2026",
  "version": "1.0.0"
}
```

---

**API 버전**: 1.0.0  
**마지막 업데이트**: 2026-02-08
