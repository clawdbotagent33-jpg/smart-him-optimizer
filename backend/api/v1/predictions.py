"""AI 예측 API 엔드포인트"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.schemas import (
    GroupPredictionRequest,
    GroupPredictionResponse,
    DenialRiskResponse,
    PredictionResponse,
)
from services.prediction_service import prediction_service

router = APIRouter()


@router.post("/predictions/group", response_model=GroupPredictionResponse)
async def predict_group(
    request: GroupPredictionRequest,
):
    """K-DRG 그룹 예측 (A/B/C)"""
    try:
        admission_data = {
            "principal_diagnosis": request.principal_diagnosis,
            "secondary_diagnoses": request.secondary_diagnoses or [],
            "procedures": request.procedures or [],
            "age": request.age,
            "gender": request.gender,
            "department": request.department,
            "length_of_stay": request.length_of_stay,
            "clinical_notes": request.clinical_notes or "",
        }

        prediction = prediction_service.predict_group(admission_data)

        return GroupPredictionResponse(
            predicted_group=prediction["predicted_group"],
            confidence=prediction["confidence"],
            drg_code=prediction["drg_code"],
            upgrade_suggestions=[
                s["description"] for s in prediction.get("upgrade_suggestions", [])
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"예측 중 오류 발생: {str(e)}",
        )


@router.post("/predictions/denial-risk", response_model=DenialRiskResponse)
async def predict_denial_risk(
    request: GroupPredictionRequest,
):
    """청구 삭감 위험도 예측"""
    try:
        admission_data = {
            "principal_diagnosis": request.principal_diagnosis,
            "secondary_diagnoses": request.secondary_diagnoses or [],
            "procedures": request.procedures or [],
            "age": request.age,
            "gender": request.gender,
            "department": request.department,
            "length_of_stay": request.length_of_stay,
        }

        result = prediction_service.predict_denial_risk(admission_data)

        return DenialRiskResponse(
            risk_level=result["risk_level"],
            risk_score=result["denial_probability"],
            denial_reasons=result["risk_factors"],
            recommendations=result["recommendations"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"위험도 예측 중 오류 발생: {str(e)}",
        )


@router.post("/predictions/comprehensive", response_model=PredictionResponse)
async def predict_comprehensive(
    request: GroupPredictionRequest,
    admission_id: str = None,
):
    """종합 예측 (그룹 + 삭감 위험 + 업그레이드 제안)"""
    try:
        admission_data = {
            "admission_id": admission_id,
            "principal_diagnosis": request.principal_diagnosis,
            "secondary_diagnoses": request.secondary_diagnoses or [],
            "procedures": request.procedures or [],
            "age": request.age,
            "gender": request.gender,
            "department": request.department,
            "length_of_stay": request.length_of_stay,
            "clinical_notes": request.clinical_notes or "",
        }

        # 종합 예측
        result = prediction_service.predict_comprehensive(admission_data)

        return PredictionResponse(
            admission_id=admission_id or "temp",
            group_prediction=GroupPredictionResponse(
                predicted_group=result["group_prediction"]["predicted_group"],
                confidence=result["group_prediction"]["confidence"],
                drg_code=result["group_prediction"]["drg_code"],
                upgrade_suggestions=[
                    s["description"]
                    for s in result["group_prediction"].get("upgrade_suggestions", [])
                ],
            ),
            denial_risk=DenialRiskResponse(
                risk_level=result["denial_risk"]["risk_level"],
                risk_score=result["denial_risk"]["denial_probability"],
                denial_reasons=result["denial_risk"]["risk_factors"],
                recommendations=result["denial_risk"]["recommendations"],
            ),
            estimated_cmi=result["estimated_cmi"],
            potential_cmi=result["potential_cmi"],
            revenue_impact=result["revenue_impact"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"종합 예측 중 오류 발생: {str(e)}",
        )


@router.post("/predictions/batch")
async def batch_predict(
    requests: List[GroupPredictionRequest],
):
    """다수 입원 건 일괄 예측"""
    try:
        results = []
        for i, req in enumerate(requests):
            admission_data = {
                "admission_id": f"batch_{i}",
                "principal_diagnosis": req.principal_diagnosis,
                "secondary_diagnoses": req.secondary_diagnoses or [],
                "procedures": req.procedures or [],
                "age": req.age,
                "gender": req.gender,
                "department": req.department,
                "length_of_stay": req.length_of_stay,
                "clinical_notes": req.clinical_notes or "",
            }

            pred = prediction_service.predict_group(admission_data)
            results.append(
                {
                    "admission_id": f"batch_{i}",
                    "predicted_group": pred["predicted_group"],
                    "confidence": pred["confidence"],
                    "drg_code": pred["drg_code"],
                }
            )

        return {"results": results, "count": len(results)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일괄 예측 중 오류 발생: {str(e)}",
        )


@router.post("/predictions/compliance")
async def check_compliance(
    request: GroupPredictionRequest,
):
    """KCD-9 규정 준수 검증"""
    try:
        diagnosis = request.principal_diagnosis

        # 간단 규정 준수 검사
        issues = []
        if len(diagnosis) < 3:
            issues.append("진단 코드가 3자리 미만입니다")

        return {
            "is_compliant": len(issues) == 0,
            "issues": issues,
            "recommendations": ["진단 코드 정확성 확인"] if issues else [],
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"규정 준수 검증 중 오류 발생: {str(e)}",
        )
