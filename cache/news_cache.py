# 新闻相关 Redis 缓存 Key 定义 & 读写封装
#
# Key 规范：
#   news:category                   -> 新闻分类列表（全量，TTL 2h）
#   news:list:{category_id}:{page}:{page_size} -> 分页列表（TTL 5min）
#   news:detail:{news_id}           -> 新闻详情（TTL 10min）
#   news:related:{news_id}          -> 相关新闻（TTL 10min）
#   news:views:{news_id}            -> 浏览量计数器（TTL 24h，定期写回 DB）

from typing import Any, Dict, List, Optional

from config.cache_conf import get_json_cache, set_cache, delete_cache, incr_cache, get_cache

# ──────────────────── Key 生成 ────────────────────

CATEGORY_KEY = "news:category"


def _list_key(category_id: int, page: int, page_size: int) -> str:
    return f"news:list:{category_id}:{page}:{page_size}"


def _detail_key(news_id: int) -> str:
    return f"news:detail:{news_id}"


def _related_key(news_id: int) -> str:
    return f"news:related:{news_id}"


def _views_key(news_id: int) -> str:
    return f"news:views:{news_id}"


# ──────────────────── 分类列表缓存 ────────────────────

async def get_cached_category() -> Optional[List[Dict]]:
    """读取新闻分类缓存"""
    return await get_json_cache(CATEGORY_KEY)   # 修复：补上 return


async def set_cached_category(data: List[Dict[str, Any]], expire: int = 7200):
    """写入新闻分类缓存，TTL 默认 2 小时"""
    return await set_cache(CATEGORY_KEY, data, expire)


async def delete_cached_category():
    """手动失效分类缓存（分类数据变更时调用）"""
    return await delete_cache(CATEGORY_KEY)


# ──────────────────── 新闻列表缓存 ────────────────────

async def get_cached_news_list(category_id: int, page: int, page_size: int) -> Optional[Dict]:
    """读取分页新闻列表缓存，返回 {list, total} 或 None"""
    return await get_json_cache(_list_key(category_id, page, page_size))


async def set_cached_news_list(
    category_id: int,
    page: int,
    page_size: int,
    data: Dict[str, Any],
    expire: int = 300,       # TTL 5 分钟，新闻列表更新较频繁
):
    """写入分页新闻列表缓存"""
    return await set_cache(_list_key(category_id, page, page_size), data, expire)


async def delete_cached_news_list_by_category(category_id: int):
    """失效某分类下所有分页缓存（暂不支持通配符，业务层用 pattern 删除）
    此处仅作标记，实际删除由 crud 层调用 redis SCAN+DEL 实现。
    """
    pass


# ──────────────────── 新闻详情缓存 ────────────────────

async def get_cached_news_detail(news_id: int) -> Optional[Dict]:
    """读取新闻详情缓存"""
    return await get_json_cache(_detail_key(news_id))


async def set_cached_news_detail(news_id: int, data: Dict[str, Any], expire: int = 600):
    """写入新闻详情缓存，TTL 默认 10 分钟"""
    return await set_cache(_detail_key(news_id), data, expire)


async def delete_cached_news_detail(news_id: int):
    """失效新闻详情缓存（新闻内容更新时调用）"""
    return await delete_cache(_detail_key(news_id))


# ──────────────────── 相关新闻缓存 ────────────────────

async def get_cached_related_news(news_id: int) -> Optional[List[Dict]]:
    """读取相关新闻列表缓存"""
    return await get_json_cache(_related_key(news_id))


async def set_cached_related_news(news_id: int, data: List[Dict], expire: int = 600):
    """写入相关新闻缓存，TTL 默认 10 分钟"""
    return await set_cache(_related_key(news_id), data, expire)


# ──────────────────── 浏览量计数器缓存（异步写回策略） ────────────────────

async def incr_cached_views(news_id: int) -> Optional[int]:
    """
    对 Redis 浏览量计数器原子自增 +1，并设置 TTL（若 key 不存在则初始化为 1）。
    后台定时任务或阈值触发时将计数器批量写回 MySQL。
    """
    key = _views_key(news_id)
    count = await incr_cache(key, 1)
    # 首次写入时设置 24h TTL，防止数据丢失
    if count == 1:
        from config.cache_conf import redis_client
        try:
            await redis_client.expire(key, 86400)
        except Exception:
            pass
    return count


async def get_cached_views(news_id: int) -> Optional[int]:
    """读取 Redis 中的浏览量计数（未缓存时返回 None，表示应从 DB 取）"""
    raw = await get_cache(_views_key(news_id))
    return int(raw) if raw is not None else None


async def reset_cached_views(news_id: int):
    """写回 DB 后清除 Redis 计数器"""
    return await delete_cache(_views_key(news_id))
