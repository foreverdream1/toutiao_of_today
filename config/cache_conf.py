import json
from typing import Any

import redis.asyncio as redis

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 10

# 使用连接池代替单连接，提升并发性能
_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True,
    max_connections=20,
)

redis_client = redis.Redis(connection_pool=_pool)


async def get_cache(key: str):
    """读取字符串缓存"""
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败: {e}")
        return None


async def get_json_cache(key: str):
    """读取并反序列化 JSON 缓存"""
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)   # 修复：load → loads
        return None
    except Exception as e:
        print(f"获取JSON缓存失败: {e}")
        return None


async def set_cache(key: str, value: Any, expire: int = 3600):
    """写入缓存，dict/list 自动 JSON 序列化，TTL 默认 1 小时"""
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False, default=str)
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print(f"设置缓存失败: {e}")
        return False


async def delete_cache(key: str):
    """删除指定缓存 key"""
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        print(f"删除缓存失败: {e}")
        return False


async def incr_cache(key: str, amount: int = 1):
    """对计数器类型的 key 做原子自增（用于浏览量写回）"""
    try:
        return await redis_client.incrby(key, amount)
    except Exception as e:
        print(f"计数器自增失败: {e}")
        return None
