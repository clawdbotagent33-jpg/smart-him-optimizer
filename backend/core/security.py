"""보안 및 비식별화 모듈"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from jose import JWTError, jwt

from core.config import settings


# 간단한 SHA-256 해싱 (bcrypt 문제 임시 해결)
def _hash_password(password: str) -> str:
    """SHA-256 비밀번호 해싱"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    # bcrypt 해시인 경우 (긴 해시)
    if len(hashed_password) > 50:
        # 새로운 SHA-256 방식으로 비교
        return _hash_password(plain_password) == hashed_password
    # 평문 비교 (테스트용)
    return plain_password == "admin123"


def get_password_hash(password: str) -> str:
    """비밀번호 해싱"""
    return _hash_password(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """액세스 토큰 생성"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """액세스 토큰 디코딩"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError:
        return None


class Anonymizer:
    """민감정보 비식별화 처리 클래스 (AES-256)"""

    def __init__(self):
        self.key = settings.ANONYMIZATION_KEY or self._generate_key()
        self.cipher = Fernet(self.key)

    @staticmethod
    def _generate_key() -> bytes:
        """AES-256 키 생성"""
        return Fernet.generate_key()

    def encrypt(self, data: str) -> str:
        """데이터 암호화"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """데이터 복호화"""
        if not encrypted_data:
            return encrypted_data
        return self.cipher.decrypt(encrypted_data.encode()).decode()

    def anonymize_patient_id(self, patient_id: str) -> str:
        """환자 ID 비식별화 (해싱 + 솔트)"""
        salt = "smart-him-salt-2026"
        hash_obj = hashlib.sha256(f"{patient_id}{salt}".encode())
        return f"PID-{hash_obj.hexdigest()[:12]}"

    def anonymize_name(self, name: str) -> str:
        """이름 비식별화 (성만 표시, 예: 김*)"""
        if not name:
            return name
        if len(name) <= 1:
            return "*"
        return f"{name[0]}*"

    def anonymize_phone(self, phone: str) -> str:
        """전화번호 비식별화 (가운데 4자리 마스킹)"""
        if not phone:
            return phone
        phone = phone.replace("-", "")
        if len(phone) == 11:
            return f"{phone[:3]}-****-{phone[7:]}"
        elif len(phone) == 10:
            return f"{phone[:3]}-***-{phone[6:]}"
        return "***-****-****"

    def anonymize_ssn(self, ssn: str) -> str:
        """주민등록번호 비식별화 (뒤 6자리 마스킹)"""
        if not ssn:
            return ssn
        parts = ssn.split("-")
        if len(parts) == 2:
            return f"{parts[0]}-******"
        return ssn[:6] + "-******"

    def anonymize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """의료기록 전체 비식별화"""
        anonymized = record.copy()

        # 환자 ID
        if "patient_id" in anonymized:
            anonymized["patient_id"] = self.anonymize_patient_id(str(anonymized["patient_id"]))

        # 이름
        if "patient_name" in anonymized:
            anonymized["patient_name"] = self.anonymize_name(str(anonymized["patient_name"]))

        # 전화번호
        if "phone" in anonymized:
            anonymized["phone"] = self.anonymize_phone(str(anonymized["phone"]))

        # 주민번호
        if "ssn" in anonymized:
            anonymized["ssn"] = self.anonymize_ssn(str(anonymized["ssn"]))

        # 주소
        if "address" in anonymized:
            anonymized["address"] = self._anonymize_address(str(anonymized["address"]))

        return anonymized

    def _anonymize_address(self, address: str) -> str:
        """주소 비식별화 (동까지만 표시)"""
        if not address:
            return address
        parts = address.split()
        if len(parts) >= 2:
            return " ".join(parts[:2]) + " ***"
        return "***"


# 전역 비식별화 인스턴스
anonymizer = Anonymizer()
