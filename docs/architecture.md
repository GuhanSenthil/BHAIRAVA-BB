# BHAIRAVA-BB Architecture

## Overview

BHAIRAVA-BB is an authorized security research framework designed to
organize reconnaissance, discovery, detection, controlled validation,
evidence collection, findings management, and reporting.

The framework is designed around a mandatory Scope Guard and a secure
execution boundary.

> **Authorization requirement:** BHAIRAVA-BB does not grant permission to
> test any system. Operators are responsible for obtaining the required
> authorization before testing.

## Data flow

```text
                         BHAIRAVA-BB
                              |
                         CLI / API
                              |
                         Scope Guard
                         /         \
                    BLOCKED       ALLOWED
                       |              |
                    Exit 3       Pipeline Engine
                                      |
             +------------+------------+------------+
             |            |            |            |
           RECON      DISCOVERY    DETECTION    VALIDATION
             |            |            |            |
             +------------+------------+------------+
                                      |
                              Findings Engine
                              correlate + dedup
                                      |
                              Evidence Engine
                              sanitize + hash
                                      |
                             Reporting Engine
                              md / json / html
                                      |
                                HUMAN REVIEW
## Security boundary

```text
AI / CLI / API
      |
      v
Structured operation
      |
      v
Policy validation
      |
      v
Scope Guard
      |
      +---- BLOCKED
      |
      v
Secure Executor
      |
      v
Tool Adapter
      |
      v
External Tool
The Scope Guard must remain an authorization boundary. User interface,
automation, planning, and AI components must not bypass it.

## Scope Guard

Relevant implementation:

`bhairava/scope_guard.py`

Scope configuration supports:

- authorized domains
- authorized URLs
- exclusions
- request-rate limits
- concurrency limits

Excluded targets take precedence over allowed targets.

Every active operation must be subject to scope validation before the
corresponding external security tool is executed.

## Secure Executor

Relevant implementation:

`bhairava/core/executor.py`

The executor provides the controlled subprocess boundary.

Expected controls include:

- argument-array subprocess execution
- avoiding `shell=True`
- timeout enforcement
- stdout/stderr limits
- controlled environment variables
- Scope Guard enforcement
- rate limiting
- concurrency control
- output handling and redaction where applicable

External tools should not be executed directly from arbitrary user or AI
input.

## Tool adapters

Location:

`bhairava/tools/adapters/`

Adapters provide a consistent interface around external security tools.

Adapters are registered through the tool registry.

Missing external dependencies should be handled according to the
framework's dependency and stage policies.

## Pipeline engines

### Recon

Location:

`bhairava/recon/`

Responsibilities:

- enumerate authorized assets
- collect reconnaissance results
- normalize discovered hosts
- re-check discovered assets against scope

### Discovery

Location:

`bhairava/discovery/`

Responsibilities:

- discover URLs and endpoints
- process supported discovery sources
- normalize results
- filter results through scope controls

### Detection

Location:

`bhairava/detection/`

Responsibilities:

- run configured detection tooling
- convert tool output into structured findings
- ensure discovered targets remain within authorization boundaries

### Validation

Location:

`bhairava/validation/`

Responsibilities:

- controlled validation of candidates
- safety and approval policies
- prevention of unsupported or destructive validation actions

## Findings engine

Location:

`bhairava/findings/`

Responsibilities include:

- finding models
- fingerprints
- lifecycle transitions
- correlation
- deduplication
- human review state

Typical lifecycle:

```text
CANDIDATE
    |
    v
NEEDS_REVIEW
    |
    +----> REJECTED
    |
    +----> DUPLICATE
    |
    v
CONFIRMED
    |
    v
REPORTED
AI assistance must not independently mark a finding as confirmed.

## Evidence engine

Location:

`bhairava/evidence/`

Responsibilities:

- collection
- sanitization
- hashing
- persistence

Sensitive values should be sanitized before evidence is persisted or
included in reports.

## Reporting engine

Location:

`bhairava/reporting/`

Supported formats:

- Markdown
- JSON
- HTML

Reports should distinguish automated observations from findings that have
received human confirmation.

## AI enhancement layer

Location:

`bhairava/agent/`

AI is optional and disabled by default.

```text
AI
 |
 | suggested action
 v
Policy Engine
 |
 v
Scope Guard
 |
 v
Secure Executor
 |
 v
Tool
AI must not:

- expand authorized scope
- remove exclusions
- disable safety controls
- remove rate limits
- remove timeouts
- execute arbitrary shell commands
- approve destructive operations
- independently confirm findings

Target content supplied to an AI provider must be treated as untrusted
data rather than trusted instructions.

## Storage

Location:

`bhairava/storage/`

SQLite provides persistent application storage for data such as:

- jobs
- findings
- evidence
- tool execution records
- schema versions

## Pipeline stages

The documented pipeline contains seven stages:

```text
scope
  |
recon
  |
discovery
  |
detection
  |
validation
  |
evidence
  |
report
Pipeline controls such as dry-run and resume are available where provided
by the installed version.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Success |
| 1 | General error |
| 2 | Invalid configuration |
| 3 | Scope violation |
| 4 | Missing dependency |
| 5 | Validation failure |

## Testing architecture

The test suite is designed to avoid requiring live third-party targets.

Testing areas include:

- Scope Guard
- executor behavior
- tool adapters
- findings lifecycle
- evidence handling
- validation controls
- reporting
- AI policy
- storage
- jobs
- pipeline behavior

Currently verified test result:

```text
124 passed
The exact count may change as the project evolves.

## Design principles

1. Authorization before active testing.
2. Scope enforcement before tool execution.
3. Explicit operator control.
4. Safe subprocess execution.
5. Least privilege.
6. Rate limiting.
7. Evidence sanitization.
8. Human review of security findings.
9. AI as an optional assistant, not an authorization authority.
10. Public accessibility does not imply authorization.

---

**Use BHAIRAVA-BB only on targets you are authorized to test.**


