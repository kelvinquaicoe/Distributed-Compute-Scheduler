# Benchmarking protocol

Do not report target metrics as measured until benchmark runs have been executed and the output saved.

1. Generate at least 10,000 jobs with a fixed random seed and document CPU/GPU request distributions and runtimes.
2. Use the same 20-worker configuration for FIFO, priority, SJF, and backfill.
3. Compare queue wait, makespan, completed/failed jobs, and time-weighted GPU utilization.
4. Repeat each run at least five times with identical seeds; report mean and variability.
5. Inject worker failures at a fixed schedule and define how retries count toward logical job completion.
6. Save raw CSV/JSON results, Python version, parameters, and commit SHA.

Definitions:
- Queue wait = start time minus submission time; report mean and median.
- GPU utilization = GPU-seconds used divided by available GPU-seconds over the measurement interval.
- Completion rate = logical jobs completed divided by logical jobs submitted.
- Queue-wait reduction = (baseline wait - new wait) / baseline wait.

A single snapshot of worker usage is not enough to substantiate utilization claims. The simulator's current execution model is simplified, so explain the model and its limits in any report.
