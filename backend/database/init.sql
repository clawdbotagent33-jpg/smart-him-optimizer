-- Smart HIM Optimizer Database Initialization Script

-- pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

-- RAG 검색을 위한 문서 벡터 테이블
CREATE TABLE IF NOT EXISTS document_vectors (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    embedding vector(384),  -- all-MiniLM-L6-v2 차원
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 벡터 인덱스 생성 (IVFFlat - 대용량 데이터용)
CREATE INDEX IF NOT EXISTS document_vectors_embedding_idx
ON document_vectors
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- 전체 텍스트 검색을 위한 인덱스
CREATE INDEX IF NOT EXISTS documents_content_gin_idx
ON documents
USING gin(to_tsvector('korean', content));

-- 환자 검색 인덱스
CREATE INDEX IF NOT EXISTS patients_anonymous_id_idx
ON patients(anonymous_id);

CREATE INDEX IF NOT EXISTS admissions_drg_group_idx
ON admissions(drg_group);

CREATE INDEX IF NOT EXISTS admissions_admission_date_idx
ON admissions(admission_date DESC);

-- 감사 로그 인덱스
CREATE INDEX IF NOT EXISTS audit_logs_user_id_idx
ON audit_logs(user_id);

CREATE INDEX IF NOT EXISTS audit_logs_created_at_idx
ON audit_logs(created_at DESC);

-- CDI 쿼리 인덱스
CREATE INDEX IF NOT EXISTS cdi_queries_status_idx
ON cdi_queries(status);

CREATE INDEX IF NOT EXISTS cdi_queries_admission_id_idx
ON cdi_queries(admission_id);

-- 예측 결과 인덱스
CREATE INDEX IF NOT EXISTS predictions_admission_id_idx
ON predictions(admission_id);

-- 사용자 함수: 재원일수 계산
CREATE OR REPLACE FUNCTION calculate_length_of_stay(
    admission_date TIMESTAMP,
    discharge_date TIMESTAMP
) RETURNS INTEGER AS $$
BEGIN
    IF discharge_date IS NULL THEN
        RETURN NULL;
    END IF;
    RETURN EXTRACT(DAY FROM (discharge_date - admission_date))::INTEGER + 1;
END;
$$ LANGUAGE plpgsql;

-- 사용자 함수: CMI 계산
CREATE OR REPLACE FUNCTION calculate_cmi(
    drg_weight FLOAT
) RETURNS FLOAT AS $$
BEGIN
    RETURN COALESCE(drg_weight, 0);
END;
$$ LANGUAGE plpgsql;
