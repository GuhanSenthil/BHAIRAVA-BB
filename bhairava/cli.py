"""bhairava.cli -- Command-line entry point."""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from . import __version__
from .banner import print_banner, info, success, warn, error, blocked
from .exceptions import BhairavaError, ConfigError, ScopeViolation
from .scope_guard import ScopeGuard


def _cmd_scope_validate(args) -> int:
    guard = ScopeGuard.from_yaml(args.scope)
    success(f"scope loaded: {guard.scope.name}")
    info(f"domains : {', '.join(guard.scope.domains) or '(none)'}")
    info(f"urls    : {', '.join(guard.scope.urls) or '(none)'}")
    info(f"excluded: {', '.join(guard.scope.excluded) or '(none)'}")
    if args.target:
        try:
            guard.validate_target(args.target)
            success(f"ALLOWED: {args.target}")
            return 0
        except ScopeViolation as e:
            blocked(str(e))
            return 3
    return 0


def _cmd_scope_show(args) -> int:
    guard = ScopeGuard.from_yaml(args.scope)
    for k, v in guard.summary().items():
        info(f"{k}: {v}")
    return 0


def _cmd_status(_args) -> int:
    print_banner(__version__, show_help_hint=False)
    info("status: ready")
    info(f"python: {sys.version.split()[0]}")
    info(f"cwd   : {Path.cwd()}")
    return 0


def _cmd_tools(args) -> int:
    """Check installed external tools via the adapter registry."""
    from .tools.registry import default_registry, render_registry_status
    reg = default_registry()
    print(render_registry_status(reg))
    return 0 if reg.available() else 4


def _cmd_config_validate(args) -> int:
    path = Path(args.scope)
    if not path.exists():
        error(f"scope file not found: {path}")
        return 2
    try:
        ScopeGuard.from_yaml(path)
    except ConfigError as e:
        error(str(e))
        return 2
    success(f"scope file valid: {path}")
    return 0


def _cmd_pipeline(args) -> int:
    guard = ScopeGuard.from_yaml(args.scope)
    if args.dry_run:
        print_banner(__version__, show_help_hint=False)
        info("DRY RUN -- no network testing will be performed")
        info(f"program: {guard.scope.name}")
        info(f"domains: {guard.scope.domains}")
        info(f"urls   : {guard.scope.urls}")
        info("planned modules: recon, discover, scan, evidence, report")
        return 0
    warn("non-dry-run pipeline not implemented yet (Phase 2)")
    return 0


def _cmd_recon(args) -> int:
    from .core.executor import ToolExecutor
    from .core.rate_limiter import RateLimiter
    from .recon.engine import ReconEngine
    from .scope_guard import ScopeGuard
    from .storage.json_store import JsonStore
    from .tools.registry import default_registry

    guard = ScopeGuard.from_yaml(args.scope)
    rl = RateLimiter(guard.scope.requests_per_second)
    executor = ToolExecutor(guard, rate_limiter=rl)
    engine = ReconEngine(executor, default_registry(), guard)

    info(f"recon on {args.target}")
    result = engine.run(args.target, timeout=args.timeout)
    success(f"hosts: {len(result.hosts)}")
    for src, n in result.sources.items():
        info(f"  {src}: {n}")
    for skip in result.skipped:
        warn(f"  skipped {skip}")
    for err in result.errors:
        warn(f"  error: {err}")

    store = JsonStore(args.data_dir)
    path = store.save("recon", {"target": args.target,
                                "hosts": result.hosts,
                                "sources": result.sources,
                                "errors": result.errors}, subdir="recon")
    success(f"saved: {path}")
    return 0


