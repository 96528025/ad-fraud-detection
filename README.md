# Real-Time Ad Click Fraud Detection System

A production-inspired fraud detection pipeline that processes ad click streams in real time, combining rule-based logic and machine learning to identify and block fraudulent traffic.

Inspired by the architecture used in large-scale ads integrity systems (e.g., TikTok Business Integrity, Meta Ads Quality).

## Architecture

```
┌─────────────────────┐
│   Click Simulator   │  Generates realistic click events
│   (producer/)       │  with injected fraud patterns
└────────┬────────────┘
         │ produces ~500 events/sec
         ▼
┌─────────────────────┐
│   Apache Kafka      │  Topic: ad-clicks
│   (ad-clicks topic) │  Partitioned by IP prefix
└────────┬────────────┘
         │ consumes
         ▼
┌─────────────────────────────────────────────┐
│         Fraud Detection Consumer            │
│  ┌──────────────┐   ┌────────────────────┐  │
│  │   Feature    │   │    Rule Engine     │  │
│  │  Extractor   │──▶│  (instant block)   │  │
│  │              │   │  • click rate > 10/│  │
│  │ • rate/IP    │   │    min → BLOCK     │  │
│  │ • time delta │   │  • same device,    │  │
│  │ • device     │   │    100+ IPs → flag │  │
│  │ • channel    │   └────────────────────┘  │
│  └──────┬───────┘            │               │
│         │                    │               │
│         ▼                    ▼               │
│  ┌──────────────┐   ┌────────────────────┐  │
│  │   ML Model   │   │  Redis Blacklist   │  │
│  │  (XGBoost)   │   │  • IP blacklist    │  │
│  │  fraud score │   │  • rate counters   │  │
│  │  0.0 – 1.0   │   │  • sliding window  │  │
│  └──────┬───────┘   └────────────────────┘  │
└─────────┼──────────────────────────────────-┘
          │ labeled events
          ▼
┌─────────────────────┐     ┌──────────────────┐
│      SQLite DB      │────▶│    Dashboard     │
│  • all click events │     │  • fraud rate    │
│  • fraud labels     │     │  • blocked IPs   │
│  • model scores     │     │  • throughput    │
└─────────────────────┘     │  • latency p99   │
                            └──────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Message broker | Apache Kafka |
| Feature store / cache | Redis |
| ML model | XGBoost |
| Event storage | SQLite |
| Dashboard | Flask + Chart.js |
| Language | Python 3.10+ |

## Fraud Patterns Detected

| Pattern | Detection Method | Latency |
|---------|-----------------|---------|
| Click flooding (>10 clicks/min from same IP) | Rule engine | <1ms |
| Device spoofing (same device, 100+ IPs) | Rule engine | <1ms |
| Bot-like click intervals (<50ms between clicks) | Rule engine | <1ms |
| Coordinated fraud (correlated IP clusters) | ML model | ~10ms |
| Abnormal time-of-day patterns | ML model | ~10ms |
| App/channel mismatch anomalies | ML model | ~10ms |

## Dataset

Training uses the [TalkingData Ad Tracking Fraud Detection](https://www.kaggle.com/c/talkingdata-adtracking-fraud-detection) dataset from Kaggle — a real-world click fraud dataset with 240M+ records.

Download and place in `data/train.csv` (not committed to repo).

## Project Structure

```
ad-fraud-detection/
├── producer/
│   └── click_simulator.py      # Simulate click stream with fraud injection
├── consumer/
│   ├── feature_extractor.py    # Extract features from raw click events
│   ├── rule_engine.py          # Fast rule-based fraud detection
│   └── ml_detector.py          # XGBoost model inference
├── model/
│   ├── train.py                # Train model on TalkingData dataset
│   └── evaluate.py             # AUC, precision, recall, F1 metrics
├── storage/
│   ├── redis_client.py         # IP blacklist + sliding window counters
│   └── db.py                   # SQLite event log
├── dashboard/
│   └── app.py                  # Flask real-time dashboard
├── data/
│   └── .gitkeep
├── docs/
│   └── design.md               # Detailed design decisions
├── requirements.txt
└── README.md
```

## Implementation Roadmap

### Phase 1 — Data Pipeline (Week 1)
- [x] Project setup and architecture design
- [ ] `click_simulator.py`: generate realistic click events (normal + 3 fraud patterns)
- [ ] Kafka topic setup (`ad-clicks`, partitioned by IP prefix)
- [ ] Basic consumer that reads and prints events
- [ ] `db.py`: SQLite schema for event log

### Phase 2 — Rule Engine (Week 1–2)
- [ ] `redis_client.py`: sliding window rate counter per IP
- [ ] `rule_engine.py`: implement 3 hard rules (flood, device spoof, bot interval)
- [ ] Integration test: inject fraud events, verify detection rate >95%

### Phase 3 — ML Model (Week 2–3)
- [ ] `train.py`: feature engineering on TalkingData dataset
  - Features: ip_click_rate, device_click_count, app_channel_ratio, hour_of_day, click_interval_mean
- [ ] Train XGBoost classifier, target AUC >0.97
- [ ] `ml_detector.py`: load model, score events in real time
- [ ] `evaluate.py`: precision/recall/F1 on held-out test set

### Phase 4 — Integration & Performance (Week 3–4)
- [ ] End-to-end pipeline: simulator → Kafka → consumer → Redis + SQLite
- [ ] Throughput benchmark: target >1,000 events/sec
- [ ] Latency measurement: rule engine p99 <2ms, ML p99 <20ms
- [ ] IP blacklist auto-expiry (TTL in Redis)

### Phase 5 — Dashboard (Week 4)
- [ ] Flask app serving real-time stats from SQLite
- [ ] Charts: fraud rate over time, top blocked IPs, detection latency histogram
- [ ] README with demo GIF

## Key Design Decisions

**Why Kafka?**
Decouples click ingestion from detection. If the ML model is slow, clicks buffer in Kafka instead of being dropped. Same architecture TikTok uses for ads event processing.

**Why two detection layers?**
Rule engine handles obvious fraud instantly (<1ms). ML handles subtle patterns that rules miss. Combining both minimizes false negatives while keeping latency low.

**Why Redis for rate counting?**
Sliding window counters need atomic increment + expiry. Redis `INCR` + `EXPIRE` is O(1) and survives consumer restarts.

**Why XGBoost over deep learning?**
Tabular fraud features respond better to tree models. XGBoost gives better AUC on TalkingData than MLP with less tuning. In production, TikTok uses gradient boosting for first-stage filtering before neural rankers.

## Results (target)

| Metric | Target |
|--------|--------|
| AUC-ROC | >0.97 |
| Precision | >0.90 |
| Recall | >0.85 |
| Throughput | >1,000 events/sec |
| Rule engine latency (p99) | <2ms |
| ML latency (p99) | <20ms |

## How to Run

```bash
# 1. Start Kafka (requires Docker)
docker-compose up -d

# 2. Install dependencies
pip install -r requirements.txt

# 3. Train model (requires TalkingData dataset in data/)
python model/train.py

# 4. Start fraud detection consumer
python consumer/ml_detector.py

# 5. Start click simulator
python producer/click_simulator.py

# 6. Open dashboard
python dashboard/app.py
# → http://localhost:5000
```

## Author

Freja Ren · [GitHub](https://github.com/96528025)
