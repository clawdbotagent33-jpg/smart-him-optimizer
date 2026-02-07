"""API 스키마 정의 - camelCase for frontend compatibility"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


def to_camel(string: str) -> str:
    """snake_case를 camelCase로 변환"""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """camelCase 변환 기본 모델"""
    class Config:
        alias_generator = to_camel
        populate_by_name = True


# ========== 공통 스키마 ==========

class SuccessResponse(BaseModel):
    """성공 응답"""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """에러 응답"""
    success: bool = False
    error: str
    detail: Optional[str] = None


# ========== 인증 스키마 ==========

class LoginRequest(BaseModel):
    """로그인 요청"""
    username: str
    password: str


class TokenResponse(CamelModel):
    """토큰 응답"""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserBase(BaseModel):
    """사용자 기본 정보"""
    username: str
    email: str
    name: str
    role: str
    department: Optional[str] = None


class UserResponse(UserBase):
    """사용자 응답"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        alias_generator = to_camel
        populate_by_name = True


# ========== 입원/환자 스키마 ==========

class AdmissionBase(BaseModel):
    """입원 기본 정보"""
    admission_id: str
    admission_date: datetime
    discharge_date: Optional[datetime] = None
    department: str
    principal_diagnosis: str
    secondary_diagnoses: Optional[List[str]] = []
    procedures: Optional[List[str]] = []
    drg_code: Optional[str] = None
    drg_group: Optional[str] = None
    drg_weight: Optional[float] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class AdmissionCreate(AdmissionBase):
    """입원 정보 생성"""
    patient_id: Optional[str] = None
    clinical_notes: Optional[str] = None
    length_of_stay: Optional[int] = None


class AdmissionResponse(AdmissionBase):
    """입원 정보 응답"""
    id: int
    anonymous_id: Optional[str] = None
    length_of_stay: Optional[int] = None
    claim_amount: Optional[float] = None
    adjusted_amount: Optional[float] = None
    denial_reason: Optional[str] = None
    created_at: datetime


# ========== 예측 스키마 ==========

class GroupPredictionRequest(BaseModel):
    """그룹 예측 요청"""
    principal_diagnosis: str
    secondary_diagnoses: List[str] = []
    procedures: List[str] = []
    age: Optional[int] = None
    gender: Optional[str] = None
    department: Optional[str] = None
    length_of_stay: Optional[int] = None
    clinical_notes: Optional[str] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class GroupPredictionResponse(CamelModel):
    """그룹 예측 응답"""
    predicted_group: str
    confidence: float
    drg_code: Optional[str] = None
    upgrade_suggestions: Optional[List[str]] = None


class DenialRiskResponse(CamelModel):
    """삭감 위험도 응답"""
    risk_level: str
    risk_score: float
    denial_reasons: List[str] = []
    recommendations: List[str] = []


class PredictionResponse(CamelModel):
    """종합 예측 응답"""
    admission_id: Optional[str] = None
    group_prediction: GroupPredictionResponse
    denial_risk: DenialRiskResponse
    estimated_cmi: Optional[float] = None
    potential_cmi: Optional[float] = None
    revenue_impact: Optional[float] = None


# ========== 문서 스키마 ==========

class DocumentUploadResponse(CamelModel):
    """문서 업로드 응답"""
    document_id: int
    title: str
    doc_type: str
    chunks_created: int


class RAGQueryRequest(BaseModel):
    """RAG 쿼리 요청"""
    question: str
    context_type: Optional[str] = "general"
    use_llm: bool = True

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class RAGQueryResponse(CamelModel):
    """RAG 쿼리 응답"""
    question: str
    answer: Optional[str] = None
    sources: List[Dict[str, Any]]


class CDIQueryRequest(BaseModel):
    """CDI 쿼리 요청"""
    admission_id: str
    missing_items: List[str]
    urgency: str = "normal"

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class CDIQueryResponse(CamelModel):
    """CDI 쿼리 응답"""
    query_id: int
    query_text: str
    missing_items: List[str]
    status: str


# ========== 안전 사고 스키마 ==========

class SafetyIncidentRequest(BaseModel):
    """안전 사고 등록 요청"""
    admission_id: str
    incident_type: str
    severity: str
    description: str
    occurred_at: datetime
    current_drg_weight: Optional[float] = None

    class Config:
        alias_generator = to_camel
        populate_by_name = True


class SafetyIncidentResponse(CamelModel):
    """안전 사고 응답"""
    incident_id: int
    suggested_kcd_code: Optional[str] = None
    code_description: Optional[str] = None
    revenue_impact: float
    upgrade_suggestions: Optional[str] = None
    should_code: bool


# ========== 대시보드 스키마 ==========

class DashboardMetrics(CamelModel):
    """대시보드 지표"""
    total_admissions: int
    average_cmi: float
    group_distribution: Dict[str, int]
    denial_rate: float
    a_group_ratio: float


class CMIMetrics(CamelModel):
    """CMI 지표"""
    average_cmi: float
    median_cmi: Optional[float] = None
    cmi_by_group: Dict[str, float]
    total_cases: int
    group_distribution: Dict[str, int]
    trend_data: Optional[List[float]] = None


class DenialAnalytics(CamelModel):
    """삭감 분석"""
    denial_rate: float
    total_claims: int
    denied_count: int
    top_reasons: List[Dict[str, Any]]
    revenue_impact: float
    trend_data: Optional[List[float]] = None


# CSV 업로드 스키마

class CSVUploadResponse(CamelModel):
    """CSV 업로드 응답"""
    success: bool
    message: str
    rows_processed: int
    errors: List[str] = []
    warnings: List[str] = []
    statistics: Optional[Dict[str, Any]] = None
