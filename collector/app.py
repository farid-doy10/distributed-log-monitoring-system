import os
from datetime import datetime, timezone
from typing import List, Optional

import psycopg2
from fastapi import FastAPI
from pydantic import BaseModel, Field

DATABASE_URL = os.environ["DATABASE_URL"]

app = FastAPI(title="Log Collector")

class LogEvent(BaseModel):
    ts: Optional[str] = None
    service: str = Field(..., min_length=1)
    level: str = Field(..., min_length=1)  # INFO/WARN/ERROR
    message: str = Field(..., min_length=1)
    latency_ms: Optional[int] = None
    status_code: Optional[int] = None

def get_conn():
    return psycopg2.connect(DATABASE_URL)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/logs")
def ingest_logs(events: List[LogEvent]):
    rows = []
    for e in events:
        ts = datetime.now(timezone.utc) if not e.ts else datetime.fromisoformat(e.ts.replace("Z", "+00:00"))
        rows.append((ts, e.service, e.level, e.message, e.latency_ms, e.status_code))

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.executemany(
                    "INSERT INTO logs (ts, service, level, message, latency_ms, status_code) VALUES (%s,%s,%s,%s,%s,%s)",
                    rows,
                )
        return {"ingested": len(rows)}
    finally:
        conn.close()

@app.get("/incidents")
def list_incidents(limit: int = 20):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT created_at, service, incident_type, severity, summary, window_start, window_end
                FROM incidents
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

        return [
            {
                "created_at": r[0].isoformat(),
                "service": r[1],
                "incident_type": r[2],
                "severity": r[3],
                "summary": r[4],
                "window_start": r[5].isoformat(),
                "window_end": r[6].isoformat(),
            }
            for r in rows
        ]
    finally:
        conn.close()

@app.get("/stats")
def stats(window_minutes: int = 5):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT service,
                       COUNT(*) AS total,
                       SUM(CASE WHEN level='ERROR' THEN 1 ELSE 0 END) AS errors
                FROM logs
                WHERE ts > now() - (%s || ' minutes')::interval
                GROUP BY service
                ORDER BY errors DESC
                """,
                (window_minutes,),
            )
            rows = cur.fetchall()

        out = []
        for service, total, errors in rows:
            total = int(total)
            errors = int(errors or 0)
            err_rate = (errors / total) if total > 0 else 0.0
            out.append(
                {"service": service, "window_minutes": window_minutes, "total": total, "errors": errors, "error_rate": err_rate}
            )
        return out
    finally:
        conn.close()