def _cmd_discover(args) -> int:
    from .core.executor import ToolExecutor
    from .core.rate_limiter import RateLimiter
    from .discovery.engine import DiscoveryEngine
    from .scope_guard import ScopeGuard
    from .storage.json_store import JsonStore
    from .tools.registry import default_registry

    guard = ScopeGuard.from_yaml(args.scope)
    rl = RateLimiter(guard.scope.requests_per_second)
    executor = ToolExecutor(guard, rate_limiter=rl)
    engine = DiscoveryEngine(executor, default_registry(), guard)

    info(f"discovery on {args.target}")
    result = engine.run(args.target, timeout=args.timeout,
                        include_active=args.active)
    success(f"endpoints: {len(result.endpoints)}")
    for src, n in result.sources.items():
        info(f"  {src}: {n}")
    for skip in result.skipped:
        warn(f"  skipped {skip}")
    for err in result.errors:
        warn(f"  error: {err}")

    store = JsonStore(args.data_dir)
    path = store.save("discover", {"target": args.target,
                                   "endpoints": result.endpoints,
                                   "sources": result.sources,
                                   "errors": result.errors}, subdir="discovery")
    success(f"saved: {path}")
    return 0


def _cmd_scan(args) -> int:
    from .core.executor import ToolExecutor
    from .core.rate_limiter import RateLimiter
    from .detection.engine import DetectionEngine
    from .findings.correlation import correlate, merge_group
    from .findings.dedup import dedupe
    from .findings.store import FindingStore
    from .scope_guard import ScopeGuard
    from .tools.registry import default_registry

    guard = ScopeGuard.from_yaml(args.scope)
    rl = RateLimiter(guard.scope.requests_per_second)
    executor = ToolExecutor(guard, rate_limiter=rl)
    engine = DetectionEngine(executor, default_registry(), guard)

    sev = tuple(s.strip().lower() for s in args.severity.split(",")) if args.severity else None

    info(f"scanning {args.target}")
    result = engine.run(
        target=args.target,
        severities=sev or ("info", "low", "medium", "high", "critical"),
        timeout=args.timeout,
    )
    success(f"raw detections: {result.raw_count}")
    info(f"scoped findings: {len(result.findings)}")
    for skip in result.skipped:
        warn(f"  skipped {skip}")
    for err in result.errors:
        warn(f"  error: {err}")

    # Correlate -> merge -> dedupe
    groups = correlate(result.findings)
    merged = [merge_group(g) for g in groups]
    final = dedupe(merged)

    success(f"correlated findings: {len(final)}")

    store = FindingStore(Path(args.data_dir) / "findings" / "latest.json")
    store.add_many(final)
    saved = store.save()
    if saved:
        success(f"saved: {saved}")

    # Print summary
    if final:
        print()
        info("FINDINGS")
        for f in sorted(final, key=lambda x: x.severity, reverse=True):
            print(f"  [{f.severity.upper():<8}] {f.title}  <{f.status}>  {f.url}")
    return 0


def _cmd_validate(args) -> int:
    from .core.executor import ToolExecutor
    from .core.rate_limiter import RateLimiter
    from .findings.store import FindingStore
    from .scope_guard import ScopeGuard
    from .tools.registry import default_registry
    from .validation.engine import ValidationEngine

    store = FindingStore(args.input)
    store.load()
    findings = store.all()
    if not findings:
        warn(f"no findings in {args.input}")
        return 1

    guard = ScopeGuard.from_yaml(args.scope)
    rl = RateLimiter(guard.scope.requests_per_second)
    executor = ToolExecutor(guard, rate_limiter=rl)
    engine = ValidationEngine(executor, default_registry(), guard,
                              auto_approve=args.yes)

    info(f"validating {len(findings)} finding(s)")
    results = engine.validate_many(findings, timeout=args.timeout)
    confirmed = sum(1 for r in results if r.validated)
    rejected = sum(1 for r in results if r.rejected)
    errors = sum(1 for r in results if r.error)
    success(f"confirmed: {confirmed}  rejected: {rejected}  errors: {errors}")

    store.save()
    success(f"updated: {args.input}")
    return 0


