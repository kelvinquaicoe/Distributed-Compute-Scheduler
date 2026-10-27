import pytest
from app.scheduler import Job, JobStatus, Scheduler

def test_fifo_dispatches_oldest_first():
    s = Scheduler(worker_count=1, cpu_per_worker=4, gpu_per_worker=1)
    first = s.submit(Job(name="first"))
    second = s.submit(Job(name="second"))
    assert [j.id for j in s.schedule("fifo")] == [first.id, second.id]

def test_priority_orders_high_priority_first():
    s = Scheduler(worker_count=1)
    low = s.submit(Job(name="low", priority=1))
    high = s.submit(Job(name="high", priority=9))
    assert [j.id for j in s.ordered_queue("priority")] == [high.id, low.id]

def test_sjf_orders_shortest_first():
    s = Scheduler(worker_count=1)
    long = s.submit(Job(name="long", estimated_seconds=100))
    short = s.submit(Job(name="short", estimated_seconds=2))
    assert [j.id for j in s.ordered_queue("sjf")] == [short.id, long.id]

def test_worker_failure_requeues_running_jobs():
    s = Scheduler(worker_count=1)
    job = s.submit(Job(name="work"))
    s.schedule("fifo")
    recovered = s.fail_worker("worker-01")
    assert [j.id for j in recovered] == [job.id]
    assert job.status == JobStatus.QUEUED
    assert job.worker_id is None

def test_invalid_policy_rejected():
    s = Scheduler()
    with pytest.raises(ValueError):
        s.schedule("magic")
