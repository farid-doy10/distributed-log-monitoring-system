# Distributed Log Monitoring & Incident Detection System

A production-style log ingestion and anomaly detection pipeline demonstrating backend infrastructure, reliability engineering, and operational debugging workflows.

This project simulates multiple backend services generating structured logs, stores them in PostgreSQL, detects error-rate anomalies, and exposes incidents through a REST API.

The system is fully containerised using Docker and designed to resemble real production monitoring pipelines used in large-scale distributed systems.

---

## Overview

Modern backend systems require strong observability to detect failures early.

This project implements a lightweight monitoring stack that:

- Ingests logs from multiple simulated services  
- Stores structured events in PostgreSQL  
- Detects abnormal error spikes  
- Automatically creates incidents  
- Exposes debugging and monitoring endpoints  

---

## Architecture

Services run using Docker Compose:

- **generator** – simulates backend services (`auth-service`, `feed-service`, `db-service`)
- **collector (FastAPI)** – receives logs via REST API and stores them
- **detector** – analyses logs and creates incidents
- **db (PostgreSQL)** – stores logs and incidents

### Data Flow

generator → collector → PostgreSQL (logs)  
detector → PostgreSQL (incidents)  
collector → `/incidents` & `/stats`

---

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- Docker & Docker Compose
- Linux-based container workflows

---

## Running the Project

### Requirements

- Docker Desktop installed and running

### Start the system

```bash
docker compose up --build
```

### Stop the system

```bash
docker compose down
```

---

## API Endpoints

### Health Check

```
GET /health
```

### View Incidents

```
GET /incidents?limit=20
```

### Service Statistics

```
GET /stats?window_minutes=5
```

---

## Operational Runbook

Connect to DB:

```bash
docker exec -it meta-pe-log-monitor-db-1 psql -U app -d logsdb
```

Check containers:

```bash
docker ps
docker logs meta-pe-log-monitor-detector-1 --tail 100
```

---

## Design Goals

- Containerised backend architecture  
- Reliability monitoring workflows  
- Incident detection and debugging  
- Linux/Docker deployment  

---

## Author

Ahmed Farid Al Basir  
MSc Artificial Intelligence — University of Sheffield
