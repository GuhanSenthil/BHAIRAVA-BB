"""bhairava.pipeline.engine -- orchestrate scope -> recon -> discovery -> detection -> evidence -> report."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..core.executor import ToolExecutor
from ..core.rate_limiter import RateLimiter
from ..detection.engine import DetectionEngine
from ..discovery.engine import DiscoveryEngine
from ..findings.correlation import correlate, merge_group
from ..findings.dedup import dedupe
from ..findings.models import Finding
from ..jobs.manager import JobManager
from ..jobs.models import PIPELINE_STAGES, Job
from ..recon.engine import ReconEngine
from ..reporting.engine import write_report
from ..scope_guard import ScopeGuard
from ..tools.registry import default_registry


@dataclass
class PipelineConfig:
    scope_yaml: Path
    data_dir: Path = Path("data")
    reports_dir: Path = Path("reports")
    timeout: int = 300
    dry_run: bool = False
    resume_job_id: str = ""
    stages: tuple[str, ...] = PIPELINE_STAGES


@dataclass
class PipelineResult:
    job: Job
    recon_hosts: int = 0
    endpoints: int = 0
    raw_findings: int = 0
    final_findings: int = 0
    reports: dict[str, Path] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


def _banner(msg: str) -> None:
    print(f"\n=== {msg} ===")


class Pipeline:
    def __init__(self, config: PipelineConfig):
        self.cfg = config
        self.guard = ScopeGuard.from_yaml(config.scope_yaml)
        rl = RateLimiter(self.guard.scope.requests_per_second)
        self.executor = ToolExecutor(self.guard, rate_limiter=rl)
        self.registry = default_registry()
        self.db = None
        self.jobs = None
        if not config.dry_run:
            from ..storage.database import Database
            db_path = Path(config.data_dir) / "bhairava.db"
            self.db = Database(db_path)
            self.jobs = JobManager(self.db)

    def _ensure_job(self) -> Job:
        if self.cfg.resume_job_id:
            job = self.jobs.get(self.cfg.resume_job_id)
            if job is None:
                raise ValueError(f"job not found: {self.cfg.resume_job_id}")
            return job
        return self.jobs.create(
            target=self.guard.scope.name,
            scope_yaml=str(self.cfg.scope_yaml),
        )

    def _dry_run_summary(self) -> PipelineResult:
        _banner("DRY RUN")
        print(f"Program:  {self.guard.scope.name}")
        print(f"Domains:  {', '.join(self.guard.scope.domains) or '(none)'}")
        print(f"URLs:     {', '.join(self.guard.scope.urls) or '(none)'}")
        print(f"Excluded: {', '.join(self.guard.scope.excluded) or '(none)'}")
        print("\nPlanned stages:")
        for s in self.cfg.stages:
            print(f"  [ ] {s}")
        print("\nNo network testing performed.")
        return PipelineResult(job=Job(target=self.guard.scope.name))

    def run(self) -> PipelineResult:
        if self.cfg.dry_run:
            return self._dry_run_summary()

        job = self._ensure_job()
        job.start()
        self.jobs.save(job)

        try:
            return self._run_stages(job)
        except Exception as e:
            job.fail(str(e))
            self.jobs.save(job)
            raise

    def _run_stages(self, job: Job) -> PipelineResult:
        result = PipelineResult(job=job)
        target = self._pick_target()

        # 1. SCOPE
        if not job.has_run("scope"):
            _banner("SCOPE")
            print(f"Program: {self.guard.scope.name}")
            print(f"Domains: {', '.join(self.guard.scope.domains)}")
            job.mark_stage("scope")
            self.jobs.save(job)

        # 2. RECON
        if "recon" in self.cfg.stages and not job.has_run("recon"):
            _banner("RECON")
            if target:
                rr = ReconEngine(self.executor, self.registry, self.guard).run(
                    target, timeout=self.cfg.timeout
                )
                result.recon_hosts = len(rr.hosts)
                result.errors.extend(rr.errors)
                print(f"hosts: {len(rr.hosts)}")
                for src, n in rr.sources.items():
                    print(f"  {src}: {n}")
                job.stats["recon_hosts"] = len(rr.hosts)
            else:
                print("no scoped target")
            job.mark_stage("recon")
            self.jobs.save(job)

        # 3. DISCOVERY
        if "discovery" in self.cfg.stages and not job.has_run("discovery"):
            _banner("DISCOVERY")
            if target:
                dr = DiscoveryEngine(self.executor, self.registry, self.guard).run(
                    target, timeout=self.cfg.timeout
                )
                result.endpoints = len(dr.endpoints)
                result.errors.extend(dr.errors)
                print(f"endpoints: {len(dr.endpoints)}")
                for src, n in dr.sources.items():
                    print(f"  {src}: {n}")
                job.stats["endpoints"] = len(dr.endpoints)
            job.mark_stage("discovery")
            self.jobs.save(job)

        # 4. DETECTION
        all_findings: list[Finding] = []
        if "detection" in self.cfg.stages and not job.has_run("detection"):
            _banner("DETECTION")
            det_target = (
                self.guard.scope.urls[0] if self.guard.scope.urls
                else (f"https://{self.guard.scope.domains[0].lstrip('*.')}"
                      if self.guard.scope.domains else "")
            )
            if det_target:
                det = DetectionEngine(self.executor, self.registry, self.guard).run(
                    det_target, timeout=self.cfg.timeout, job_id=job.id
                )
                all_findings = det.findings
                result.raw_findings = len(det.findings)
                result.errors.extend(det.errors)
                print(f"raw findings: {len(det.findings)}")
            job.mark_stage("detection")
            self.jobs.save(job)

        # 5. CORRELATION + persist
        groups = correlate(all_findings)
        merged = [merge_group(g) for g in groups]
        final_findings = dedupe(merged)
        result.final_findings = len(final_findings)

        for f in final_findings:
            self.db.execute(
                "INSERT OR REPLACE INTO findings (id, job_id, data, created_at) VALUES (?,?,?,?)",
                (f.id, job.id, json.dumps(f.to_dict()), f.timestamp),
            )

        # 6. VALIDATION (opt-in only)
        if "validation" in self.cfg.stages and not job.has_run("validation"):
            _banner("VALIDATION")
            print("validation stage is opt-in; skipping")
            job.mark_stage("validation")
            self.jobs.save(job)

        # 7. EVIDENCE
        if "evidence" in self.cfg.stages and not job.has_run("evidence"):
            _banner("EVIDENCE")
            print(f"evidence attached to {len(final_findings)} finding(s)")
            job.mark_stage("evidence")
            self.jobs.save(job)

        # 8. REPORT
        if "report" in self.cfg.stages and not job.has_run("report"):
            _banner("REPORT")
            out_dir = Path(self.cfg.reports_dir) / job.id
            written = write_report(
                final_findings, out_dir,
                target=self.guard.scope.name,
                program=self.guard.scope.name,
            )
            result.reports = written
            for fmt, p in written.items():
                print(f"  {fmt}: {p}")
            job.mark_stage("report")
            self.jobs.save(job)

        job.stats["final_findings"] = len(final_findings)
        job.finish()
        self.jobs.save(job)
        return result

    def _pick_target(self) -> str:
        if self.guard.scope.domains:
            return self.guard.scope.domains[0].lstrip("*.")
        if self.guard.scope.urls:
            return self.guard.scope.urls[0]
        return ""

    def close(self) -> None:
        if self.db is not None:
            self.db.close()
