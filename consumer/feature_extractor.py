"""
Feature Extractor

Transforms raw click events into feature vectors for the ML model.
Reads sliding-window statistics from Redis.

Features extracted:
  - ip_click_count_1min:     clicks from this IP in last 60s (from Redis)
  - ip_click_count_1hour:    clicks from this IP in last 3600s (from Redis)
  - device_ip_count_1hour:   unique IPs seen for this device_id (from Redis)
  - click_interval_ms:       ms since previous click from this IP
  - hour_of_day:             0–23, captures time-of-day fraud patterns
  - app_channel_seen_count:  how often this (app, channel) pair appears
  - os_device_mismatch:      1 if OS/device combo is unusual
"""

# TODO Phase 2:
# 1. Class FeatureExtractor(redis_client)
# 2. extract(event: dict) -> dict of feature values
# 3. Use Redis INCR + EXPIRE for sliding window counters
# 4. Track last-click-time per IP in Redis for interval calculation
# 5. Return feature dict ready to feed into RuleEngine and MLDetector
