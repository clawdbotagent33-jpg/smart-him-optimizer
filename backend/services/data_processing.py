"""데이터 처리 서비스 모듈"""
import io
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.security import anonymizer
from core.config import settings


class EMRDataProcessor:
    """EMR 데이터 처리 클래스"""

    def __init__(self):
        self.anonymizer = anonymizer
        self.required_columns = [
            "patient_id",
            "patient_name",
            "admission_date",
            "principal_diagnosis",
            "department"
        ]

    def parse_csv(self, file_content: bytes) -> pd.DataFrame:
        """CSV 파일 파싱"""
        try:
            df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_content), encoding='cp949')

        return df

    def parse_excel(self, file_content: bytes) -> pd.DataFrame:
        """Excel 파일 파싱"""
        df = pd.read_excel(io.BytesIO(file_content))
        return df

    def validate_emr_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """EMR 데이터 검증"""
        errors = []
        warnings = []

        # 필수 컬럼 확인
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            errors.append(f"필수 컬럼 누락: {', '.join(missing_cols)}")

        # 데이터 형식 확인
        if 'admission_date' in df.columns:
            try:
                pd.to_datetime(df['admission_date'])
            except Exception:
                errors.append("admission_date 형식이 올바르지 않습니다")

        # 진단코드 형식 확인
        if 'principal_diagnosis' in df.columns:
            invalid_codes = df[
                ~df['principal_diagnosis'].str.match(r'^[A-Z]\d{2}(\.\d)?', na=False)
            ]['principal_diagnosis'].unique()
            if len(invalid_codes) > 0:
                warnings.append(f"진단코드 형식 확인 필요: {list(invalid_codes[:5])}")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "row_count": len(df),
            "columns": list(df.columns)
        }

    def anonymize_emr_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """EMR 데이터 비식별화"""
        anonymized_df = df.copy()

        # 환자 ID 비식별화
        if 'patient_id' in anonymized_df.columns:
            anonymized_df['patient_id'] = anonymized_df['patient_id'].apply(
                lambda x: self.anonymizer.anonymize_patient_id(str(x))
            )

        # 이름 비식별화
        if 'patient_name' in anonymized_df.columns:
            anonymized_df['patient_name'] = anonymized_df['patient_name'].apply(
                self.anonymizer.anonymize_name
            )

        # 전화번호 비식별화
        if 'phone' in anonymized_df.columns:
            anonymized_df['phone'] = anonymized_df['phone'].apply(
                self.anonymizer.anonymize_phone
            )

        # 주민번호 비식별화
        if 'ssn' in anonymized_df.columns:
            anonymized_df['ssn'] = anonymized_df['ssn'].apply(
                self.anonymizer.anonymize_ssn
            )

        # 주소 비식별화
        if 'address' in anonymized_df.columns:
            anonymized_df['address'] = anonymized_df['address'].apply(
                self.anonymizer._anonymize_address
            )

        return anonymized_df

    def transform_to_admission_format(
        self,
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """입원 데이터 형식으로 변환"""
        admissions = []

        for _, row in df.iterrows():
            admission = {
                "anonymous_id": self.anonymizer.anonymize_patient_id(
                    str(row.get('patient_id', ''))
                ),
                "admission_id": row.get('admission_id', f"ADM-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                "admission_date": self._parse_date(row.get('admission_date')),
                "discharge_date": self._parse_date(row.get('discharge_date')),
                "department": row.get('department', ''),
                "principal_diagnosis": row.get('principal_diagnosis', ''),
                "secondary_diagnoses": self._parse_list(row.get('secondary_diagnoses')),
                "procedures": self._parse_list(row.get('procedures')),
                "drg_code": row.get('drg_code', ''),
                "drg_group": row.get('drg_group', ''),
                "drg_weight": row.get('drg_weight', 0.0),
                "length_of_stay": row.get('length_of_stay'),
                "gender": row.get('gender', ''),
                "age": row.get('age', 0),
                "lab_results": self._parse_json(row.get('lab_results', {})),
                "vital_signs": self._parse_json(row.get('vital_signs', {})),
                "safety_incidents": self._parse_json(row.get('safety_incidents', [])),
                "claim_amount": row.get('claim_amount', 0.0),
                "adjusted_amount": row.get('adjusted_amount', 0.0),
                "denial_reason": row.get('denial_reason', ''),
            }

            # 재원일수 계산
            if admission['admission_date'] and admission['discharge_date']:
                admission['length_of_stay'] = (
                    admission['discharge_date'] - admission['admission_date']
                ).days + 1

            admissions.append(admission)

        return admissions

    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """날짜 파싱"""
        if pd.isna(date_value):
            return None
        if isinstance(date_value, datetime):
            return date_value
        try:
            return pd.to_datetime(date_value)
        except Exception:
            return None

    def _parse_list(self, value: Any) -> List[str]:
        """리스트 파싱"""
        if pd.isna(value):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            return [item.strip() for item in value.split(',')]
        return []

    def _parse_json(self, value: Any) -> Any:
        """JSON 파싱"""
        if pd.isna(value):
            return None
        if isinstance(value, (dict, list)):
            return value
        if isinstance(value, str):
            try:
                import json
                return json.loads(value)
            except Exception:
                return None
        return None

    def calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """기본 통계 계산"""
        stats = {
            "total_patients": df['patient_id'].nunique() if 'patient_id' in df.columns else 0,
            "total_admissions": len(df),
            "group_distribution": {},
            "department_distribution": {},
            "average_los": 0,
            "cmi": 0
        }

        # 그룹 분포
        if 'drg_group' in df.columns:
            stats['group_distribution'] = df['drg_group'].value_counts().to_dict()

        # 부서 분포
        if 'department' in df.columns:
            stats['department_distribution'] = df['department'].value_counts().head(10).to_dict()

        # 평균 재원일수
        if 'length_of_stay' in df.columns:
            stats['average_los'] = float(df['length_of_stay'].mean())

        # CMI (Case Mix Index)
        if 'drg_weight' in df.columns:
            stats['cmi'] = float(df['drg_weight'].mean())

        return stats


class DocumentProcessor:
    """문서 처리 클래스 (RAG용)"""

    def __init__(self):
        self.supported_formats = ['.pdf', '.txt', '.docx', '.hwp', '.png', '.jpg']

    def extract_text(self, file_path: str, file_type: str) -> str:
        """파일에서 텍스트 추출"""
        if file_type == '.pdf':
            return self._extract_from_pdf(file_path)
        elif file_type == '.docx':
            return self._extract_from_docx(file_path)
        elif file_type == '.txt':
            return self._extract_from_txt(file_path)
        elif file_type in ['.png', '.jpg', '.jpeg']:
            return self._extract_from_image(file_path)
        else:
            raise ValueError(f"지원하지 않는 파일 형식: {file_type}")

    def _extract_from_pdf(self, file_path: str) -> str:
        """PDF 텍스트 추출"""
        import PyPDF2
        text = ""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text

    def _extract_from_docx(self, file_path: str) -> str:
        """DOCX 텍스트 추출"""
        from docx import Document
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text

    def _extract_from_txt(self, file_path: str) -> str:
        """TXT 텍스트 추출"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _extract_from_image(self, file_path: str) -> str:
        """이미지 텍스트 추출 (OCR)"""
        # OCR 구현 (필요시)
        return "[이미지 파일: OCR 처리 필요]"

    def classify_document(self, content: str, filename: str) -> str:
        """문서 유형 분류"""
        filename_lower = filename.lower()

        if 'k-drg' in filename_lower or 'drg' in filename_lower:
            return 'k_drg_guideline'
        elif 'kcd' in filename_lower or '질병' in filename_lower:
            return 'kcd9_guideline'
        elif '수기' in filename_lower or '메모' in filename_lower:
            return 'manual_memo'
        elif '지침' in filename_lower or '가이드' in filename_lower:
            return 'guideline'
        elif '평가' in filename_lower or '지표' in filename_lower:
            return 'performance_metric'
        else:
            return 'general'


# 전역 인스턴스
emr_processor = EMRDataProcessor()
document_processor = DocumentProcessor()
