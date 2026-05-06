"""
Rule Engine — Fast First-Line Fraud Detection

Hard rules that catch obvious fraud instantly (<1ms).
Runs before the ML model to reduce load and latency.

Rules:
  RULE-01  ip_click_count_1min > 10        → BLOCK (click flood)
  RULE-02  device_ip_count_1hour > 50      → FLAG  (device spoofing)
  RULE-03  click_interval_ms < 50          → BLOCK (bot behavior)
  RULE-04  ip in redis blacklist            → BLOCK (known bad actor)

Returns:
  {"action": "BLOCK" | "FLAG" | "ALLOW", "rule": "RULE-01" | None}
"""

# TODO Phase 2:
# 1. Class RuleEngine(redis_client)
# 2. evaluate(features: dict) -> {"action": str, "rule": str | None}
# 3. check_blacklist(ip) using Redis SET lookup
# 4. add_to_blacklist(ip, ttl_seconds=3600) for auto-expiring bans
# 5. Unit tests: inject feature dicts, assert correct action returned
