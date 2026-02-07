"""예측 API 테스트"""

import pytest


class TestPredictionsAPI:
    """예측 API 테스트 클래스"""

    def test_predict_group_success(self, client):
        """그룹 예측 API 성공 테스트"""
        response = client.post(
            "/api/v1/predictions/group",
            json={
                "principalDiagnosis": "I50",
                "secondaryDiagnoses": ["E11"],
                "procedures": [],
                "age": 65,
                "gender": "M",
                "department": "내과",
                "lengthOfStay": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "predictedGroup" in data
        assert "confidence" in data
        assert data["predictedGroup"] in ["A", "B", "C"]
        assert 0 <= data["confidence"] <= 1

    def test_predict_group_with_a_group_code(self, client):
        """A그룹 코드로 예측 테스트"""
        response = client.post(
            "/api/v1/predictions/group",
            json={
                "principalDiagnosis": "A11",
                "age": 60,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["predictedGroup"] == "A"

    def test_predict_denial_risk_success(self, client):
        """삭감 위험 예측 API 성공 테스트"""
        response = client.post(
            "/api/v1/predictions/denial-risk",
            json={
                "principalDiagnosis": "I50",
                "age": 65,
                "lengthOfStay": 5,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "riskLevel" in data
        assert "riskScore" in data
        assert data["riskLevel"] in ["LOW", "MEDIUM", "HIGH"]
        assert 0 <= data["riskScore"] <= 1

    def test_predict_comprehensive_success(self, client):
        """종합 예측 API 성공 테스트"""
        response = client.post(
            "/api/v1/predictions/comprehensive",
            json={
                "principalDiagnosis": "I50",
                "secondaryDiagnoses": ["E11", "I10"],
                "procedures": ["처치1"],
                "age": 65,
                "gender": "M",
                "department": "내과",
                "lengthOfStay": 5,
                "clinicalNotes": "심부전 증상",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "groupPrediction" in data
        assert "denialRisk" in data
        assert "estimatedCmi" in data
        assert "potentialCmi" in data
        assert "revenueImpact" in data

    def test_predict_comprehensive_with_admission_id(self, client):
        """admission_id와 함께 종합 예측 테스트"""
        response = client.post(
            "/api/v1/predictions/comprehensive?admission_id=ADM001",
            json={
                "principalDiagnosis": "A01",
                "age": 70,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["admissionId"] == "ADM001"

    def test_batch_predict_success(self, client):
        """일괄 예측 API 성공 테스트"""
        response = client.post(
            "/api/v1/predictions/batch",
            json=[
                {
                    "principalDiagnosis": "I50",
                    "age": 65,
                },
                {
                    "principalDiagnosis": "A01",
                    "age": 70,
                },
            ],
        )

        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["results"]) == 2

    def test_check_compliance(self, client):
        """규정 준수 검증 API 테스트"""
        # 불량한 진단 코드
        response = client.post(
            "/api/v1/predictions/compliance",
            json={
                "principalDiagnosis": "I",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["isCompliant"] == False
        assert len(data["issues"]) > 0

        # 정상적인 진단 코드
        response = client.post(
            "/api/v1/predictions/compliance",
            json={
                "principalDiagnosis": "I50",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["isCompliant"] == True
        assert len(data["issues"]) == 0
