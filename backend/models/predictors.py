"""ML 예측 모델 모듈"""
import pickle
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import xgboost as xgb

from core.config import settings


class AGroupClassifier:
    """A그룹(전문질병군) 분류 예측 모델"""

    def __init__(self):
        self.model = None
        self.label_encoders = {}
        self.feature_columns = []

    def load_model(self, model_path: Optional[str] = None):
        """모델 로드"""
        path = model_path or f"{settings.ML_MODEL_PATH}/a_group_classifier.pkl"
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.label_encoders = model_data['encoders']
                self.feature_columns = model_data['features']
            return True
        except Exception as e:
            print(f"Model load error: {e}")
            return False

    def save_model(self, model_path: Optional[str] = None):
        """모델 저장"""
        path = model_path or f"{settings.ML_MODEL_PATH}/a_group_classifier.pkl"
        model_data = {
            'model': self.model,
            'encoders': self.label_encoders,
            'features': self.feature_columns
        }
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

    def train(self, df: pd.DataFrame, target_col: str = 'drg_group'):
        """모델 학습"""
        # 특성 엔지니어링
        X, y = self._prepare_features(df, target_col)

        # 학습/검증 분할
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # XGBoost 모델 학습
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        )

        self.model.fit(X_train, y_train)

        # 특성 컬럼 저장
        self.feature_columns = X.columns.tolist()

        # 평가
        train_score = self.model.score(X_train, y_train)
        val_score = self.model.score(X_val, y_val)

        return {
            "train_accuracy": train_score,
            "val_accuracy": val_score
        }

    def predict(self, admission_data: Dict[str, Any]) -> Dict[str, Any]:
        """A그룹 전환 가능성 예측"""
        if self.model is None:
            self.load_model()

        # 데이터프레임 변환
        df = pd.DataFrame([admission_data])

        # 특성 준비
        X = self._encode_features(df)

        # 예측
        proba = self.model.predict_proba(X)[0]

        # 클래스 매핑
        classes = self.model.classes_
        group_probs = {}
        for i, cls in enumerate(classes):
            group_probs[str(cls)] = float(proba[i])

        # A그룹 확률
        a_group_prob = group_probs.get('A', 0.0)

        return {
            "predicted_group": classes[np.argmax(proba)],
            "probabilities": group_probs,
            "a_group_probability": a_group_prob,
            "can_upgrade": a_group_prob >= settings.A_GROUP_THRESHOLD,
            "confidence": float(np.max(proba))
        }

    def _prepare_features(self, df: pd.DataFrame, target_col: str):
        """특성 엔지니어링"""
        features = []

        # 기본 특성
        feature_cols = [
            'age', 'gender', 'length_of_stay',
            'department', 'principal_diagnosis_chapter'
        ]

        # 검사 결과 관련 특성
        lab_cols = [col for col in df.columns if col.startswith('lab_')]
        feature_cols.extend(lab_cols)

        # 처치 관련 특성
        proc_cols = [col for col in df.columns if col.startswith('proc_')]
        feature_cols.extend(proc_cols)

        # 합병증 수
        if 'secondary_diagnoses' in df.columns:
            df['comorbidity_count'] = df['secondary_diagnoses'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )
            feature_cols.append('comorbidity_count')

        # 사용 가능한 컬럼만 선택
        available_cols = [col for col in feature_cols if col in df.columns]

        X = df[available_cols].copy()
        y = df[target_col] if target_col in df.columns else None

        # 범주형 변수 인코딩
        for col in X.select_dtypes(include=['object']).columns:
            if col not in self.label_encoders:
                self.label_encoders[col] = LabelEncoder()
                X[col] = self.label_encoders[col].fit_transform(X[col].fillna('Unknown'))
            else:
                X[col] = self.label_encoders[col].transform(X[col].fillna('Unknown'))

        # 결측치 처리
        X = X.fillna(0)

        return X, y

    def _encode_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """특성 인코딩"""
        X = df.copy()

        # 필요한 특성 생성
        if 'secondary_diagnoses' in X.columns:
            X['comorbidity_count'] = X['secondary_diagnoses'].apply(
                lambda x: len(x) if isinstance(x, list) else 0
            )

        # 인코딩
        for col, encoder in self.label_encoders.items():
            if col in X.columns:
                # 새로운 값 처리
                unique_values = set(encoder.classes_)
                X[col] = X[col].apply(
                    lambda x: x if x in unique_values else 'Unknown'
                )
                X[col] = encoder.transform(X[col].fillna('Unknown'))

        return X.fillna(0)


