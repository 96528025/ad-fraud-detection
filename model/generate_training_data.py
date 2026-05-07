"""
生成训练数据

模拟 100,000 条点击事件，计算每条事件的特征，保存为 CSV。
特征计算方式和线上 feature_extractor.py 保持一致。

用法：
    python model/generate_training_data.py
输出：
    data/training_data.csv
"""

import random
import time
import uuid
import pandas as pd
from collections import defaultdict
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "data" / "training_data.csv"
N_SAMPLES = 100_000
FRAUD_RATIO = 0.10

# 和 click_simulator.py 保持一致
random.seed(42)
IP_POOL = [f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
           for _ in range(500)]
DEVICE_POOL = [f"dev_{i:05d}" for i in range(200)]
APP_IDS = list(range(1, 50))
CHANNEL_IDS = list(range(1, 20))
OS_IDS = [0, 1, 2, 3]
FLOOD_IPS = IP_POOL[:5]
SPOOF_DEVICE = "dev_99999"
SPOOF_IPS = [f"10.0.{i}.{j}" for i in range(10) for j in range(10)]


def generate_events(n: int) -> list:
    events = []
    base_time = time.time() - n * 0.002  # 模拟过去一段时间的事件

    for i in range(n):
        ts = base_time + i * 0.002
        roll = random.random()

        if roll < FRAUD_RATIO:
            fraud_type = random.choice(["flood", "spoof", "bot"])
            if fraud_type == "flood":
                ip = random.choice(FLOOD_IPS)
                device_id = random.choice(DEVICE_POOL)
            elif fraud_type == "spoof":
                ip = random.choice(SPOOF_IPS)
                device_id = SPOOF_DEVICE
            else:  # bot
                ip = random.choice(IP_POOL[:10])
                device_id = random.choice(DEVICE_POOL[:5])
                ts = base_time + i * 0.002 + random.uniform(0, 0.01)  # 极短间隔
            is_fraud = True
        else:
            ip = random.choice(IP_POOL)
            device_id = random.choice(DEVICE_POOL)
            is_fraud = False

        events.append({
            "click_id":   str(uuid.uuid4()),
            "timestamp":  ts,
            "ip":         ip,
            "device_id":  device_id,
            "app_id":     random.choice(APP_IDS),
            "channel_id": random.choice(CHANNEL_IDS),
            "os":         random.choice(OS_IDS),
            "is_fraud":   is_fraud,
        })

    return events


def compute_features(events: list) -> pd.DataFrame:
    """
    离线批量计算特征，模拟线上 Redis 滑动窗口逻辑。
    """
    # 按时间排序
    events = sorted(events, key=lambda e: e["timestamp"])

    # 用于追踪历史状态
    ip_click_times = defaultdict(list)      # ip → [timestamps]
    device_ips = defaultdict(set)           # device_id → {ips}
    ip_last_click = {}                      # ip → last timestamp

    rows = []
    for ev in events:
        ip = ev["ip"]
        device_id = ev["device_id"]
        ts = ev["timestamp"]
        ts_ms = ts * 1000

        # 清理 1 分钟窗口外的记录
        ip_click_times[ip] = [t for t in ip_click_times[ip] if ts - t < 60]
        ip_click_count_1min = len(ip_click_times[ip])

        # 清理 1 小时窗口
        ip_click_times[ip].append(ts)
        ip_click_count_1hour = len([t for t in ip_click_times[ip] if ts - t < 3600])

        # 设备 IP 多样性
        device_ips[device_id].add(ip)
        device_ip_count = len(device_ips[device_id])

        # 点击间隔
        last_ts = ip_last_click.get(ip)
        click_interval_ms = (ts_ms - last_ts * 1000) if last_ts else -1
        ip_last_click[ip] = ts

        # 时段
        hour_of_day = int((ts % 86400) / 3600)

        rows.append({
            "ip_click_count_1min":  ip_click_count_1min,
            "ip_click_count_1hour": ip_click_count_1hour,
            "device_ip_count":      device_ip_count,
            "click_interval_ms":    click_interval_ms,
            "hour_of_day":          hour_of_day,
            "app_id":               ev["app_id"],
            "channel_id":           ev["channel_id"],
            "os":                   ev["os"],
            "is_blacklisted":       0,
            "is_fraud":             int(ev["is_fraud"]),
        })

    return pd.DataFrame(rows)


def main():
    print(f"生成 {N_SAMPLES:,} 条事件...")
    events = generate_events(N_SAMPLES)

    fraud_count = sum(1 for e in events if e["is_fraud"])
    print(f"  正常: {N_SAMPLES - fraud_count:,}  欺诈: {fraud_count:,} ({fraud_count/N_SAMPLES*100:.1f}%)")

    print("计算特征...")
    df = compute_features(events)

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"保存到 {OUTPUT_PATH}")
    print(f"数据集大小: {len(df):,} 行 x {len(df.columns)} 列")
    print(f"\n特征预览:")
    print(df.head(3).to_string())


if __name__ == "__main__":
    main()
