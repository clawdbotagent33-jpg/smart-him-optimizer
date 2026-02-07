"""데이터베이스 모델 정의"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database.base import Base


class UserRole(str, enum.Enum):
    """사용자 역할"""
    ADMIN = "admin"
    HIM_MANAGER = "him_manager"  # 보건의료정보관리사
    DOCTOR = "doctor"
    NURSE = "nurse"
    VIEWER = "viewer"


class DRGGroup(str, enum.Enum):
    """K-DRG 그룹"""
    GROUP_A = "A"  # 전문질병군
    GROUP_B = "B"  # 일반질병군
    GROUP_C = "C"  # 심층질병군


class User(Base):
    """사용자 모델"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(50), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    department = Column(String(100))
    license_number = Column(String(50))  # 보건의료정보관리사 자격증 번호
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)

    # 관계
    audit_logs = relationship("AuditLog", back_populates="user")
    cdi_queries = relationship("CDIQuery", back_populates="created_by_user")


class Patient(Base):
    """환자 모델 (비식별화)"""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    anonymous_id = Column(String(50), unique=True, nullable=False, index=True)  # 비식별화 ID
    original_id_hash = Column(String(64), unique=True, nullable=False)  # 원본 ID 해시
    gender = Column(String(10))  # M/F
    age = Column(Integer)
    admission_date = Column(DateTime, nullable=False)
    discharge_date = Column(DateTime)
    department = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    admissions = relationship("Admission", back_populates="patient")


class Admission(Base):
    """입원 기록 모델"""
    __tablename__ = "admissions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    admission_id = Column(String(50), unique=True, nullable=False, index=True)
    admission_date = Column(DateTime, nullable=False)
    discharge_date = Column(DateTime)
    length_of_stay = Column(Integer)  # 재원일수

    # 진단 정보
    principal_diagnosis = Column(String(20))  # 주진단 KCD-9 코드
    secondary_diagnoses = Column(JSON)  # 부진단 목록
    procedures = Column(JSON)  # 처치 목록

    # K-DRG 정보
    drg_code = Column(String(20))  # K-DRG 코드
    drg_group = Column(Enum(DRGGroup))  # A/B/C 그룹
    drg_weight = Column(Float)  # CMI 가중치
    relative_weight = Column(Float)

    # 검사 정보
    lab_results = Column(JSON)  # 검사 결과
    vital_signs = Column(JSON)  # 생체 징후

    # 안전 지표
    safety_incidents = Column(JSON)  # 낙상, 감염 등 안전 사고

    # 청구 정보
    claim_amount = Column(Float)
    adjusted_amount = Column(Float)  # 심평원 조정 금액
    denial_reason = Column(Text)  # 삭감 사유

    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 관계
    patient = relationship("Patient", back_populates="admissions")
    predictions = relationship("Prediction", back_populates="admission")
    cdi_queries = relationship("CDIQuery", back_populates="admission")


class Prediction(Base):
    """AI 예측 결과 모델"""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=False)

    # 예측 유형
    prediction_type = Column(String(50), nullable=False)  # a_group, denial, clinical_entity

    # 예측 결과
    predicted_value = Column(JSON)  # 예측 값
    confidence = Column(Float)  # 신뢰도
    explanation = Column(JSON)  # XAI 설명 (SHAP 값 등)

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    admission = relationship("Admission", back_populates="predictions")


class CDIQuery(Base):
    """CDI(Clinical Documentation Improvement) 쿼리 모델"""
    __tablename__ = "cdi_queries"

    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 쿼리 내용
    query_type = Column(String(50))  # missing_diagnosis, clarification, etc.
    subject = Column(String(200))
    message = Column(Text, nullable=False)
    suggested_documentation = Column(Text)

    # 상태
    status = Column(String(20), default="pending")  # pending, responded, resolved

    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    responded_at = Column(DateTime)
    resolved_at = Column(DateTime)

    # 관계
    admission = relationship("Admission", back_populates="cdi_queries")
    created_by_user = relationship("User", back_populates="cdi_queries")


class Document(Base):
    """문서 모델 (RAG 학습 데이터)"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_type = Column(String(50), nullable=False)  # manual, guideline, memo, etc.
    title = Column(String(200))
    content = Column(Text, nullable=False)
    doc_metadata = Column(JSON)  # 'metadata'는 예약어라 변경
    vector_id = Column(String(100))  # ChromaDB 벡터 ID

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """감사 로그 모델"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    details = Column(JSON)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계
    user = relationship("User", back_populates="audit_logs")


class SafetyIncident(Base):
    """환자 안전 사고 모델"""
    __tablename__ = "safety_incidents"

    id = Column(Integer, primary_key=True, index=True)
    admission_id = Column(Integer, ForeignKey("admissions.id"))
    incident_type = Column(String(50))  # fall, infection, pressure_ulcer, etc.
    severity = Column(String(20))  # mild, moderate, severe
    description = Column(Text)
    occurred_at = Column(DateTime)

    # 코딩 연계
    suggested_kcd_code = Column(String(20))
    is_coded = Column(Boolean, default=False)
    revenue_impact = Column(Float)  # 예상 수익 영향

    created_at = Column(DateTime, default=datetime.utcnow)
