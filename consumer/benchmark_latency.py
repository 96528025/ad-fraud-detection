"""
延迟基准测试 —— 直接复用线上处理路径，分别测量：

  1. 规则引擎单独延迟   rule_engine.evaluate()
  2. 端到端检测延迟     规则引擎 + 特征提取 + ML 打分（与 ml_detector 的 latency_ms 口径一致）

输出 p50 / p95 / p99 / p99.9 / max，而不是平均值。

依赖：本地 Redis（localhost:6379）+ model/fraud_model.pkl
用法：
    python consumer/benchmark_latency.py [n_events]
"""

import sys
import os
import time
import random

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from consumer.rule_engine import RuleEngine
from consumer.feature_extractor import FeatureExtractor
from consumer.ml_detector import ml_score          # 复用同一个已加载的模型
from storage.redis_client import RedisClient
from producer.click_simulator import (
    normal_click, flood_click, device_spoof_click, bot_click, FRAUD_RATIO,
)

N_EVENTS = int(sys.argv[1]) if len(sys.argv) > 1 else 20_000
N_WARMUP = 2_000


def gen_event() -> dict:
    """按线上同样的 10% 欺诈比例生成事件。"""
    if random.random() < FRAUD_RATIO:
        return random.choice([flood_click, device_spoof_click, bot_click])()
    return normal_click()


def pct(arr, p):
    return np.percentile(arr, p)


def report(name: str, samples_ms: np.ndarray):
    print(f"\n{name}  (n={len(samples_ms):,})")
    print(f"  p50   = {pct(samples_ms, 50):.3f} ms")
    print(f"  p95   = {pct(samples_ms, 95):.3f} ms")
    print(f"  p99   = {pct(samples_ms, 99):.3f} ms")
    print(f"  p99.9 = {pct(samples_ms, 99.9):.3f} ms")
    print(f"  max   = {samples_ms.max():.3f} ms   mean = {samples_ms.mean():.3f} ms")


def main():
    redis = RedisClient()
    rule_engine = RuleEngine(redis)
    feature_extractor = FeatureExtractor(redis)

    print(f"预热 {N_WARMUP:,} 条，测量 {N_EVENTS:,} 条 ...")

    # 预热（加载路径、填充 Redis 状态），不计入统计
    for _ in range(N_WARMUP):
        e = gen_event()
        rule_engine.evaluate(e)
        ml_score(feature_extractor.extract(e))

    rule_ms = np.empty(N_EVENTS)
    e2e_ms  = np.empty(N_EVENTS)

    for i in range(N_EVENTS):
        e = gen_event()

        # ── 端到端计时（口径与 ml_detector.latency_ms 完全一致）──
        t0 = time.perf_counter()
        rule_result = rule_engine.evaluate(e)          # 规则引擎
        t_rule = time.perf_counter()
        features = feature_extractor.extract(e)        # 特征提取
        _ = ml_score(features)                         # ML 打分
        t_end = time.perf_counter()

        rule_ms[i] = (t_rule - t0)  * 1000
        e2e_ms[i]  = (t_end - t0)   * 1000

    report("规则引擎 (rule engine only)", rule_ms)
    report("端到端 (rule + features + ML)", e2e_ms)


if __name__ == "__main__":
    main()
