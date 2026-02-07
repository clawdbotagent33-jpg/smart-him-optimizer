"""HIM(HIM) 관련 비즈니스 로직 서비스"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from database.models import Admission, Patient, Prediction, CDIQuery
from database.base import AsyncSessionLocal
from models.predictors import a_group_classifier, denial_predictor, clinical_entity_extractor
from rag.retriever import rag_retriever
from core.config import settings


class HIMService:
    """보건의료정보관리 서비스"""

    def __init__(self):
        self.a_group_classifier = a_group_classifier
        self.denial_predictor = denial_predictor
        self.entity_extractor = clinical_entity_extractor
        self.rag_retriever = rag_retriever

    async def predict_admission_outcome(
        self,
        admission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """입원 건에 대한 종합 예측"""
        results = {}

        # 1. A그룹 전환 가능성 예측
        group_prediction = self.a_group_classifier.predict(admission_data)
        results['group_prediction'] = group_prediction

        # 2. 삭감 위험도 예측
        denial_risk = self.denial_predictor.predict_risk(admission_data)
        results['denial_risk'] = denial_risk

        # 3. 임상적 엔티티 추출
        clinical_text = admission_data.get('clinical_notes', '')
        if clinical_text:
            diagnoses = self.entity_extractor.extract_diagnoses(clinical_text)
            procedures = self.entity_extractor.extract_procedures(clinical_text)
            results['extracted_entities'] = {
                'diagnoses': diagnoses,
                'procedures': procedures
            }

        # 4. A그룹 전환 제안 (RAG)
        if group_prediction['a_group_probability'] < settings.A_GROUP_THRESHOLD:
            upgrade_suggestions = await self.rag_retriever.suggest_a_group_upgrade(
                principal_diagnosis=admission_data.get('principal_diagnosis', ''),
                secondary_diagnoses=admission_data.get('secondary_diagnoses', []),
                procedures=admission_data.get('procedures', []),
                current_group=admission_data.get('drg_group', 'B')
            )
            results['upgrade_suggestions'] = upgrade_suggestions

        # 5. 종합 권고사항
        results['recommendations'] = self._generate_recommendations(results)

        return results

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """종합 권고사항 생성"""
        recommendations = []

        # A그룹 전환 권고
        group_pred = results.get('group_prediction', {})
        if group_pred.get('can_upgrade'):
            recommendations.append(
                f"A그룹 전환 가능성 있음 ({group_pred.get('a_group_probability', 0)*100:.1f}%)"
            )

        # 삭감 위험 경고
        denial_risk = results.get('denial_risk', {})
        if denial_risk.get('risk_level') == 'HIGH':
            recommendations.append(
                f"삭감 위험도 높음 ({denial_risk.get('denial_probability', 0)*100:.1f}%)"
            )

        # 누락 문서화 경고
        risk_factors = denial_risk.get('risk_factors', [])
        if risk_factors:
            recommendations.extend([f"위험 요인: {rf}" for rf in risk_factors])

        return recommendations

    async def generate_cdi_query(
        self,
        admission_id: str,
        missing_items: List[str],
        urgency: str = "normal"
    ) -> Dict[str, Any]:
        """CDI 쿼리 생성"""
        query_data = await self.rag_retriever.generate_cdi_query(
            admission_id=admission_id,
            missing_items=missing_items,
            urgency=urgency
        )

        return query_data

    async def analyze_safety_incident_impact(
        self,
        incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """안전 사고의 수익 영향 분석"""
        incident_type = incident_data.get('incident_type')

        # 사고 유형별 진단코드 매핑
        incident_codes = {
            'fall': {'code': 'W00-W19', 'description': '낙상 관련 진단'},
            'pressure_ulcer': {'code': 'L89', 'description': '욕창'},
            'infection': {'code': 'T80-T88', 'description': '감염 합병증'},
            'medication_error': {'code': 'T36-T50', 'description': '약물 부작용'},
        }

        code_info = incident_codes.get(incident_type, {})

        # DRG 가중치 영향 분석 (간단 구현)
        base_weight = incident_data.get('current_drg_weight', 1.0)
        potential_weight = base_weight * 1.2  # 합병증 추가 시 약 20% 증가 가정

        revenue_impact = (potential_weight - base_weight) * 1000000  # 예상

        return {
            'incident_type': incident_type,
            'suggested_kcd_code': code_info.get('code'),
            'code_description': code_info.get('description'),
            'current_drg_weight': base_weight,
            'potential_drg_weight': potential_weight,
            'revenue_impact': revenue_impact,
            'should_code': revenue_impact > 50000  # 5만원 이상이면 코딩 권고
        }

    async def batch_predict_admissions(
        self,
        admissions_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """다수 입원 건 일괄 예측"""
        results = []

        for admission_data in admissions_data:
            try:
                prediction = await self.predict_admission_outcome(admission_data)
                prediction['admission_id'] = admission_data.get('admission_id')
                results.append(prediction)
            except Exception as e:
                results.append({
                    'admission_id': admission_data.get('admission_id'),
                    'error': str(e)
                })

        return results

    async def get_compliance_report(
        self,
        admission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """규정 준수 보고서 생성"""
        diagnosis_codes = [admission_data.get('principal_diagnosis', '')]
        diagnosis_codes.extend(admission_data.get('secondary_diagnoses', []))

        compliance_check = await self.rag_retriever.check_compliance(
            diagnosis_codes=diagnosis_codes,
            documentation=admission_data.get('clinical_notes', '')
        )

        return {
            'admission_id': admission_data.get('admission_id'),
            'is_compliant': compliance_check.get('is_compliant', True),
            'compliance_report': compliance_check.get('compliance_report', ''),
            'suggested_codes': compliance_check.get('suggested_codes', [])
        }

    async def calculate_cmi_metrics(
        self,
        department: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """CMI 지표 계산"""
        async with AsyncSessionLocal() as session:
            query = session.query(Admission)

            if department:
                query = query.filter(Admission.department == department)
            if start_date:
                query = query.filter(Admission.admission_date >= start_date)
            if end_date:
                query = query.filter(Admission.admission_date <= end_date)

            admissions = await query.all()

            if not admissions:
                return {
                    'total_cases': 0,
                    'average_cmi': 0,
                    'group_distribution': {}
                }

            total_weight = sum([adm.drg_weight or 0 for adm in admissions])
            avg_cmi = total_weight / len(admissions)

            group_dist = {}
            for adm in admissions:
                group = adm.drg_group or 'Unknown'
                group_dist[group] = group_dist.get(group, 0) + 1

            return {
                'total_cases': len(admissions),
                'average_cmi': avg_cmi,
                'group_distribution': group_dist,
                'total_weight': total_weight
            }

    async def get_denial_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """삭감 분석"""
        async with AsyncSessionLocal() as session:
            query = session.query(Admission).filter(
                Admission.denial_reason.isnot(None),
                Admission.denial_reason != ''
            )

            if start_date:
                query = query.filter(Admission.admission_date >= start_date)
            if end_date:
                query = query.filter(Admission.admission_date <= end_date)

            denied_claims = await query.all()

            # 사유별 집계
            denial_reasons = {}
            total_denied_amount = 0

            for claim in denied_claims:
                reason = claim.denial_reason or 'Unknown'
                denial_reasons[reason] = denial_reasons.get(reason, 0) + 1
                if claim.claim_amount and claim.adjusted_amount:
                    total_denied_amount += (claim.claim_amount - claim.adjusted_amount)

            return {
                'total_denied_claims': len(denied_claims),
                'denial_reasons': denial_reasons,
                'total_denied_amount': total_denied_amount,
                'denial_rate': len(denied_claims) / max(len(denied_claims), 1) * 100
            }


# 전역 인스턴스
him_service = HIMService()
