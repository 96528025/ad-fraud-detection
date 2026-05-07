import json
import random
import time
import uuid
from kafka import KafkaProducer

KAFKA_BROKER = "localhost:9092"
TOPIC = "ad-clicks"

FRAUD_RATIO = 0.10  # 10% of events are fraudulent

# Pools of realistic-looking values
IP_POOL = [f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
           for _ in range(500)]
DEVICE_POOL = [f"dev_{i:05d}" for i in range(200)]
APP_IDS = list(range(1, 50))
CHANNEL_IDS = list(range(1, 20))
OS_IDS = [0, 1, 2, 3]  # android, ios, windows, other

# Fixed pools for fraud patterns
FLOOD_IPS = random.sample(IP_POOL, 5)          # IPs that will flood clicks
SPOOF_DEVICE = "dev_99999"                      # device that rotates IPs
SPOOF_IPS = [f"10.0.{i}.{j}" for i in range(10) for j in range(10)]  # 100 IPs


def make_event(ip, device_id, is_fraud=False):
    return {
        "click_id":  str(uuid.uuid4()),
        "timestamp": time.time(),
        "ip":        ip,
        "device_id": device_id,
        "app_id":    random.choice(APP_IDS),
        "channel_id": random.choice(CHANNEL_IDS),
        "os":        random.choice(OS_IDS),
        "is_fraud":  is_fraud,
    }


def normal_click():
    return make_event(
        ip=random.choice(IP_POOL),
        device_id=random.choice(DEVICE_POOL),
        is_fraud=False,
    )


def flood_click():
    """同一个 IP 短时间内大量点击"""
    return make_event(
        ip=random.choice(FLOOD_IPS),
        device_id=random.choice(DEVICE_POOL),
        is_fraud=True,
    )


def device_spoof_click():
    """同一个设备 ID 轮换大量不同 IP"""
    return make_event(
        ip=random.choice(SPOOF_IPS),
        device_id=SPOOF_DEVICE,
        is_fraud=True,
    )


def bot_click():
    """点击间隔极短（模拟机器人）"""
    return make_event(
        ip=random.choice(IP_POOL[:10]),
        device_id=random.choice(DEVICE_POOL[:5]),
        is_fraud=True,
    )


def main():
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    print(f"Sending to Kafka topic '{TOPIC}' ... (Ctrl+C to stop)\n")

    sent = 0
    fraud_sent = 0
    start = time.time()

    while True:
        roll = random.random()

        if roll < FRAUD_RATIO:
            fraud_type = random.choice(["flood", "spoof", "bot"])
            if fraud_type == "flood":
                event = flood_click()
            elif fraud_type == "spoof":
                event = device_spoof_click()
            else:
                event = bot_click()
                time.sleep(0.01)  # bot clicks arrive ~10ms apart
            fraud_sent += 1
        else:
            event = normal_click()

        producer.send(TOPIC, value=event)
        sent += 1

        # Print stats every 100 events
        if sent % 100 == 0:
            elapsed = time.time() - start
            print(f"  sent={sent:,}  fraud={fraud_sent:,} ({fraud_sent/sent*100:.1f}%)  "
                  f"rate={sent/elapsed:.0f} events/sec")

        time.sleep(0.002)  # ~500 events/sec


if __name__ == "__main__":
    main()
