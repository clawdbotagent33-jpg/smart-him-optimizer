"""예측 서비스 - ML 모델 통합"""

import time
from typing import Dict, Any, Optional

from models.predictors import a_group_classifier, denial_predictor
from core.config import settings
from core.logging_config import get_logger, log_prediction
from core.monitoring import record_prediction, record_prediction_latency

logger = get_logger(__name__)


class PredictionService:
    """예측 서비스 - ML 모델 및 규칙 기반 예측 통합"""

    def __init__(self):
        self.models_loaded = False
        self.use_ml = False
        self._load_models()

    def _load_models(self):
        """ML 모델 로드 시도"""
        try:
            # A그룹 분류 모델 로드
            if a_group_classifier.load_model():
                logger.info("A그룹 분류 모델 로드 성공")
                self.use_ml = True
            else:
                logger.warning("A그룹 분류 모델 로드 실패 - 규칙 기반 예측 사용")

            # 삭감 예측 모델 로드
            if denial_predictor.load_model():
                logger.info("삭감 예측 모델 로드 성공")
            else:
                logger.warning("삭감 예측 모델 로드 실패 - 규칙 기반 예측 사용")

            self.models_loaded = True
        except Exception as e:
            logger.error(f"모델 로드 중 오류: {e}")
            self.use_ml = False

    def predict_group(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """K-DRG 그룹 예측"""
        start_time = time.time()

        if self.use_ml and a_group_classifier.model is not None:
            try:
                result = self._predict_with_ml(data)
            except Exception as e:
                logger.warning(f"ML 예측 실패, 규칙 기반으로 전환: {e}")
                result = self._predict_with_rules(data)
        else:
            result = self._predict_with_rules(data)

        # 모니터링 데이터 기록
        latency = time.time() - start_time
        record_prediction("group", result["predicted_group"])
        record_prediction_latency("group", latency)

        log_prediction(
            logger,
            admission_id=data.get("admission_id", "unknown"),
            predicted_group=result["predicted_group"],
            confidence=result["confidence"],
            latency_ms=latency * 1000,
            method="ml" if self.use_ml else "rules",
        )

        return result

    def _predict_with_ml(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """ML 모델로 예측"""
        result = a_group_classifier.predict(data)

        predicted_group = result.get("predicted_group", "B")
        confidence = result.get("confidence", 0.6)
        probabilities = result.get("probabilities", {})

        return {
            "predicted_group": predicted_group,
            "confidence": confidence,
            "drg_code": f"{predicted_group}001",
            "a_group_probability": probabilities.get("A", 0.0),
            "can_upgrade": probabilities.get("A", 0.0) >= settings.A_GROUP_THRESHOLD,
            "upgrade_suggestions": self._get_upgrade_suggestions(
                predicted_group, data.get("principal_diagnosis", "")
            ),
        }

    def _predict_with_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """규칙 기반 예측 (Fallback)"""
        diagnosis = data.get("principal_diagnosis", "")

        # 간단 규칙: 특정 진단 코드는 A그룹
        if diagnosis.startswith(("A1", "A2", "A3", "B1", "B2")):
            predicted_group = "A"
            confidence = 0.75
        elif diagnosis.startswith(("C1", "C2", "D1")):
            predicted_group = "C"
            confidence = 0.65
        else:
            predicted_group = "B"
            confidence = 0.60

        # A그룹 전환 가능성 계산
        a_group_probability = (
            0.3 if predicted_group == "B" else 0.1 if predicted_group == "C" else 0.9
        )

        return {
            "predicted_group": predicted_group,
            "confidence": confidence,
            "drg_code": f"{predicted_group}001",
            "a_group_probability": a_group_probability,
            "can_upgrade": a_group_probability >= settings.A_GROUP_THRESHOLD,
            "upgrade_suggestions": self._get_upgrade_suggestions(
                predicted_group, diagnosis
            ),
        }

    def _get_upgrade_suggestions(self, current_group: str, diagnosis: str) -> list:
        """업그레이드 제안 생성"""
        suggestions = []

        if current_group == "B":
            suggestions = [
                {
                    "type": "documentation",
                    "priority": "high",
                    "description": "합병증 상세 기록 추가",
                    "expected_impact": 0.15,
                },
                {
                    "type": "diagnosis",
                    "priority": "medium",
                    "description": "중증도 등급 재평가",
                    "expected_impact": 0.10,
                },
                {
                    "type": "procedure",
                    "priority": "medium",
                    "description": "수술/처치 기록 확인",
                    "expected_impact": 0.08,
                },
            ]
        elif current_group == "C":
            suggestions = [
                {
                    "type": "diagnosis",
                    "priority": "high",
                    "description": "주진단 세부화",
                    "expected_impact": 0.12,
                },
                {
                    "type": "documentation",
                    "priority": "medium",
                    "description": "동반질환 기록 강화",
                    "expected_impact": 0.08,
                },
            ]

        return suggestions

    def predict_denial_risk(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """청구 삭감 위험도 예측"""
        if self.use_ml and denial_predictor.model is not None:
            try:
                return denial_predictor.predict_risk(data)
            except Exception as e:
                logger.warning(f"ML 삭감 예측 실패, 규칙 기반으로 전환: {e}")

        return self._predict_denial_with_rules(data)

    def _predict_denial_with_rules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """규칙 기반 삭감 위험 예측"""
        diagnosis = data.get("principal_diagnosis", "")

        risk_score = 0.0
        risk_factors = []

        # 주진단 누락
        if not diagnosis:
            risk_score += 0.3
            risk_factors.append("주진단 미기재")

        # 진단 코드 길이
        if len(diagnosis) < 3:
            risk_score += 0.2
            risk_factors.append("진단 코드 불명확")

        # 재원일수
        los = data.get("length_of_stay", 0)
        if los < 1 or los > 365:
            risk_score += 0.2
            risk_factors.append(f"비정상 재원일수: {los}일")

        # 위험도 레벨
        if risk_score >= 0.7:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "denial_probability": min(risk_score, 1.0),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendations": self._get_denial_recommendations(risk_factors),
        }

    def _get_denial_recommendations(self, risk_factors: list) -> list:
        """삭감 방지 권고사항 생성"""
        recommendations = []

        if any("진단" in factor for factor in risk_factors):
            recommendations.append("진단 코드 정확성 확인")

        if any("재원" in factor for factor in risk_factors):
            recommendations.append("입퇴원일자 확인")

        if not recommendations:
            recommendations.append("기록完整性 확인")

        return recommendations

    def predict_comprehensive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """종합 예측 (그룹 + 삭감 위험 + 업그레이드 제안)"""
        # 그룹 예측
        group_pred = self.predict_group(data)

        # 삭감 위험 예측
        denial_pred = self.predict_denial_risk(data)

        # CMI 예상
        group = group_pred["predicted_group"]
        cmi_values = {
            "A": {"current": 1.3, "potential": 1.3},
            "B": {
                "current": 1.0,
                "potential": 1.3 if group_pred["can_upgrade"] else 1.0,
            },
            "C": {
                "current": 0.7,
                "potential": 1.0 if group_pred["can_upgrade"] else 0.7,
            },
        }

        cmi = cmi_values.get(group, cmi_values["B"])
        revenue_impact = (cmi["potential"] - cmi["current"]) * 300000

        return {
            "group_prediction": group_pred,
            "denial_risk": denial_pred,
            "estimated_cmi": cmi["current"],
            "potential_cmi": cmi["potential"],
            "revenue_impact": revenue_impact,
            "recommendations": self._generate_recommendations(group_pred, denial_pred),
        }

    def _generate_recommendations(self, group_pred: Dict, denial_pred: Dict) -> list:
        """통합 권고사항 생성"""
        recommendations = []

        # A그룹 전환 가능성
        if group_pred["can_upgrade"]:
            recommendations.append(
                f"A그룹 전환 가능성: {group_pred['a_group_probability'] * 100:.1f}%"
            )

        # 삭감 위험
        if denial_pred["risk_level"] in ["HIGH", "MEDIUM"]:
            recommendations.append(f"청구 삭감 위험: {denial_pred['risk_level']}")

        return recommendations


# 전역 예측 서비스 인스턴스
prediction_service = PredictionService()
