# BHAIRAVA-BB
[![Tests](https://github.com/GuhanSenthil/BHAIRAVA-BB/actions/workflows/tests.yml/badge.svg)](https://github.com/GuhanSenthil/BHAIRAVA-BB/actions/workflows/tests.yml)
[![Lint](https://github.com/GuhanSenthil/BHAIRAVA-BB/actions/workflows/lint.yml/badge.svg)](https://github.com/GuhanSenthil/BHAIRAVA-BB/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
\n
Authorized Bug Bounty Security Research Framework.

Use only against targets you have explicit written authorization to test.

## Install (Kali / Debian)

    git clone https://github.com/GuhanSenthil/BHAIRAVA-BB
    cd BHAIRAVA-BB
    chmod +x install.sh
    sudo ./install.sh
    bhairava --version

## Usage

    bhairava --help
    bhairava scope validate <target>
    bhairava scope show
    bhairava tools
    bhairava status
    bhairava pipeline --dry-run

## Scope

Every active operation passes through the Scope Guard. Out-of-scope
targets are blocked before any network testing begins.

## Exit codes

    0  success
    1  general error
    2  invalid configuration
    3  scope violation
    4  missing dependency
    5  validation failure

## License

MIT. See LICENSE.

## Safety guarantees

BHAIRAVA-BB enforces the following guarantees across the whole pipeline.
Each guarantee is covered by automated tests.

### Phase F -- pipeline, jobs, and storage

- **Every pipeline stage routes through ScopeGuard.** The pipeline inherits
  the same executor that rate-limits and scope-checks each tool invocation.
  An out-of-scope target is rejected before any tool runs.
- **`--dry-run` writes nothing.** No database file, no report directory,
  no network traffic. Running `bhairava pipeline --dry-run` against a real
  scope produces only a printed summary.
- **Job persistence contains no secrets.** Findings are stored as sanitized
  JSON records. API keys, cookies, bearer tokens, and passwords never enter
  the SQLite database.
- **`--resume` skips completed stages.** A resumed job re-runs only the
  stages not yet marked complete. No duplicate scans, no duplicate findings.
- **Job IDs are unique and time-ordered.** Format:
  `JOB-YYYYMMDD-HHMMSS-<hex>`. `jobs list` returns the newest first.
- **Cancellation is terminal.** A cancelled job cannot be resumed
  accidentally; `jobs cancel` writes the terminal state once.
- **Deletion removes all related rows atomically.** `jobs delete` removes
  the job row, its findings, its evidence, and its tool-run history in a
  single transaction, in that order, to respect foreign-key relationships.

### Inherited guarantees (from earlier phases)

- **Executor:** every subprocess call uses argument arrays with no
  `shell=True`, enforces a timeout, caps stdout/stderr size, and passes a
  minimal environment allowlist.
- **Adapter registry:** unknown tools are skipped, not fatal. A missing
  adapter never crashes the CLI.
- **Detection:** every Nuclei match is re-validated against ScopeGuard
  before being stored as a finding.
- **Validation:** sqlmap runs only with `--batch --smart --level=1 --risk=1`.
  Flags like `--os-shell`, `--file-read`, `--dump`, `--sql-shell` are
  blocked at command-construction time.
- **Evidence:** sanitizer strips bearer tokens, OpenAI/Anthropic/GitHub/
  Groq/Gemini keys, cookies, `Authorization`, and private keys before
  any record is written.
- **AI layer:** disabled by default. When enabled, all target content is
  wrapped in an untrusted-data block and explicitly labelled as data.
  AI cannot expand scope, disable rate limits, or execute commands -- every
  proposed step is re-validated through the policy engine and ScopeGuard.
- **Reporting:** reports never contain secrets. Sanitization happens at
  collection time, not at render time.

### Automated test coverage

    pytest -q
    # 124 passed

The suite includes explicit negative tests for:

- out-of-scope targets blocked at every entry point
- ScopeGuard wildcard and exclusion behaviour
- sqlmap forbidden-flag rejection
- AI policy engine rejecting shell metacharacters and unknown tools
- job state machine rejecting illegal transitions
- pipeline dry-run creating no files
\n## Documentation

- [Architecture](docs/architecture.md) - system architecture and data flow
- [Scope Management](docs/scope-management.md) - authorization and scope configuration
- [Troubleshooting](docs/troubleshooting.md) - common installation and runtime issues
- [Security Policy](SECURITY.md) - security vulnerability reporting
- [Contributing](CONTRIBUTING.md) - contribution workflow




---

# BHAIRAVA-BB V6

BHAIRAVA-BB V6 extends the framework with an asset-centric security research architecture.

## V6 Pipeline

```text
Scope
  ->
Recon
  ->
Asset Intelligence
  ->
Discovery
  ->
Detection
  ->
Finding Correlation
  ->
Evidence
  ->
Human Review
  ->
Report
```


V6 Architecture
Asset Intelligence
- Asset normalization
- Asset deduplication
- Technology fingerprinting
- Asset relationship graph
- Persistent asset repository
Finding Intelligence
- Finding correlation
- Confidence handling
- Finding deduplication
- Lifecycle management
Evidence
- Structured evidence
- Sanitization
- Integrity hashing
- Reproduction metadata
Resumable Jobs
- Checkpoints
- Resume support
- Pipeline stages
Planning
- Deterministic execution planning
- Dry-run support
Database
- Versioned migrations
- SQLite persistence
- Controlled schema evolution
Reporting
- Report templates
- Report exporters
AI Safety
AI is optional and disabled by default.
The controlled architecture is:
AI
 ->
Policy Engine
 ->
Scope Guard
 ->
Secure Executor
 ->
Evidence
 ->
Human Review

AI cannot independently expand scope, remove exclusions, disable safety limits, execute arbitrary shell commands, approve destructive operations, or confirm findings without the deterministic workflow.
Verification
The V6 implementation has passed the full automated regression suite:
152 passed

See the complete [V6 Architecture](docs/architecture/BHAIRAVA-BB-V6-ARCHITECTURE.md).
