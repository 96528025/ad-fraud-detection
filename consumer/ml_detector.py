import json
import time
import sys
import os
from pathlib import Path

import joblib
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka import KafkaConsumer
from storage.db import ClickDB
from storage.redis_client import RedisClient
from consumer.rule_engine import RuleEngine
from consumer.feature_extractor import FeatureExtractor

KAFKA_BROKER = "localhost:9092"
TOPIC = "ad-clicks"
ML_THRESHOLD = 0.5
MODEL_PATH = Path(__file__).parent.parent / "model" / "fraud_model.pkl"

FEATURES = [
    "ip_click_count_1min",
    "ip_click_count_1hour",
    "device_ip_count",
    "click_interval_ms",
    "hour_of_day",
    "app_id",
    "channel_id",
    "os",
    "is_blacklisted",
]

# 启动时加载模型（只加载一次）
_model = joblib.load(MODEL_PATH)


def ml_score(features: dict) -> float:
    df = pd.DataFrame([features])[FEATURES]
    return float(_model.predict_proba(df)[0][1])


def main():
    db = ClickDB()
    redis = RedisClient()
    rule_engine = RuleEngine(redis)
    feature_extractor = FeatureExtractor(redis)

    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="latest",
        group_id="fraud-detector",
    )

    print(f"Listening on Kafka topic '{TOPIC}' ... (Ctrl+C to stop)\n")

    total = 0
    blocked = 0
    flagged = 0
    start = time.time()

    for message in consumer:
        t0 = time.time()
        event = message.value

        # 1. 规则引擎
        rule_result = rule_engine.evaluate(event)

        # 2. 特征提取 + ML 评分（规则已拦截的也算分，供记录用）
        features = feature_extractor.extract(event)
        score = ml_score(features)

        # 3. 最终决定
        if rule_result["action"] == "BLOCK":
            final_action = "BLOCK"
        elif rule_result["action"] == "FLAG" or score >= ML_THRESHOLD:
            final_action = "BLOCK"
        else:
            final_action = "ALLOW"

        latency_ms = (time.time() - t0) * 1000

        # 4. 写入数据库
        db.insert_click(
            event=event,
            rule_action=rule_result["action"],
            rule_name=rule_result["rule"],
            ml_score=score,
            final_action=final_action,
            latency_ms=latency_ms,
        )

        # 5. 统计
        total += 1
        if final_action == "BLOCK":
            blocked += 1
        elif rule_result["action"] == "FLAG":
            flagged += 1

        if total % 100 == 0:
            elapsed = time.time() - start
            print(f"  total={total:,}  blocked={blocked:,} ({blocked/total*100:.1f}%)  "
                  f"flagged={flagged:,}  rate={total/elapsed:.0f} events/sec  "
                  f"latency={latency_ms:.1f}ms")


if __name__ == "__main__":
    main()
