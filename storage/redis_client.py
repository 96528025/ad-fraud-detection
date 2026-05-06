"""
Redis Client — IP Blacklist + Sliding Window Counters

Two data structures:
  1. Blacklist SET: "blacklist" → {ip1, ip2, ...}
     - SISMEMBER for O(1) lookup
     - Per-key TTL via separate "blacklist:{ip}" keys

  2. Rate counters: "rate:{ip}:{window}" → int
     - INCR + EXPIRE for atomic sliding window
     - Separate keys for 1min and 1hour windows

  3. Device-IP tracker: "device:{device_id}:ips" → HyperLogLog
     - PFADD / PFCOUNT for memory-efficient unique IP count
     - ~0.81% error rate, uses <1KB per device
"""

# TODO Phase 2:
# 1. Class RedisClient(host, port)
# 2. increment_click_count(ip, window_seconds) -> int
# 3. get_click_count(ip, window_seconds) -> int
# 4. add_device_ip(device_id, ip)
# 5. get_device_ip_count(device_id) -> int (HyperLogLog)
# 6. add_to_blacklist(ip, ttl=3600)
# 7. is_blacklisted(ip) -> bool
# 8. set_last_click_time(ip, timestamp_ms)
# 9. get_last_click_time(ip) -> float | None
