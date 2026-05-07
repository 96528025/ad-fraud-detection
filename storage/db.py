import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "clicks.db"


class ClickDB:
    def __init__(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS clicks (
                click_id      TEXT PRIMARY KEY,
                timestamp     REAL,
                ip            TEXT,
                device_id     TEXT,
                app_id        INTEGER,
                channel_id    INTEGER,
                os            INTEGER,
                is_fraud_gt   INTEGER,
                rule_action   TEXT,
                rule_name     TEXT,
                ml_score      REAL,
                final_action  TEXT,
                latency_ms    REAL
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ip ON clicks(ip)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ts ON clicks(timestamp)")
        self.conn.commit()

    def insert_click(self, event: dict, rule_action: str = None,
                     rule_name: str = None, ml_score: float = None,
                     final_action: str = None, latency_ms: float = None):
        self.conn.execute("""
            INSERT OR IGNORE INTO clicks VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            event["click_id"],
            event["timestamp"],
            event["ip"],
            event["device_id"],
            event["app_id"],
            event["channel_id"],
            event["os"],
            int(event.get("is_fraud", False)),
            rule_action,
            rule_name,
            ml_score,
            final_action,
            latency_ms,
        ))
        self.conn.commit()

    def get_stats(self) -> dict:
        row = self.conn.execute("""
            SELECT
                COUNT(*)                                      AS total,
                SUM(is_fraud_gt)                              AS total_fraud_gt,
                SUM(final_action = 'BLOCK')                   AS total_blocked,
                AVG(latency_ms)                               AS avg_latency_ms,
                AVG(CASE WHEN timestamp > ? THEN
                    CAST(is_fraud_gt AS FLOAT) END)           AS fraud_rate_5min
            FROM clicks
        """, (time.time() - 300,)).fetchone()
        return dict(row)

    def get_recent_clicks(self, limit: int = 100) -> list:
        rows = self.conn.execute("""
            SELECT * FROM clicks ORDER BY timestamp DESC LIMIT ?
        """, (limit,)).fetchall()
        return [dict(r) for r in rows]
