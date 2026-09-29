# Changelog

All notable changes to BHAIRAVA-BB are documented here.

## V6

### Added

- Asset Intelligence with normalization and deduplication.
- Technology fingerprinting and asset relationships.
- Persistent asset repository.
- Finding correlation and deduplication.
- Finding confidence handling.
- Structured evidence models.
- Evidence sanitization and integrity hashing.
- Resumable job checkpoints and resume support.
- Pipeline stage modeling.
- Database migration infrastructure.
- Deterministic planning and dry-run support.
- Reporting templates and exporters.
- V6 regression coverage.

### Compatibility

- Preserved legacy finding lifecycle interfaces.
- Preserved legacy evidence collector interfaces.
- Preserved existing sanitizer compatibility.
- Preserved the established scope and authorization architecture.

### Verification

- Full automated regression suite: 152 tests passed.

The format follows Keep a Changelog and Semantic Versioning.

## [1.0.0] - 2026-09-27

First documented framework release.

### Added

- Scope Guard authorization boundary.
- Secure external-tool execution architecture.
- Tool adapter and registry architecture.
- Reconnaissance engine.
- Discovery engine.
- Detection engine.
- Controlled validation engine.
- Findings lifecycle and deduplication.
- Evidence collection, sanitization, and hashing.
- Markdown, JSON, and HTML reporting.
- SQLite persistence.
- Persistent job management.
- Optional AI enhancement layer.
- GitHub issue and pull-request templates.
- Architecture documentation.
- Scope-management documentation.
- Troubleshooting documentation.

### Security

- Active operations are subject to authorization and scope controls.
- External tool execution is centralized through the executor architecture.
- Shell-based arbitrary command execution is not part of the intended
  execution model.
- Evidence handling includes secret-sanitization mechanisms.
- AI is disabled by default.
- AI is not an authorization authority.
- AI must not expand scope or bypass security controls.

### Testing

Verified project test result:

```text
124 passed
```
The test count may change as the project evolves.

### Pipeline

The documented pipeline contains seven stages:

```text
scope
recon
discovery
detection
validation
evidence
report
```
### Documentation

- `README.md`
- `docs/architecture.md`
- `docs/scope-management.md`
- `docs/troubleshooting.md`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`

### Legal and authorization

BHAIRAVA-BB does not grant authorization to test third-party systems.

Operators are responsible for obtaining authorization, respecting program
rules and exclusions, respecting rate limits and technique restrictions,
obtaining required notice or consent, and complying with applicable law.
