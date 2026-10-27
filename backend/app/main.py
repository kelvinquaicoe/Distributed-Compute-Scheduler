from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from .scheduler import Job, Scheduler

app = FastAPI(title="Distributed Compute Scheduler", version="0.1.0")
scheduler = Scheduler(worker_count=20)

class JobRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    resource: str = "cpu"
    cpu_cores: int = Field(default=1, ge=1)
    gpu_count: int = Field(default=0, ge=0)
    estimated_seconds: int = Field(default=30, ge=1)
    priority: int = Field(default=1, ge=0, le=10)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/summary")
def summary():
    return scheduler.summary()

@app.get("/workers")
def workers():
    return [{"id": w.id, "online": w.online, "cpu_capacity": w.cpu_capacity,
             "gpu_capacity": w.gpu_capacity, "cpu_used": w.cpu_used,
             "gpu_used": w.gpu_used, "jobs": w.jobs} for w in scheduler.workers]

@app.post("/jobs", status_code=201)
def submit_job(payload: JobRequest):
    try:
        job = scheduler.submit(Job(**payload.model_dump()))
        return job.__dict__ | {"status": job.status.value}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

@app.get("/jobs")
def list_jobs():
    return [j.__dict__ | {"status": j.status.value} for j in scheduler.jobs.values()]

@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    job = scheduler.jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return job.__dict__ | {"status": job.status.value}

@app.post("/schedule/{policy}")
def schedule(policy: str):
    try:
        dispatched = scheduler.schedule(policy.lower())
        return {"dispatched": [j.id for j in dispatched], "count": len(dispatched)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

@app.post("/jobs/{job_id}/finish")
def finish_job(job_id: str, failed: bool = False):
    try:
        job = scheduler.finish(job_id, failed=failed)
        return job.__dict__ | {"status": job.status.value}
    except KeyError:
        raise HTTPException(status_code=404, detail="job not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))

@app.post("/workers/{worker_id}/fail")
def fail_worker(worker_id: str):
    try:
        recovered = scheduler.fail_worker(worker_id)
        return {"worker_id": worker_id, "requeued_job_ids": [j.id for j in recovered]}
    except KeyError:
        raise HTTPException(status_code=404, detail="worker not found")
