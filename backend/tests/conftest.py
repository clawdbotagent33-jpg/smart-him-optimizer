"""테스트 설정 및 공통 픽스처"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from api.main import app
from database.base import Base, get_db
from core.config import settings

# 테스트용 데이터베이스 URL
TEST_DATABASE_URL = settings.DATABASE_URL + "_test"

# 테스트용 엔진 생성
engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
    echo=False,
)

# 테스트용 세션 팩토리
TestingSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def override_get_db():
    """테스트용 DB 세션 오버라이드"""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# DB 의존성 오버라이드
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    """FastAPI 테스트 클라이언트"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
async def setup_database():
    """각 테스트 전에 데이터베이스 초기화"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """테스트용 DB 세션"""
    async with TestingSessionLocal() as session:
        yield session
