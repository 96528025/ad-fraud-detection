import time
from storage.redis_client import RedisClient

CLICK_FLOOD_THRESHOLD = 10   # 同IP 1分钟内超过这个次数 → BLOCK
DEVICE_IP_THRESHOLD = 50     # 同设备不同IP超过这个数量 → FLAG
BOT_INTERVAL_MS = 50         # 点击间隔小于这个毫秒数 → BLOCK


class RuleEngine:
    def __init__(self, redis_client: RedisClient):
        self.r = redis_client

    def evaluate(self, event: dict) -> dict:
        ip = event["ip"]
        device_id = event["device_id"]
        now_ms = event["timestamp"] * 1000

        # RULE-01: 黑名单
        if self.r.is_blacklisted(ip):
            return {"action": "BLOCK", "rule": "RULE-01-BLACKLIST"}

        # 更新 Redis 计数器
        click_count_1min = self.r.increment_click_count(ip, 60)
        self.r.add_device_ip(device_id, ip)

        # 计算点击间隔
        last_click_ms = self.r.get_last_click_time(ip)
        interval_ms = (now_ms - last_click_ms) if last_click_ms else None
        self.r.set_last_click_time(ip, now_ms)

        # RULE-02: 点击洪泛
        if click_count_1min > CLICK_FLOOD_THRESHOLD:
            self.r.add_to_blacklist(ip, ttl=3600)
            return {"action": "BLOCK", "rule": "RULE-02-FLOOD"}

        # RULE-03: 机器人点击间隔
        if interval_ms is not None and interval_ms < BOT_INTERVAL_MS:
            return {"action": "BLOCK", "rule": "RULE-03-BOT"}

        # RULE-04: 设备 IP 伪造
        device_ip_count = self.r.get_device_ip_count(device_id)
        if device_ip_count > DEVICE_IP_THRESHOLD:
            return {"action": "FLAG", "rule": "RULE-04-DEVICE-SPOOF"}

        return {"action": "ALLOW", "rule": None}
