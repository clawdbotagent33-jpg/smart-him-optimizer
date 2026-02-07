"""초기 사용자 생성 스크립트"""
import sys
sys.path.append('/home/red/smart-him-optimizer/backend')

from passlib.context import CryptContext
from database.base import AsyncSessionLocal, engine
from database.models import Base, User, UserRole
from sqlalchemy import select
import asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_user():
    """테스트 사용자 생성"""
    async with AsyncSessionLocal() as session:
        # 기존 사용자 확인
        result = await session.execute(select(User).filter(User.username == 'admin'))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"이미 존재하는 사용자: {existing.username}")
            return existing

        # 테스트 사용자 생성
        hashed_password = pwd_context.hash('admin123')

        users = [
            User(
                username='admin',
                email='admin@him.local',
                hashed_password=hashed_password,
                name='시스템 관리자',
                role=UserRole.ADMIN,
                department='정보팀',
                is_active=True
            ),
            User(
                username='him',
                email='him@him.local',
                hashed_password=hashed_password,
                name='김보건',
                role=UserRole.HIM_MANAGER,
                department='보건의료정보관리과',
                is_active=True
            ),
            User(
                username='doctor',
                email='doctor@him.local',
                hashed_password=hashed_password,
                name='이의사',
                role=UserRole.DOCTOR,
                department='내과',
                is_active=True
            ),
        ]

        for user in users:
            session.add(user)

        await session.commit()

        print("테스트 사용자가 생성되었습니다:")
        print("- 사용자명: admin, 비밀번호: admin123 (관리자)")
        print("- 사용자명: him, 비밀번호: admin123 (HIM관리사)")
        print("- 사용자명: doctor, 비밀번호: admin123 (의사)")

if __name__ == '__main__':
    asyncio.run(create_test_user())
