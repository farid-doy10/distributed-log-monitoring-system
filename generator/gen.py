import os
import time
import random
from datetime import datetime, timezone
import requests

COLLECTOR_URL = os.environ["COLLECTOR_URL"]

SERVICES = ["auth-service", "feed-service", "db-service"]
LEVELS = ["INFO", "WARN", "ERROR"]

def make_log(service, anomaly=False):
    level = "ERROR" if anomaly and random.random() < 0.7 else random.choices(LEVELS, weights=[80, 15, 5])[0]
    latency = int(random.gauss(120, 30))
    if anomaly and random.random() < 0.5:
        latency *= 5  # latency spike
    latency = max(latency, 1)
    status = 200 if level != "ERROR" else random.choice([500, 502, 503])
    msg = "request ok" if level == "INFO" else ("slow response" if level == "WARN" else "request failed")

    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "level": level,
        "message": msg,
        "latency_ms": latency,
        "status_code": status,
    }

def main():
    t0 = time.time()
    while True:
        # Every ~60 seconds it inject an anomaly window for demo
        anomaly = (int(time.time() - t0) % 60) in range(10, 20)

        batch = []
        for _ in range(30):  # logs per loop
            svc = random.choice(SERVICES)
            batch.append(make_log(svc, anomaly=anomaly))

        try:
            r = requests.post(COLLECTOR_URL, json=batch, timeout=5)
            print("sent", len(batch), "status", r.status_code)
        except Exception as e:
            print("send failed:", e)

        time.sleep(1)

if __name__ == "__main__":
    main()