def _cmd_report(args) -> int:
    from pathlib import Path as _P
    from .findings.store import FindingStore
    from .reporting.engine import write_report

    store = FindingStore(args.input)
    store.load()
    findings = store.all()
    if not findings:
        warn(f"no findings in {args.input}")
        return 1

    formats = tuple(f.strip() for f in args.format.split(","))
    written = write_report(findings, args.output, target=args.target,
                           program=args.program, formats=formats)
    success(f"report on {len(findings)} finding(s):")
    for fmt, path in written.items():
        info(f"  {fmt}: {path}")
    return 0


def _load_ai_cfg(args):
    """Load AI section of config.yaml."""
    from pathlib import Path as _P
    import yaml
    cfg_path = _P(args.config)
    if not cfg_path.exists():
        return {}
    data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return data.get("ai", {}) or {}


def _cmd_agent_plan(args) -> int:
    from .agent.planner import Planner
    from .scope_guard import ScopeGuard

    guard = ScopeGuard.from_yaml(args.scope)
    ai_cfg = _load_ai_cfg(args)
    if args.provider:
        ai_cfg["provider"] = args.provider
    if args.model:
        ai_cfg["model"] = args.model

    planner = Planner(ai_cfg, guard)
    if not planner.available():
        warn("AI provider not available; enable in config.yaml or pass --provider")
        return 4

    info(f"planning with {ai_cfg.get('provider')}/{ai_cfg.get('model')}")
    result = planner.plan()
    if result.error:
        warn(f"planner error: {result.error}")
    if result.rejected:
        for r in result.rejected:
            warn(f"  rejected: {r}")
    if result.steps:
        success(f"accepted {len(result.steps)} step(s):")
        for s in result.steps:
            print(f"  [{s['module']:<9}] {s['tool']:<12} {s['target']:<40} {s['reason']}")
    else:
        info("no actionable steps proposed")
    return 0


