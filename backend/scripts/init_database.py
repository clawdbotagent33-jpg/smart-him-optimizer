"""데이터베이스 초기화 스크립트"""

import asyncio
import sys
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from database.base import init_db


async def main():
    print("데이터베이스 테이블 생성 중...")
    await init_db()
    print("데이터베이스 초기화 완료!")


if __name__ == "__main__":
    asyncio.run(main())
