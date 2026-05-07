import time
import redis

REDIS_HOST = "localhost"
REDIS_PORT = 6379


class RedisClient:
    def __init__(self):
        self.r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    # ── 滑动窗口点击计数 ──────────────────────────────────────────
    def increment_click_count(self, ip: str, window_seconds: int) -> int:
        """给 IP 的点击数 +1，返回当前窗口内的总点击数"""
        key = f"rate:{ip}:{window_seconds}"
        count = self.r.incr(key)
        if count == 1:
            self.r.expire(key, window_seconds)  # 第一次写入时设置过期时间
        return count

    def get_click_count(self, ip: str, window_seconds: int) -> int:
        return int(self.r.get(f"rate:{ip}:{window_seconds}") or 0)

    # ── 设备 IP 多样性追踪（HyperLogLog）────────────────────────
    def add_device_ip(self, device_id: str, ip: str):
        """记录这个设备出现过这个 IP"""
        key = f"device:{device_id}:ips"
        self.r.pfadd(key, ip)
        self.r.expire(key, 3600)  # 1小时后过期

    def get_device_ip_count(self, device_id: str) -> int:
        """返回这个设备过去1小时出现过多少个不同 IP（近似值）"""
        return self.r.pfcount(f"device:{device_id}:ips")

    # ── 上次点击时间（用于计算点击间隔）────────────────────────
    def set_last_click_time(self, ip: str, timestamp_ms: float):
        self.r.set(f"last_click:{ip}", timestamp_ms, ex=300)  # 5分钟过期

    def get_last_click_time(self, ip: str) -> float | None:
        val = self.r.get(f"last_click:{ip}")
        return float(val) if val else None

    # ── IP 黑名单 ────────────────────────────────────────────────
    def add_to_blacklist(self, ip: str, ttl: int = 3600):
        """把 IP 加入黑名单，默认封禁 1 小时"""
        self.r.set(f"blacklist:{ip}", 1, ex=ttl)

    def is_blacklisted(self, ip: str) -> bool:
        return self.r.exists(f"blacklist:{ip}") == 1
