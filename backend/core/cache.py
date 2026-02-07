"""캐싱 설정"""

from typing import Optional
import functools
import hashlib
import json
import logging
from datetime import timedelta

from core.config import settings

logger = logging.getLogger(__name__)


class SimpleCache:
    """인메모리 캐시 (Redis 없이 사용 가능)"""

    def __init__(self):
        self._cache = {}
        self._ttl = {}

    def get(self, key: str) -> Optional[any]:
        """캐시에서 값 가져오기"""
        import time

        if key in self._cache:
            # TTL 확인
            if key in self._ttl and time.time() > self._ttl[key]:
                del self._cache[key]
                del self._ttl[key]
                return None
            return self._cache[key]
        return None

    def set(self, key: str, value: any, ttl: int = 300):
        """캐시에 값 저장"""
        import time

        self._cache[key] = value
        self._ttl[key] = time.time() + ttl

    def delete(self, key: str):
        """캐시에서 값 삭제"""
        if key in self._cache:
            del self._cache[key]
            if key in self._ttl:
                del self._ttl[key]

    def clear(self):
        """캐시 전체 삭제"""
        self._cache.clear()
        self._ttl.clear()


# 전역 캐시 인스턴스
cache = SimpleCache()


def generate_cache_key(*args, **kwargs) -> str:
    """캐시 키 생성"""
    key_data = {"args": args, "kwargs": kwargs}
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: int = 300, key_prefix: str = ""):
    """함수 결과 캐싱 데코레이터"""

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{generate_cache_key(*args, **kwargs)}"

            # 캐시 확인
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 함수 실행
            result = await func(*args, **kwargs)

            # 결과 캐싱
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache set: {cache_key}")

            return result

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{generate_cache_key(*args, **kwargs)}"

            # 캐시 확인
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 함수 실행
            result = func(*args, **kwargs)

            # 결과 캐싱
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache set: {cache_key}")

            return result

        # 비동기 함수인지 확인
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def invalidate_cache(key_prefix: str = ""):
    """캐시 무효화"""
    # SimpleCache는 개별 키 삭제만 지원
    # 실제 Redis를 사용할 때는 패턴 삭제 가능
    logger.info(f"Cache invalidation requested for prefix: {key_prefix}")
