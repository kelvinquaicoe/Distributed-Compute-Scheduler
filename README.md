# Distributed Compute Scheduler

A distributed-systems project that simulates CPU/GPU job scheduling across worker nodes. It provides a FastAPI REST API and a React + TypeScript dashboard, with scheduling policies, worker-failure simulation, and benchmark utilities.

## Features

- Submit jobs with CPU/GPU resource requests, estimated runtimes, and priorities.
- Compare FIFO, priority, shortest-job-first (SJF), and backfill scheduling policies.
- Simulate worker capacity, job dispatch, completion, and worker failures.
- Inspect job states and worker utilization through the API and dashboard.
- Run repeatable benchmark workloads to compare scheduling outcomes.

> **Benchmark honesty:** Treat figures such as 10,000+ jobs, 20 workers, +24% GPU utilization, -37% queue wait, and 99.8% completion under failures as targets until you have run and saved reproducible benchmark results. Do not present them as verified measurements without evidence.

## Tech stack

Python, FastAPI, Pydantic, React, TypeScript, Vite, Docker Compose. The initial simulator uses in-memory state and simulated job execution; it does not launch real GPU workloads.

## Quick start: backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API documentation.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/summary` | Job counts and resource utilization |
| GET | `/workers` | Worker inventory and capacity |
| POST | `/jobs` | Submit a job |
| GET | `/jobs` | List jobs |
| GET | `/jobs/{job_id}` | Inspect one job |
| POST | `/schedule/{policy}` | Dispatch jobs using `fifo`, `priority`, `sjf`, or `backfill` |
| POST | `/jobs/{job_id}/finish` | Simulate job completion; pass `failed=true` to simulate failure |
| POST | `/workers/{worker_id}/fail` | Simulate a worker failure and requeue its running jobs |

Example request:

```json
{
  "name": "image-batch-001",
  "resource": "gpu",
  "cpu_cores": 2,
  "gpu_count": 1,
  "estimated_seconds": 60,
  "priority": 5
}
```

## Run tests

```bash
cd backend
pytest
```

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Set `VITE_API_URL=http://127.0.0.1:8000` if the API is hosted elsewhere.

## Structure

- `backend/app/scheduler.py` — jobs, workers, resource accounting, scheduling policies
- `backend/app/main.py` — FastAPI endpoints
- `backend/tests/` — scheduler tests
- `frontend/` — React + TypeScript dashboard
- `docs/benchmarking.md` — benchmark methodology

## Limitations and next steps

This is an educational simulator, not a production cluster manager. Jobs are simulated, state is in memory, and the backfill policy is a simple capacity-filling heuristic rather than a reservation-based cluster scheduler. Persistence, real worker agents, authentication, and distributed coordination are possible future extensions.
