"""
청구 삭감 예측 모델 학습 스크립트
"""
import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
import pickle
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings


def load_training_data(csv_path: str) -> pd.DataFrame:
    """학습 데이터 로드"""
    df = pd.read_csv(csv_path)

    # 필수 컬럼 확인
    required_cols = ['was_denied']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"필수 컬럼 누락: {col}")

    return df


def preprocess_data(df: pd.DataFrame) -> tuple:
    """데이터 전처리"""
    df = df.copy()

    # 결측치 처리
    df['drg_weight'] = df['drg_weight'].fillna(0)
    df['length_of_stay'] = df['length_of_stay'].fillna(0)

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

    # 위험 요인 특성
    df['has_principal_diagnosis'] = df['principal_diagnosis'].notna().astype(int)
    df['abnormal_los'] = ((df['length_of_stay'] < 2) | (df['length_of_stay'] > 60)).astype(int)

    # 특성 선택
    feature_cols = [
        'length_of_stay',
        'drg_weight',
        'comorbidity_count',
        'procedure_count',
        'has_principal_diagnosis',
        'abnormal_los'
    ]

    # DRG 그룹 인코딩
    if 'drg_group' in df.columns:
        df['drg_group_A'] = (df['drg_group'] == 'A').astype(int)
        df['drg_group_B'] = (df['drg_group'] == 'B').astype(int)
        df['drg_group_C'] = (df['drg_group'] == 'C').astype(int)
        feature_cols.extend(['drg_group_A', 'drg_group_B', 'drg_group_C'])

    # 과거 삭감 이력
    if 'past_denials' in df.columns:
        feature_cols.append('past_denials')
        df['past_denials'] = df['past_denials'].fillna(0)
    else:
        df['past_denials'] = 0
        feature_cols.append('past_denials')

    X = df[feature_cols].fillna(0)
    y = df['was_denied']

    return X, y, feature_cols


def train_model(X_train, y_train, X_val, y_val) -> RandomForestClassifier:
    """RandomForest 모델 학습"""
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,
        min_samples_leaf=5,
        random_state=42,
        class_weight='balanced'
    )

    model.fit(X_train, y_train)

    return model


def evaluate_model(model, X_test, y_test):
    """모델 평가"""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n=== 분류 보고서 ===")
    print(classification_report(y_test, y_pred))

    print(f"\nROC-AUC 점수: {roc_auc_score(y_test, y_prob):.4f}")

    # 특성 중요도
    importance = model.feature_importances_
    feature_names = model.feature_names_in_

    print("\n=== 특성 중요도 ===")
    for name, imp in sorted(zip(feature_names, importance), key=lambda x: -x[1]):
        print(f"{name}: {imp:.4f}")


def save_model(model, feature_cols, output_path: str):
    """모델 저장"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    model_data = {
        'model': model,
        'features': feature_cols,
        'trained_at': datetime.now().isoformat()
    }

    with open(output_path, 'wb') as f:
        pickle.dump(model_data, f)

    print(f"\n모델이 저장되었습니다: {output_path}")


def main():
    """메인 학습 함수"""
    print("=== 삭감 예측 모델 학습 시작 ===\n")

    # 데이터 경로
    data_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'data', 'raw', 'denials_train.csv'
    )

    if not os.path.exists(data_path):
        print(f"데이터 파일을 찾을 수 없습니다: {data_path}")
        print("샘플 데이터를 생성합니다...")

        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        create_sample_data(data_path)

    # 데이터 로드
    print("데이터 로드 중...")
    df = load_training_data(data_path)
    print(f"데이터 크기: {df.shape}")

    # 전처리
    print("전처리 중...")
    X, y, feature_cols = preprocess_data(df)

    # 데이터 분할
    print("데이터 분할 중...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"학습 데이터: {X_train.shape}")
    print(f"테스트 데이터: {X_test.shape}")

    # 학습
    print("\n모델 학습 중...")
    model = train_model(X_train, y_train, X_test, y_test)

    # 평가
    print("\n평가 중...")
    evaluate_model(model, X_test, y_test)

    # 저장
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'backend', settings.ML_MODEL_PATH, 'denial_predictor.pkl'
    )
    save_model(model, feature_cols, output_path)

    print("\n=== 학습 완료 ===")


def create_sample_data(path: str):
    """샘플 데이터 생성"""
    np.random.seed(42)
    n_samples = 1000

    # 삭감 확률에 영향을 미치는 요인
    data = {
        'principal_diagnosis': [
            f"I{np.random.randint(10, 99)}" if np.random.random() > 0.1 else None
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
        'length_of_stay': np.random.randint(1, 30, n_samples),
        'drg_weight': np.random.uniform(0.5, 2.0, n_samples),
        'drg_group': np.random.choice(['A', 'B', 'C'], n_samples),
        'past_denials': np.random.randint(0, 5, n_samples),
    }

    df = pd.DataFrame(data)

    # 삭급 여부 생성 (룰 기반)
    denial_prob = (
        (df['principal_diagnosis'].isna()) * 0.3 +
        (df['length_of_stay'] < 2) * 0.2 +
        (df['drg_group'] == 'C') * 0.15 +
        (df['past_denials'] > 0) * 0.1
    )
    df['was_denied'] = (np.random.random(n_samples) < denial_prob).astype(int)

    df.to_csv(path, index=False)
    print(f"샘플 데이터 생성 완료: {path}")


if __name__ == '__main__':
    main()
