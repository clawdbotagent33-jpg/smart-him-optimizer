"""
A그룹(전문질병군) 분류 모델 학습 스크립트
"""
import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import xgboost as xgb
import pickle
from datetime import datetime

# 상위 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings


def load_training_data(csv_path: str) -> pd.DataFrame:
    """학습 데이터 로드"""
    df = pd.read_csv(csv_path)

    # 필수 컬럼 확인
    required_cols = ['principal_diagnosis', 'drg_group']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"필수 컬럼 누락: {col}")

    return df


def preprocess_data(df: pd.DataFrame) -> tuple:
    """데이터 전처리"""
    # 특성 엔지니어링
    df = df.copy()

    # 진단 코드 챕터 추출 (알파벳 부분)
    df['diagnosis_chapter'] = df['principal_diagnosis'].str[:1]

    # 합병증 수
    if 'secondary_diagnoses' in df.columns:
        df['comorbidity_count'] = df['secondary_diagnoses'].apply(
            lambda x: len(x.split(',')) if pd.notna(x) and isinstance(x, str) else 0
        )
    else:
        df['comorbidity_count'] = 0

    # 처치 수
    if 'procedures' in df.columns:
        df['procedure_count'] = df['procedures'].apply(
            lambda x: len(x.split(',')) if pd.notna(x) and isinstance(x, str) else 0
        )
    else:
        df['procedure_count'] = 0

    # 범주형 변수 인코딩
    label_encoders = {}

    for col in ['diagnosis_chapter', 'department', 'gender']:
        if col in df.columns:
            le = LabelEncoder()
            df[f'{col}_encoded'] = le.fit_transform(df[col].fillna('Unknown'))
            label_encoders[col] = le

    # 특성 컬럼 선택
    feature_cols = []
    if 'age' in df.columns:
        feature_cols.append('age')
    if 'length_of_stay' in df.columns:
        feature_cols.append('length_of_stay')
    if 'comorbidity_count' in df.columns:
        feature_cols.append('comorbidity_count')
    if 'procedure_count' in df.columns:
        feature_cols.append('procedure_count')

    # 인코딩된 컬럼 추가
    for col in ['diagnosis_chapter', 'department', 'gender']:
        encoded_col = f'{col}_encoded'
        if encoded_col in df.columns:
            feature_cols.append(encoded_col)

    X = df[feature_cols].copy()
    y = df['drg_group']

    # 결측치 처리
    X = X.fillna(0)

    return X, y, label_encoders, feature_cols


def train_model(X_train, y_train, X_val, y_val) -> xgb.XGBClassifier:
    """XGBoost 모델 학습"""
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        use_label_encoder=False,
        eval_metric='mlogloss'
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    return model


def evaluate_model(model, X_test, y_test):
    """모델 평가"""
    y_pred = model.predict(X_test)

    print("\n=== 분류 보고서 ===")
    print(classification_report(y_test, y_pred))

    print("\n=== 혼동 행렬 ===")
    print(confusion_matrix(y_test, y_pred))

    # 특성 중요도
    importance = model.feature_importances_
    print("\n=== 특성 중요도 ===")
    for i, imp in enumerate(importance):
        print(f"특성 {i}: {imp:.4f}")


def save_model(model, label_encoders, feature_cols, output_path: str):
    """모델 저장"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    model_data = {
        'model': model,
        'encoders': label_encoders,
        'features': feature_cols,
        'trained_at': datetime.now().isoformat()
    }

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"\n모델이 저장되었습니다: {output_path}")


def main():
    """메인 학습 함수"""
    print("=== A그룹 분류 모델 학습 시작 ===\n")

    # 데이터 경로
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'raw', 'admissions_train.csv'
    )

    if not os.path.exists(data_path):
        print(f"데이터 파일을 찾을 수 없습니다: {data_path}")
        print("샘플 데이터를 생성합니다...")

        # 샘플 데이터 생성
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        create_sample_data(data_path)

    # 데이터 로드
    print("데이터 로드 중...")
    df = load_training_data(data_path)
    print(f"데이터 크기: {df.shape}")

    # 전처리
    print("전처리 중...")
    X, y, label_encoders, feature_cols = preprocess_data(df)

    # 데이터 분할
    print("데이터 분할 중...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    print(f"학습 데이터: {X_train.shape}")
    print(f"검증 데이터: {X_val.shape}")
    print(f"테스트 데이터: {X_test.shape}")

    # 학습
    print("\n모델 학습 중...")
    model = train_model(X_train, y_train, X_val, y_val)

    # 평가
    print("\n평가 중...")
    evaluate_model(model, X_test, y_test)

    # 저장
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'backend', settings.ML_MODEL_PATH, 'a_group_classifier.pkl'
    )
    save_model(model, label_encoders, feature_cols, output_path)

    print("\n=== 학습 완료 ===")


def create_sample_data(path: str):
    """샘플 데이터 생성"""
    np.random.seed(42)
    n_samples = 1000

    data = {
        'principal_diagnosis': [
            f"{np.random.choice(['I', 'J', 'E', 'G'])}"
            f"{np.random.randint(10, 99)}"
                    for _ in range(n_samples)
        ],
        'secondary_diagnoses': [
            ','.join([f"E{np.random.randint(10, 99)}" for _ in range(np.random.randint(0, 3))])
            for _ in range(n_samples)
        ],
        'procedures': [
            ','.join([f"O{np.random.randint(100, 999)}" for _ in range(np.random.randint(0, 2))])
            for _ in range(n_samples)
        ],
        'age': np.random.randint(20, 90, n_samples),
        'gender': np.random.choice(['M', 'F'], n_samples),
        'department': np.random.choice(['내과', '외과', '정형외과', '신경과'], n_samples),
        'length_of_stay': np.random.randint(1, 30, n_samples),
        'drg_group': np.random.choice(['A', 'B', 'C'], n_samples, p=[0.15, 0.70, 0.15])
    }

    df = pd.DataFrame(data)
    df.to_csv(path, index=False)
    print(f"샘플 데이터 생성 완료: {path}")


if __name__ == '__main__':
    main()
