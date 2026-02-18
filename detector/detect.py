import os
import time
from datetime import datetime, timezone, timedelta
import psycopg2

DATABASE_URL = os.environ["DATABASE_URL"]

def get_conn_with_retry(retries=30, sleep_seconds=2):
    last_err = None
    for _ in range(retries):
        try:
            return psycopg2.connect(DATABASE_URL)
        except Exception as e:
            last_err = e
            print(f"[detector] DB not ready yet, retrying in {sleep_seconds}s...")
            time.sleep(sleep_seconds)
    raise last_err

def check_error_spike(conn, service, window_minutes=5):
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=window_minutes)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM logs
            WHERE service=%s AND level='ERROR' AND ts >= %s AND ts <= %s
            """,
            (service, window_start, now),
        )
        err_count = cur.fetchone()[0]

    # Simple threshold for demo (you can improve later)
    if err_count >= 20:
        severity = "HIGH"
        summary = f"ERROR spike: {err_count} errors in last {window_minutes} min"
        return ("ERROR_SPIKE", severity, summary, window_start, now)
    return None

def check_latency_spike(conn, service, window_minutes=5):
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=window_minutes)

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms)
            FROM logs
            WHERE service=%s AND latency_ms IS NOT NULL AND ts >= %s AND ts <= %s
            """,
            (service, window_start, now),
        )
        p95 = cur.fetchone()[0]

    if p95 is not None and p95 >= 800:
        severity = "MED"
        summary = f"Latency spike: p95={int(p95)}ms in last {window_minutes} min"
        return ("LATENCY_SPIKE", severity, summary, window_start, now)
    return None

def incident_exists(conn, service, incident_type, window_end, dedupe_minutes=10):
    since = window_end - timedelta(minutes=dedupe_minutes)
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM incidents
            WHERE service=%s AND incident_type=%s AND created_at >= %s
            """,
            (service, incident_type, since),
        )
        return cur.fetchone()[0] > 0

def create_incident(conn, service, incident_type, severity, summary, window_start, window_end):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO incidents (created_at, service, incident_type, severity, summary, window_start, window_end)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            """,
            (datetime.now(timezone.utc), service, incident_type, severity, summary, window_start, window_end),
        )

def main():
    services = ["auth-service", "feed-service", "db-service"]
    while True:
        conn = get_conn_with_retry()
        try:
            with conn:
                for svc in services:
                    for checker in (check_error_spike, check_latency_spike):
                        result = checker(conn, svc)
                        if result:
                            incident_type, severity, summary, ws, we = result
                            if not incident_exists(conn, svc, incident_type, we):
                                create_incident(conn, svc, incident_type, severity, summary, ws, we)
                                print(f"[INCIDENT] {svc} {incident_type} {severity} - {summary}")
        finally:
            conn.close()

        time.sleep(10)

if __name__ == "__main__":
    main()
