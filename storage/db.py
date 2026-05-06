"""
SQLite Event Log

Schema:
  clicks table:
    click_id      TEXT PRIMARY KEY
    timestamp     REAL
    ip            TEXT
    device_id     TEXT
    app_id        INTEGER
    channel_id    INTEGER
    os            INTEGER
    is_fraud_gt   INTEGER  -- ground truth (from simulator)
    rule_action   TEXT     -- BLOCK / FLAG / ALLOW
    rule_name     TEXT     -- which rule triggered
    ml_score      REAL     -- XGBoost fraud probability
    final_action  TEXT     -- combined decision
    latency_ms    REAL     -- end-to-end detection latency
"""

# TODO Phase 1:
# 1. Class ClickDB(db_path)
# 2. create_tables() — run once on init
# 3. insert_click(event_dict, rule_result, ml_score, latency_ms)
# 4. get_stats() -> dict with fraud_rate, blocked_count, avg_latency
#    (used by dashboard)
# 5. get_recent_clicks(limit=100) -> list of dicts