def _cmd_agent_analyze(args) -> int:
    from .agent.analyzer import Analyzer
    from .findings.store import FindingStore

    store = FindingStore(args.input)
    store.load()
    findings = store.all()
    if not findings:
        warn(f"no findings in {args.input}")
        return 1

    ai_cfg = _load_ai_cfg(args)
    if args.provider:
        ai_cfg["provider"] = args.provider
    if args.model:
        ai_cfg["model"] = args.model

    analyzer = Analyzer(ai_cfg)
    if not analyzer.available():
        warn("AI provider not available; enable in config.yaml or pass --provider")
        return 4

    info(f"analyzing {len(findings)} finding(s)")
    results = analyzer.analyze_many(findings)
    for r in results:
        if r.analysis:
            print(f"\n[{r.finding_id}]")
            print(f"  severity: {r.analysis['severity_assessment']}")
            print(f"  confidence: {r.analysis['confidence_adjust']:.2f}")
            print(f"  summary: {r.analysis['summary']}")
            for s in r.analysis['verification_steps']:
                print(f"    - {s}")
        elif r.error:
            warn(f"[{r.finding_id}] {r.error}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bhairava",
        description="BHAIRAVA-BB -- Authorized Bug Bounty Security Research Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--version", action="version",
                   version=f"BHAIRAVA-BB v{__version__}\nAuthorized Security Research Framework")
    p.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    p.add_argument("--scope", default="config/scope.yaml", help="Path to scope YAML (default: config/scope.yaml)")

    sub = p.add_subparsers(dest="command")

    sp_scope = sub.add_parser("scope", help="Manage authorized target scope")
    sp_scope_sub = sp_scope.add_subparsers(dest="scope_cmd")

    sv = sp_scope_sub.add_parser("validate", help="Validate a target against scope")
    sv.add_argument("target", nargs="?")
    sv.set_defaults(func=_cmd_scope_validate)

    ss = sp_scope_sub.add_parser("show", help="Show current scope")
    ss.set_defaults(func=_cmd_scope_show)

    sub.add_parser("status", help="Show framework status").set_defaults(func=_cmd_status)
    sub.add_parser("tools", help="Check installed external tools").set_defaults(func=_cmd_tools)

    sp_cfg = sub.add_parser("config", help="Manage configuration")
    sp_cfg_sub = sp_cfg.add_subparsers(dest="cfg_cmd")
    cv = sp_cfg_sub.add_parser("validate", help="Validate scope YAML")
    cv.set_defaults(func=_cmd_config_validate)

    sp_val = sub.add_parser("validate", help="Validate candidate findings")
    sp_val.add_argument("--input", required=True,
                        help="Path to findings JSON (from scan)")
    sp_val.add_argument("--timeout", type=int, default=300)
    sp_val.add_argument("--yes", action="store_true",
                        help="Auto-approve impactful validators (sqlmap)")
    sp_val.set_defaults(func=_cmd_validate)

    sp_rep = sub.add_parser("report", help="Generate reports from findings")
    sp_rep.add_argument("--input", required=True,
                        help="Path to findings JSON")
    sp_rep.add_argument("--output", default="reports",
                        help="Output directory")
    sp_rep.add_argument("--format", default="markdown,json,html",
                        help="Comma-separated: markdown,json,html")
    sp_rep.add_argument("--target", default="")
    sp_rep.add_argument("--program", default="")
    sp_rep.set_defaults(func=_cmd_report)

    sp_scan = sub.add_parser("scan", help="Vulnerability detection via Nuclei")
    sp_scan.add_argument("--target", required=True)
    sp_scan.add_argument("--severity", default="",
                         help="Comma-separated severities (default: all)")
    sp_scan.add_argument("--timeout", type=int, default=600)
    sp_scan.add_argument("--data-dir", default="data")
    sp_scan.set_defaults(func=_cmd_scan)

    sp_agent = sub.add_parser("agent", help="AI-assisted planning and analysis")
    agent_sub = sp_agent.add_subparsers(dest="agent_cmd")

    ap = agent_sub.add_parser("plan", help="AI-suggested next steps (policy-checked)")
    ap.add_argument("--provider", default="")
    ap.add_argument("--model", default="")
    ap.add_argument("--config", default="config/config.yaml")
    ap.set_defaults(func=_cmd_agent_plan)

    aa = agent_sub.add_parser("analyze", help="AI analysis of findings")
    aa.add_argument("--input", required=True, help="Path to findings JSON")
    aa.add_argument("--provider", default="")
    aa.add_argument("--model", default="")
    aa.add_argument("--config", default="config/config.yaml")
    aa.set_defaults(func=_cmd_agent_analyze)

    sp_recon = sub.add_parser("recon", help="Subdomain and asset reconnaissance")
    sp_recon.add_argument("--target", required=True)
    sp_recon.add_argument("--timeout", type=int, default=120)
    sp_recon.add_argument("--data-dir", default="data")
    sp_recon.set_defaults(func=_cmd_recon)

    sp_disc = sub.add_parser("discover", help="URL and endpoint discovery")
    sp_disc.add_argument("--target", required=True)
    sp_disc.add_argument("--timeout", type=int, default=120)
    sp_disc.add_argument("--active", action="store_true",
                         help="Include ffuf/linkfinder (fuzzing)")
    sp_disc.add_argument("--data-dir", default="data")
    sp_disc.set_defaults(func=_cmd_discover)

    sp_pipe = sub.add_parser("pipeline", help="Run authorized workflow")
    sp_pipe.add_argument("--dry-run", action="store_true")
    sp_pipe.set_defaults(func=_cmd_pipeline)

    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        print_banner(__version__)
        return 0

    fn = getattr(args, "func", None)
    if fn is None:
        parser.print_help()
        return 1

    try:
        return fn(args) or 0
    except ScopeViolation as e:
        blocked(str(e))
        return 3
    except ConfigError as e:
        error(str(e))
        return 2
    except BhairavaError as e:
        error(str(e))
        return e.exit_code
    except KeyboardInterrupt:
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