class DenialPredictor:
    """청구 삭감 예측 모델"""

    def __init__(self):
        self.model = None
        self.risk_factors = {}

    def load_model(self, model_path: Optional[str] = None):
        """모델 로드"""
        path = model_path or f"{settings.ML_MODEL_PATH}/denial_predictor.pkl"
        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)
                self.model = model_data['model']
                self.risk_factors = model_data.get('risk_factors', {})
            return True
        except Exception as e:
            print(f"Model load error: {e}")
            return False

    def save_model(self, model_path: Optional[str] = None):
        """모델 저장"""
        path = model_path or f"{settings.ML_MODEL_PATH}/denial_predictor.pkl"
        model_data = {
            'model': self.model,
            'risk_factors': self.risk_factors
        }
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)

    def train(self, df: pd.DataFrame, target_col: str = 'was_denied'):
        """모델 학습"""
        X = self._prepare_features(df)
        y = df[target_col] if target_col in df.columns else None

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )

        self.model.fit(X_train, y_train)

        return {
            "train_accuracy": self.model.score(X_train, y_train),
            "val_accuracy": self.model.score(X_val, y_val),
            "feature_importance": dict(zip(X.columns, self.model.feature_importances_.tolist()))
        }

    def predict_risk(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """삭감 위험도 예측"""
        if self.model is None:
            # 모델이 없으면 룰 기반 예측
            return self._rule_based_prediction(claim_data)

        df = pd.DataFrame([claim_data])
        X = self._prepare_features(df)

        proba = self.model.predict_proba(X)[0]
        denial_prob = float(proba[1]) if len(proba) > 1 else 0.0

        return {
            "denial_probability": denial_prob,
            "risk_level": self._get_risk_level(denial_prob),
            "risk_factors": self._identify_risk_factors(claim_data)
        }

    def _rule_based_prediction(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """룰 기반 삭감 위험 예측"""
        risk_score = 0.0
        risk_factors = []

        # 주진단 누락
        if not claim_data.get('principal_diagnosis'):
            risk_score += 0.3
            risk_factors.append("주진단 미기재")

        # 재원일수 비정상
        los = claim_data.get('length_of_stay', 0)
        if los < 1 or los > 365:
            risk_score += 0.2
            risk_factors.append(f"비정상 재원일수: {los}일")

        # DRG 불일치
        if not claim_data.get('drg_code'):
            risk_score += 0.3
            risk_factors.append("DRG 코드 미지정")

        # 과거 삭감 이력
        if claim_data.get('past_denials', 0) > 0:
            risk_score += 0.2
            risk_factors.append("과거 삭감 이력 존재")

        return {
            "denial_probability": min(risk_score, 1.0),
            "risk_level": self._get_risk_level(risk_score),
            "risk_factors": risk_factors
        }

    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """특성 준비"""
        feature_cols = [
            'length_of_stay', 'drg_weight', 'comorbidity_count',
            'procedure_count', 'past_denials'
        ]

        available_cols = [col for col in feature_cols if col in df.columns]
        X = df[available_cols].fillna(0)

        return X

    def _get_risk_level(self, probability: float) -> str:
        """위험도 레벨 반환"""
        if probability >= 0.7:
            return "HIGH"
        elif probability >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"

    def _identify_risk_factors(self, claim_data: Dict[str, Any]) -> List[str]:
        """위험 요인 식별"""
        factors = []

        if not claim_data.get('principal_diagnosis'):
            factors.append("주진단 미기재")

        los = claim_data.get('length_of_stay', 0)
        if los < 2:
            factors.append("단기 재원 (1일 이하)")

        if not claim_data.get('secondary_diagnoses'):
            factors.append("부진단 미기재")

        drg_group = claim_data.get('drg_group')
        if drg_group == 'C':
            factors.append("심층질병군(C그룹)")

        return factors


class ClinicalEntityExtractor:
    """임상적 엔티티 추출 (진단코드 후보 추천)"""

    def __init__(self):
        self.diagnosis_keywords = {}
        self.procedure_keywords = {}

    def load_knowledge_base(self, kb_path: Optional[str] = None):
        """진단/처치 지식베이스 로드"""
        # KCD-9 기반 키워드 맵핑
        self.diagnosis_keywords = {
            "폐렴": ["J18", "J15", "J12"],
            "당뇨": ["E10", "E11", "E12"],
            "고혈압": ["I10", "I11", "I12"],
            "뇌졸중": ["I63", "I64", "I60"],
            "심근경색": ["I21", "I22", "I23"],
            "폐결핵": ["A15", "A16", "A17"],
            "간염": ["B15", "B16", "B17", "B18"],
            "신부전": ["N17", "N18", "N19"],
            # ... 더 많은 키워드
        }

        self.procedure_keywords = {
            "수술": ["O", "코드"],
            "내시경": ["F", "검사"],
            "영상": ["X선", "CT", "MRI"],
            # ...
        }

    def extract_diagnoses(self, clinical_text: str) -> List[Dict[str, str]]:
        """임상 텍스트에서 진단 추출"""
        diagnoses = []

        for keyword, codes in self.diagnosis_keywords.items():
            if keyword in clinical_text:
                diagnoses.append({
                    "keyword": keyword,
                    "suggested_codes": codes,
                    "context": self._extract_context(clinical_text, keyword)
                })

        return diagnoses

    def extract_procedures(self, clinical_text: str) -> List[Dict[str, str]]:
        """임상 텍스트에서 처치 추출"""
        procedures = []

        for keyword, codes in self.procedure_keywords.items():
            if keyword in clinical_text:
                procedures.append({
                    "keyword": keyword,
                    "suggested_codes": codes
                })

        return procedures

    def _extract_context(self, text: str, keyword: str, window: int = 50) -> str:
        """키워드 주변 문맥 추출"""
        pos = text.find(keyword)
        if pos == -1:
            return ""

        start = max(0, pos - window)
        end = min(len(text), pos + len(keyword) + window)

        return text[start:end].strip()


# 전역 인스턴스
a_group_classifier = AGroupClassifier()
denial_predictor = DenialPredictor()
clinical_entity_extractor = ClinicalEntityExtractor()
