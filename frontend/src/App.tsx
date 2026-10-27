import { useCallback, useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
type Job = {
  id: string; name: string; resource: string; cpu_cores: number; gpu_count: number;
  estimated_seconds: number; priority: number; status: string; worker_id?: string | null;
};
type Summary = {
  job_counts: Record<string, number>; worker_count: number; online_workers: number;
  cpu_utilization: number; gpu_utilization: number;
};
const policies = [
  { value: "fifo", label: "First in, first out" },
  { value: "priority", label: "Priority" },
  { value: "sjf", label: "Shortest job first" },
  { value: "backfill", label: "Backfill heuristic" },
];
export default function App() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [policy, setPolicy] = useState("fifo");
  const [name, setName] = useState("image-batch");
  const [resource, setResource] = useState("gpu");
  const [cpu, setCpu] = useState(2);
  const [gpu, setGpu] = useState(1);
  const [duration, setDuration] = useState(60);
  const [priority, setPriority] = useState(5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async () => {
    try {
      const [jobResponse, summaryResponse] = await Promise.all([
        fetch(`${API}/jobs`), fetch(`${API}/summary`)
      ]);
      if (!jobResponse.ok || !summaryResponse.ok) throw new Error("API request failed");
      setJobs(await jobResponse.json());
      setSummary(await summaryResponse.json());
      setError("");
    } catch {
      setError("Cannot reach the API. Start it with: cd backend && uvicorn app.main:app --reload");
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  async function submitJob(event: React.FormEvent) {
    event.preventDefault(); setError(""); setNotice("");
    try {
      const response = await fetch(`${API}/jobs`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, resource, cpu_cores: cpu, gpu_count: resource === "cpu" ? 0 : gpu,
          estimated_seconds: duration, priority })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Could not submit job");
      setNotice(`Submitted ${data.name} to the queue.`);
      await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not submit job"); }
  }

  async function scheduleJobs() {
    setBusy(true); setError(""); setNotice("");
    try {
      const response = await fetch(`${API}/schedule/${policy}`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Scheduling failed");
      setNotice(`${data.count} job(s) dispatched using ${policy.toUpperCase()}.`);
      await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Scheduling failed"); }
    finally { setBusy(false); }
  }

  async function finishJob(job: Job, failed = false) {
    setError(""); setNotice("");
    try {
      const response = await fetch(`${API}/jobs/${job.id}/finish?failed=${failed}`, { method: "POST" });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Could not finish job");
      setNotice(`${job.name} marked ${failed ? "failed" : "completed"}.`);
      await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not finish job"); }
  }

  return <main>
    <header className="hero">
      <div><p className="eyebrow">SYSTEMS ENGINEERING / SIMULATION</p><h1>Distributed Compute Scheduler</h1>
        <p className="subtitle">Explore how scheduling policies dispatch CPU and GPU workloads across a simulated worker fleet.</p></div>
      <div className="fleet"><span className="pulse" />{summary?.online_workers ?? 20} workers online</div>
    </header>
    {error && <div className="alert" role="alert">{error}</div>}
    {notice && <div className="notice" role="status">{notice}</div>}
    <section className="metrics">
      <Metric label="Queued" value={summary?.job_counts.queued ?? 0} />
      <Metric label="Running" value={summary?.job_counts.running ?? 0} />
      <Metric label="Completed" value={summary?.job_counts.completed ?? 0} />
      <Metric label="Failed" value={summary?.job_counts.failed ?? 0} />
      <Metric label="CPU utilization" value={summary ? `${(summary.cpu_utilization * 100).toFixed(0)}%` : "—"} />
      <Metric label="GPU utilization" value={summary ? `${(summary.gpu_utilization * 100).toFixed(0)}%` : "—"} />
    </section>
    <div className="columns">
      <section className="panel"><div className="panel-heading"><span className="number">01</span><div><h2>Submit a job</h2><p>Create a workload for the queue.</p></div></div>
        <form onSubmit={submitJob} className="job-form">
          <label>Job name<input value={name} onChange={e => setName(e.target.value)} required maxLength={120} /></label>
          <label>Resource type<select value={resource} onChange={e => {setResource(e.target.value); if (e.target.value === "cpu") setGpu(0); else if (gpu === 0) setGpu(1);}}><option value="cpu">CPU</option><option value="gpu">GPU</option><option value="mixed">Mixed CPU + GPU</option></select></label>
          <div className="field-row"><label>CPU cores<input type="number" min="1" value={cpu} onChange={e => setCpu(Number(e.target.value))} /></label>
            <label>GPU count<input type="number" min="0" value={resource === "cpu" ? 0 : gpu} disabled={resource === "cpu"} onChange={e => setGpu(Number(e.target.value))} /></label></div>
          <div className="field-row"><label>Duration (seconds)<input type="number" min="1" value={duration} onChange={e => setDuration(Number(e.target.value))} /></label>
            <label>Priority (0–10)<input type="number" min="0" max="10" value={priority} onChange={e => setPriority(Number(e.target.value))} /></label></div>
          <button className="primary" type="submit">+ Add to queue</button>
        </form>
      </section>
      <section className="panel"><div className="panel-heading"><span className="number">02</span><div><h2>Run scheduler</h2><p>Choose a policy and dispatch jobs that fit available resources.</p></div></div>
        <label>Scheduling policy<select value={policy} onChange={e => setPolicy(e.target.value)}>{policies.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}</select></label>
        <div className="policy-note"><strong>{policy.toUpperCase()}</strong><span>{policy === "fifo" ? "Dispatches jobs in submission order." : policy === "priority" ? "Dispatches higher-priority jobs first." : policy === "sjf" ? "Prefers jobs with shorter estimated runtimes." : "Uses a short-job-first capacity-filling heuristic."}</span></div>
        <button className="primary" onClick={scheduleJobs} disabled={busy}>{busy ? "Scheduling…" : "▶ Dispatch queued jobs"}</button>
        <button className="secondary" onClick={() => void refresh()}>Refresh dashboard</button>
      </section>
    </div>
    <section className="panel queue-panel"><div className="queue-heading"><div><p className="eyebrow">LIVE SIMULATOR STATE</p><h2>Job queue <span className="count">{jobs.length}</span></h2></div><span className="muted">Simulation only · no real cluster workloads</span></div>
      {jobs.length === 0 ? <div className="empty"><strong>No jobs yet</strong><span>Submit a workload above to get started.</span></div> :
      <div className="table-wrap"><table><thead><tr><th>Job</th><th>Resource</th><th>CPU / GPU</th><th>Priority</th><th>Worker</th><th>Status</th><th>Action</th></tr></thead>
        <tbody>{[...jobs].reverse().map(job => <tr key={job.id}><td><strong>{job.name}</strong><small>{job.id.slice(0, 8)}</small></td><td>{job.resource.toUpperCase()}</td><td>{job.cpu_cores} CPU / {job.gpu_count} GPU</td><td>{job.priority}/10</td><td>{job.worker_id ?? "—"}</td><td><span className={`status ${job.status}`}>{job.status}</span></td><td>{job.status === "running" ? <div className="actions"><button className="tiny" onClick={() => void finishJob(job)}>Finish</button><button className="tiny danger" onClick={() => void finishJob(job, true)}>Fail</button></div> : "—"}</td></tr>)}</tbody></table></div>}
    </section>
    <footer><span>Distributed Compute Scheduler</span><span>Built to explore scheduling trade-offs, not to claim production performance.</span></footer>
  </main>;
}
function Metric({label, value}: {label:string; value:string|number}) {
  return <article className="metric"><span>{label}</span><strong>{typeof value === "number" ? value.toLocaleString() : value}</strong></article>;
}