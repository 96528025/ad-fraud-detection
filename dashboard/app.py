import sys
import os
import time
import sqlite3
from pathlib import Path
from flask import Flask, jsonify, render_template
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

DB_PATH = Path(__file__).parent.parent / "data" / "clicks.db"


def query(sql, params=()):
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def stats():
    now = time.time()

    rows = query("""
        SELECT
            COUNT(*)                                        AS total,
            SUM(CASE WHEN final_action='BLOCK' THEN 1 ELSE 0 END) AS blocked,
            ROUND(AVG(latency_ms), 2)                       AS avg_latency_ms,
            ROUND(AVG(CASE WHEN timestamp > ? THEN
                CAST(final_action='BLOCK' AS FLOAT) END) * 100, 1) AS fraud_rate_5min
        FROM clicks
    """, (now - 300,))

    # 每分钟分组的欺诈率（最近10分钟，用于折线图）
    timeline = query("""
        SELECT
            CAST((timestamp - ?) / 60 AS INT)   AS minute_ago,
            COUNT(*)                             AS total,
            SUM(CASE WHEN final_action='BLOCK' THEN 1 ELSE 0 END) AS blocked
        FROM clicks
        WHERE timestamp > ?
        GROUP BY minute_ago
        ORDER BY minute_ago
    """, (now, now - 600))

    # Top 5 封禁 IP
    top_ips = query("""
        SELECT ip, COUNT(*) AS count
        FROM clicks
        WHERE final_action='BLOCK'
        GROUP BY ip
        ORDER BY count DESC
        LIMIT 5
    """)

    return jsonify({
        "summary": rows[0] if rows else {},
        "timeline": timeline,
        "top_blocked_ips": top_ips,
    })


@app.route("/api/recent")
def recent():
    rows = query("""
        SELECT click_id, ip, device_id, final_action, rule_name,
               ROUND(ml_score, 3) AS ml_score,
               ROUND(latency_ms, 2) AS latency_ms,
               datetime(timestamp, 'unixepoch', 'localtime') AS time
        FROM clicks
        ORDER BY timestamp DESC
        LIMIT 50
    """)
    return jsonify(rows)


if __name__ == "__main__":
    app.run(debug=True, port=5001)
