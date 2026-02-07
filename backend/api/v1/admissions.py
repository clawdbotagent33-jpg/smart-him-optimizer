"""입원 관리 API 엔드포인트 - 테스트용 (인증 없음)"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional
import io
import uuid
from datetime import datetime

from api.schemas import (
    AdmissionCreate,
    AdmissionResponse,
    CSVUploadResponse,
    SafetyIncidentRequest,
    SafetyIncidentResponse,
    CDIQueryRequest,
    CDIQueryResponse,
)

router = APIRouter()

# 메모리 저장소
MEMORY_ADMISSIONS = {}
MEMORY_PATIENTS = {}
MEMORY_INCIDENTS = {}
MEMORY_CDI_QUERIES = {}


@router.post("/admissions/upload-csv", response_model=CSVUploadResponse)
async def upload_admissions_csv(
    file: UploadFile = File(...),
):
    """CSV 파일 업로드로 입원 데이터 일괄 등록"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV 파일만 업로드 가능합니다"
        )

    try:
        # 파일 읽기
        content = await file.read()
        text_content = content.decode('utf-8')

        # 간단 CSV 파싱
        lines = text_content.strip().split('\n')
        headers = [h.strip() for h in lines[0].split(',')]

        saved_count = 0
        for line in lines[1:]:
            values = [v.strip() for v in line.split(',')]
            if len(values) < 3:
                continue

            # 환자 및 입원 데이터 생성
            admission_id = str(uuid.uuid4())
            patient_id = str(uuid.uuid4())

            patient_data = {
                "id": patient_id,
                "anonymous_id": f"PAT-{patient_id[:8]}",
                "gender": values[0] if len(values) > 0 else "M",
                "age": int(values[1]) if len(values) > 1 and values[1].isdigit() else 50,
            }
            MEMORY_PATIENTS[patient_id] = patient_data

            admission_data = {
                "id": admission_id,
                "admission_id": admission_id,
                "patient_id": patient_id,
                "admission_date": datetime.now(),
                "department": values[2] if len(values) > 2 else "내과",
                "principal_diagnosis": values[3] if len(values) > 3 else "A01",
                "drg_group": "B",
                "drg_weight": 1.0,
            }
            MEMORY_ADMISSIONS[admission_id] = admission_data
            saved_count += 1

        return CSVUploadResponse(
            success=True,
            message=f"총 {saved_count}건의 입원 데이터를 처리했습니다",
            rows_processed=saved_count,
            warnings=[],
            statistics={"total": saved_count}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 처리 중 오류 발생: {str(e)}"
        )


@router.get("/admissions/{admission_id}", response_model=AdmissionResponse)
async def get_admission(
    admission_id: str,
):
    """입원 상세 조회"""
    if admission_id not in MEMORY_ADMISSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="입원 기록을 찾을 수 없습니다"
        )

    data = MEMORY_ADMISSIONS[admission_id]
    return AdmissionResponse(
        id=data["id"],
        admission_id=data["admission_id"],
        patient_id=data["patient_id"],
        admission_date=data.get("admission_date"),
        department=data.get("department"),
        principal_diagnosis=data.get("principal_diagnosis"),
        drg_group=data.get("drg_group"),
        drg_weight=data.get("drg_weight", 1.0),
    )


@router.get("/admissions", response_model=List[AdmissionResponse])
async def list_admissions(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    drg_group: Optional[str] = None,
):
    """입원 목록 조회"""
    admissions = list(MEMORY_ADMISSIONS.values())

    if department:
        admissions = [a for a in admissions if a.get("department") == department]
    if drg_group:
        admissions = [a for a in admissions if a.get("drg_group") == drg_group]

    admissions = admissions[skip:skip + limit]

    return [
        AdmissionResponse(
            id=a["id"],
            admission_id=a["admission_id"],
            patient_id=a["patient_id"],
            admission_date=a.get("admission_date"),
            department=a.get("department"),
            principal_diagnosis=a.get("principal_diagnosis"),
            drg_group=a.get("drg_group"),
            drg_weight=a.get("drg_weight", 1.0),
        )
        for a in admissions
    ]


@router.post("/admissions/safety-incident", response_model=SafetyIncidentResponse)
async def report_safety_incident(
    request: SafetyIncidentRequest,
):
    """안전 사고 보고 및 수익 영향 분석"""

    incident_id = str(uuid.uuid4())
    incident = {
        "id": incident_id,
        "admission_id": request.admission_id,
        "incident_type": request.incident_type,
        "severity": request.severity,
        "description": request.description,
        "occurred_at": request.occurred_at,
        "suggested_kcd_code": "W10",  # 낙상 - 예시
        "revenue_impact": -500000,  # 예상 손실
    }
    MEMORY_INCIDENTS[incident_id] = incident

    return SafetyIncidentResponse(
        incident_id=incident_id,
        suggested_kcd_code="W10",
        revenue_impact=-500000,
        upgrade_suggestions="낙상 관련 합병증 코드 추가 기록 권장"
    )


@router.post("/admissions/cdi-query", response_model=CDIQueryResponse)
async def create_cdi_query(
    request: CDIQueryRequest,
):
    """CDI 쿼리 생성"""

    query_id = str(uuid.uuid4())
    query_text = f"[CDI 쿼리] 다음 항목의 추가 기록을 요청합니다: {', '.join(request.missing_items)}"

    cdi_query = {
        "id": query_id,
        "admission_id": request.admission_id,
        "query_text": query_text,
        "missing_items": request.missing_items,
        "status": "pending",
        "urgency": request.urgency,
    }
    MEMORY_CDI_QUERIES[query_id] = cdi_query

    return CDIQueryResponse(
        query_id=query_id,
        query_text=query_text,
        missing_items=request.missing_items,
        status="pending"
    )
