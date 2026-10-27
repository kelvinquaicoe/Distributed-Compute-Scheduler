"""Deterministic in-memory job and worker scheduling simulator."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from uuid import uuid4

class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Job:
    name: str
    resource: str = "cpu"
    cpu_cores: int = 1
    gpu_count: int = 0
    estimated_seconds: int = 30
    priority: int = 1
    id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.QUEUED
    worker_id: Optional[str] = None
    submitted_at: int = 0
    started_at: Optional[int] = None
    finished_at: Optional[int] = None
    failure_reason: Optional[str] = None

@dataclass
class Worker:
    id: str
    cpu_capacity: int = 8
    gpu_capacity: int = 1
    cpu_used: int = 0
    gpu_used: int = 0
    online: bool = True
    jobs: list[str] = field(default_factory=list)

    def can_run(self, job: Job) -> bool:
        return (self.online and self.cpu_used + job.cpu_cores <= self.cpu_capacity
                and self.gpu_used + job.gpu_count <= self.gpu_capacity)

class Scheduler:
    POLICIES = {"fifo", "priority", "sjf", "backfill"}

    def __init__(self, worker_count: int = 20, cpu_per_worker: int = 8, gpu_per_worker: int = 1):
        self.workers = [Worker(f"worker-{i+1:02d}", cpu_per_worker, gpu_per_worker)
                        for i in range(worker_count)]
        self.jobs: dict[str, Job] = {}
        self.clock = 0

    def submit(self, job: Job) -> Job:
        if job.resource not in {"cpu", "gpu", "mixed"}:
            raise ValueError("resource must be cpu, gpu, or mixed")
        if job.cpu_cores < 1 or job.gpu_count < 0 or job.estimated_seconds < 1:
            raise ValueError("resource requests and duration must be positive")
        if job.gpu_count > 0 and job.resource == "cpu":
            raise ValueError("CPU-only jobs cannot request GPUs")
        if job.resource == "gpu" and job.gpu_count < 1:
            raise ValueError("GPU jobs must request at least one GPU")
        job.submitted_at = self.clock
        self.jobs[job.id] = job
        return job

    def ordered_queue(self, policy: str) -> list[Job]:
        if policy not in self.POLICIES:
            raise ValueError(f"unknown policy: {policy}")
        queue = [j for j in self.jobs.values() if j.status == JobStatus.QUEUED]
        if policy == "priority":
            return sorted(queue, key=lambda j: (-j.priority, j.submitted_at, j.id))
        if policy == "sjf":
            return sorted(queue, key=lambda j: (j.estimated_seconds, j.submitted_at, j.id))
        if policy == "backfill":
            return sorted(queue, key=lambda j: (j.estimated_seconds, -j.priority, j.submitted_at))
        return sorted(queue, key=lambda j: (j.submitted_at, j.id))

    def schedule(self, policy: str = "fifo") -> list[Job]:
        dispatched = []
        for job in self.ordered_queue(policy):
            worker = next((w for w in self.workers if w.can_run(job)), None)
            if worker is None:
                continue
            worker.cpu_used += job.cpu_cores
            worker.gpu_used += job.gpu_count
            worker.jobs.append(job.id)
            job.worker_id = worker.id
            job.status = JobStatus.RUNNING
            job.started_at = self.clock
            dispatched.append(job)
        return dispatched

    def finish(self, job_id: str, failed: bool = False, reason: str = "simulated failure") -> Job:
        job = self.jobs[job_id]
        if job.status != JobStatus.RUNNING or not job.worker_id:
            raise ValueError("only running jobs can finish")
        worker = self.worker(job.worker_id)
        worker.cpu_used -= job.cpu_cores
        worker.gpu_used -= job.gpu_count
        if job_id in worker.jobs:
            worker.jobs.remove(job_id)
        job.status = JobStatus.FAILED if failed else JobStatus.COMPLETED
        job.finished_at = self.clock + job.estimated_seconds
        if failed:
            job.failure_reason = reason
        self.clock = max(self.clock, job.finished_at)
        return job

    def fail_worker(self, worker_id: str) -> list[Job]:
        worker = self.worker(worker_id)
        worker.online = False
        recovered = []
        for job_id in list(worker.jobs):
            job = self.jobs[job_id]
            worker.cpu_used -= job.cpu_cores
            worker.gpu_used -= job.gpu_count
            worker.jobs.remove(job_id)
            job.status = JobStatus.QUEUED
            job.worker_id = None
            job.started_at = None
            recovered.append(job)
        return recovered

    def worker(self, worker_id: str) -> Worker:
        for worker in self.workers:
            if worker.id == worker_id:
                return worker
        raise KeyError(worker_id)

    def summary(self) -> dict:
        counts = {status.value: sum(j.status == status for j in self.jobs.values())
                  for status in JobStatus}
        online = [w for w in self.workers if w.online]
        cpu_capacity = sum(w.cpu_capacity for w in online)
        gpu_capacity = sum(w.gpu_capacity for w in online)
        cpu_used = sum(w.cpu_used for w in online)
        gpu_used = sum(w.gpu_used for w in online)
        return {"job_counts": counts, "worker_count": len(self.workers),
                "online_workers": len(online),
                "cpu_utilization": cpu_used / cpu_capacity if cpu_capacity else 0,
                "gpu_utilization": gpu_used / gpu_capacity if gpu_capacity else 0}
