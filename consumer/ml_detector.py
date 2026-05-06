"""
ML Detector — Main Consumer Entry Point

Reads from Kafka 'ad-clicks' topic, runs the full detection pipeline:
  1. Deserialize event JSON
  2. Extract features (FeatureExtractor)
  3. Rule engine check (RuleEngine) — if BLOCK, skip ML
  4. ML model score (XGBoost) — if score > threshold, BLOCK
  5. Write result to SQLite
  6. Update Redis counters

Pipeline latency targets:
  - Rule engine path: p99 < 2ms
  - ML path:          p99 < 20ms
  - End-to-end:       p99 < 25ms
"""

# TODO Phase 3:
# 1. Load XGBoost model from model/fraud_model.pkl at startup
# 2. KafkaConsumer loop reading from 'ad-clicks'
# 3. For each message: extract → rule check → ml score → store
# 4. Print rolling stats: events/sec, fraud rate, avg latency
# 5. Graceful shutdown on SIGINT (flush pending writes to SQLite)
