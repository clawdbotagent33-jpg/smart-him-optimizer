"""대시보드 API 엔드포인트 - 테스트용 (인증 없음)"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime, timedelta

from api.schemas import DashboardMetrics, CMIMetrics, DenialAnalytics

router = APIRouter()


@router.get("/dashboard/summary", response_model=DashboardMetrics)
async def get_dashboard_summary(
    department: Optional[str] = None,
    days: int = 30
):
    """대시보드 요약 지표"""
    try:
        # 간단한 샘플 데이터 반환
        group_dist = {'A': 45, 'B': 120, 'C': 35}
        total_cases = sum(group_dist.values())
        a_group_ratio = (group_dist['A'] / total_cases * 100) if total_cases > 0 else 0

        return DashboardMetrics(
            total_admissions=total_cases,
            average_cmi=1.15,
            group_distribution=group_dist,
            denial_rate=8.5,
            a_group_ratio=round(a_group_ratio, 2)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"대시보드 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get("/dashboard/cmi", response_model=CMIMetrics)
async def get_cmi_metrics(
    department: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """CMI 지표 조회"""
    try:
        return CMIMetrics(
            average_cmi=1.15,
            median_cmi=1.08,
            cmi_by_group={'A': 1.85, 'B': 0.95, 'C': 0.65},
            total_cases=200,
            group_distribution={'A': 45, 'B': 120, 'C': 35},
            trend_data=[1.1, 1.12, 1.15, 1.13, 1.15, 1.18, 1.15]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"CMI 지표 조회 중 오류 발생: {str(e)}"
        )


@router.get("/dashboard/denials", response_model=DenialAnalytics)
async def get_denial_analytics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """삭감 분석 조회"""
    try:
        return DenialAnalytics(
            denial_rate=8.5,
            total_claims=200,
            denied_count=17,
            top_reasons=[
                {"reason": "진단 코드 불명확", "count": 7},
                {"reason": "기록 부족", "count": 5},
                {"reason": "중증도 부족", "count": 3}
            ],
            revenue_impact=-8500000,
            trend_data=[10, 9, 8.5, 8, 8.5]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"삭감 분석 조회 중 오류 발생: {str(e)}"
        )


@router.get("/dashboard/group-distribution")
async def get_group_distribution(
    department: Optional[str] = None,
    days: int = 30
):
    """그룹별 분포 시계열 데이터"""
    # 샘플 시계열 데이터
    dates = []
    series = {'A': [], 'B': [], 'C': []}

    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        dates.append(date)
        series['A'].append(1 + (i % 5))
        series['B'].append(3 + (i % 7))
        series['C'].append(1 + (i % 3))

    return {
        "dates": dates,
        "series": series
    }


@router.get("/dashboard/top-diagnoses")
async def get_top_diagnoses(
    limit: int = 10,
    days: int = 30
):
    """상위 진단별 통계"""
    return {
        "diagnoses": [
            {"code": "I10", "count": 25, "avg_weight": 0.95},
            {"code": "J18", "count": 18, "avg_weight": 1.1},
            {"code": "E11", "count": 15, "avg_weight": 1.05},
            {"code": "I50", "count": 12, "avg_weight": 1.35},
            {"code": "N18", "count": 10, "avg_weight": 1.2},
        ]
    }


@router.get("/dashboard/performance-metrics")
async def get_performance_metrics(
    days: int = 30
):
    """성과 지표 (복지부 지원사업 기준)"""
    return {
        "period_days": days,
        "metrics": {
            "a_group_conversion_rate": {
                "value": 12.5,
                "target": 15,
                "unit": "%",
                "status": "improving"
            },
            "coding_compliance_rate": {
                "value": 95.2,
                "target": 98,
                "unit": "%",
                "status": "stable"
            },
            "denial_reduction_rate": {
                "value": -18.5,
                "target": -20,
                "unit": "%",
                "status": "improving"
            },
            "query_response_time": {
                "value": 4.2,
                "target": 4.0,
                "unit": "시간",
                "status": "stable"
            }
        }
    }
