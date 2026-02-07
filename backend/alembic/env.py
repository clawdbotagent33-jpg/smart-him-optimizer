"""Alembic 환경 설정 - 비동기 SQLAlchemy 지원"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

# 모델 임포트
from database.base import Base
from database.models import (
    User,
    Patient,
    Admission,
    Prediction,
    CDIQuery,
    Document,
    AuditLog,
    SafetyIncident,
)
from core.config import settings

# this is the Alembic Config object
config = context.config

# 데이터베이스 URL 설정
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 모델 메타데이터 설정
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드로 마이그레이션 실행"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """마이그레이션 실행"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 마이그레이션 실행"""
    # 동기 엔진 사용 (Alembic은 비동기를 직접 지원하지 않음)
    from sqlalchemy import create_engine

    url = config.get_main_option("sqlalchemy.url")
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


def run_migrations_online() -> None:
    """온라인 모드로 마이그레이션 실행"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
