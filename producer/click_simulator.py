"""
Click Simulator — Kafka Producer

Generates a realistic stream of ad click events and sends to Kafka.
Injects 3 fraud patterns at configurable rates:
  1. Click flooding: same IP sends >10 clicks/min
  2. Device spoofing: same device_id rotates through many IPs
  3. Bot clicks: clicks arrive at inhuman intervals (<50ms)

Event schema:
{
    "click_id":    str,   # UUID
    "timestamp":   float, # Unix epoch ms
    "ip":          str,   # IPv4
    "device_id":   str,
    "app_id":      int,
    "channel_id":  int,
    "os":          int,
    "click_time":  str,   # ISO 8601
    "is_fraud":    bool   # ground truth label (for evaluation)
}

Usage:
    python producer/click_simulator.py
"""

# TODO Phase 1:
# 1. Connect to Kafka broker (localhost:9092)
# 2. Build _generate_normal_click() using random realistic distributions
# 3. Build _inject_flood_fraud() — burst 20+ clicks from same IP
# 4. Build _inject_device_spoof_fraud() — rotate IPs for fixed device
# 5. Build _inject_bot_fraud() — clicks every 10–30ms
# 6. Main loop: mix normal (90%) + fraud (10%), send to 'ad-clicks' topic
# 7. Print throughput stats every 10 seconds
