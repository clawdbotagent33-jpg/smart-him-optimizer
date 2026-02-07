"""인증 API 엔드포인트 - 임시 메모리 버전 (DB 없이 동작)"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
from typing import Optional

from core.security import create_access_token, decode_access_token
from api.schemas import LoginRequest, TokenResponse, UserResponse

router = APIRouter()
security = HTTPBearer()

# 평문 비밀번호 (테스트용)
TEST_PASSWORD = "admin123"

# 임시 사용자 저장소 (DB 없이 테스트용)
TEST_USERS = {
    'admin': {
        'id': 1,
        'username': 'admin',
        'email': 'admin@him.local',
        'name': '시스템 관리자',
        'role': 'admin',
        'department': '정보팀',
        'is_active': True,
        'created_at': datetime.now(),
        'password': TEST_PASSWORD
    },
    'him': {
        'id': 2,
        'username': 'him',
        'email': 'him@him.local',
        'name': '김보건',
        'role': 'him_manager',
        'department': '보건의료정보관리과',
        'is_active': True,
        'created_at': datetime.now(),
        'password': TEST_PASSWORD
    },
    'doctor': {
        'id': 3,
        'username': 'doctor',
        'email': 'doctor@him.local',
        'name': '이의사',
        'role': 'doctor',
        'department': '내과',
        'is_active': True,
        'created_at': datetime.now(),
        'password': TEST_PASSWORD
    }
}


class SimpleUser:
    """간단 사용자 객체"""
    def __init__(self, data):
        self.id = data['id']
        self.username = data['username']
        self.email = data['email']
        self.name = data['name']
        self.role = data['role']
        self.department = data.get('department')
        self.is_active = data['is_active']
        self.created_at = data['created_at']
        self.password = data['password']


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> SimpleUser:
    """현재 사용자 가져오기"""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 토큰입니다"
        )

    username = payload.get("sub")
    if username is None or username not in TEST_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다"
        )

    return SimpleUser(TEST_USERS[username])


def require_role(*roles: str):
    """역할 기반 접근 제어 의존성"""
    async def role_checker(current_user: SimpleUser = Depends(get_current_user)) -> SimpleUser:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"접근 권한이 없습니다"
            )
        return current_user
    return role_checker


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """로그인"""
    username = request.username
    password = request.password

    # 사용자 조회
    if username not in TEST_USERS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다"
        )

    user_data = TEST_USERS[username]
    user = SimpleUser(user_data)

    # 비밀번호 검증 (평문 비교)
    if password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자명 또는 비밀번호가 올바르지 않습니다"
        )

    # 토큰 생성
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )

    return TokenResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            role=user.role,
            department=user.department,
            is_active=user.is_active,
            created_at=user.created_at
        )
    )


@router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: SimpleUser = Depends(get_current_user)):
    """현재 사용자 정보 조회"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        department=current_user.department,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


@router.post("/auth/logout")
async def logout():
    """로그아웃"""
    return {"message": "로그아웃되었습니다"}
