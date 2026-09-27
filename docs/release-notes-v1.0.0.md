# BHAIRAVA-BB v1.0.0

## Overview

BHAIRAVA-BB v1.0.0 is a documented release of an authorized security
research framework.

The framework is designed to place authorization and scope enforcement
before active security operations.

## Highlights

### Scope Guard

The framework provides a dedicated scope-management layer intended to
prevent active operations from proceeding against targets outside the
configured authorization boundary.

### Secure execution

External security tools are intended to run through a centralized
execution boundary with controls such as argument-based execution,
timeouts, output limits, and scope enforcement.

### Security research pipeline

The documented seven-stage pipeline is:

```text
scope
  ↓
recon
  ↓
discovery
  ↓
detection
  ↓
validation
  ↓
evidence
  ↓
report
### Findings

Findings are represented as structured records with lifecycle states and
deduplication/correlation support.

Automated candidates are not intended to replace human confirmation.

### Evidence

Evidence handling includes sanitization and hashing capabilities.

Sensitive information should not be published in reports or issue
submissions.

### AI

AI is an optional enhancement layer and is disabled by default.

AI is intended to assist with planning and analysis while remaining
behind policy and authorization controls.

AI must not:

- expand authorization
- remove exclusions
- disable safety controls
- execute arbitrary shell commands
- approve destructive operations
- independently confirm findings

### Testing

Verified project test result:

```text
124 passed
## Installation

```bash
git clone https://github.com/GuhanSenthil/BHAIRAVA-BB.git
cd BHAIRAVA-BB
python3 -m pip install .
bhairava --version
## Initial checks

```bash
bhairava --help
bhairava status
bhairava tools
bhairava config validate
Before any active testing, configure and verify the authorization scope.

## What BHAIRAVA-BB does not provide

BHAIRAVA-BB does not:

- grant authorization
- make third-party systems automatically in scope
- replace program rules
- replace human security review
- make findings automatically valid
- authorize destructive testing

## Documentation

- [README](https://github.com/GuhanSenthil/BHAIRAVA-BB#readme)
- [Architecture](architecture.md)
- [Scope Management](scope-management.md)
- [Troubleshooting](troubleshooting.md)
- [Security Policy](../SECURITY.md)
- [Contributing](../CONTRIBUTING.md)

## Responsible use

Use BHAIRAVA-BB only against systems for which you have the required
authorization.

Public accessibility does not establish authorization.

Active testing requires explicit authorization for the target and the
intended technique.

When authorization or scope is unclear, do not test.


