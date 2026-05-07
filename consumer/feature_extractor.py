import time
from storage.redis_client import RedisClient


class FeatureExtractor:
    def __init__(self, redis_client: RedisClient):
        self.r = redis_client

    def extract(self, event: dict) -> dict:
        ip = event["ip"]
        device_id = event["device_id"]
        now_ms = event["timestamp"] * 1000

        # 点击频率特征
        ip_click_count_1min = self.r.get_click_count(ip, 60)
        ip_click_count_1hour = self.r.get_click_count(ip, 3600)

        # 设备 IP 多样性
        device_ip_count = self.r.get_device_ip_count(device_id)

        # 点击间隔
        last_click_ms = self.r.get_last_click_time(ip)
        click_interval_ms = (now_ms - last_click_ms) if last_click_ms else -1

        # 时段特征（0–23小时）
        hour_of_day = int((event["timestamp"] % 86400) / 3600)

        # 黑名单
        is_blacklisted = int(self.r.is_blacklisted(ip))

        return {
            "ip_click_count_1min":  ip_click_count_1min,
            "ip_click_count_1hour": ip_click_count_1hour,
            "device_ip_count":      device_ip_count,
            "click_interval_ms":    click_interval_ms,
            "hour_of_day":          hour_of_day,
            "app_id":               event["app_id"],
            "channel_id":           event["channel_id"],
            "os":                   event["os"],
            "is_blacklisted":       is_blacklisted,
        }
