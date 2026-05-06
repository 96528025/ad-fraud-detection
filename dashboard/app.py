"""
Real-Time Dashboard — Flask + Chart.js

Endpoints:
  GET /           → dashboard HTML page
  GET /api/stats  → JSON with live metrics
  GET /api/recent → last 100 click events with fraud labels

Dashboard shows:
  - Events/sec (throughput)
  - Fraud rate % (rolling 5min)
  - Top 10 blocked IPs
  - Detection latency histogram (rule vs ML path)
  - Fraud events timeline chart

Usage:
  python dashboard/app.py
  → http://localhost:5000
"""

# TODO Phase 5:
# 1. Flask app with CORS enabled
# 2. /api/stats polls SQLite every 2s, returns JSON
# 3. /api/recent returns last 100 rows from clicks table
# 4. index.html with Chart.js: line chart + bar chart + table
# 5. Auto-refresh every 3 seconds via JS setInterval
