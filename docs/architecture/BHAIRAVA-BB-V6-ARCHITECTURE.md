# BHAIRAVA-BB V6 Architecture

## 1. Overview

BHAIRAVA-BB V6 is an authorized security research framework designed around deterministic scope enforcement, controlled execution, asset intelligence, finding correlation, evidence integrity, resumable jobs, planning, and reporting.

The V6 architecture extends the existing BHAIRAVA-BB framework without removing the established safety boundaries.

## 2. Core Pipeline

The V6 logical pipeline is:

Scope
-> Recon
-> Asset Intelligence
-> Discovery
-> Detection
-> Finding Correlation
-> Evidence
-> Review
-> Report
-> Completed

The Scope Guard remains mandatory before active network or security operations.

## 3. Scope

Scope defines:

- authorized domains
- authorized URLs
- exclusions
- request-rate limits
- concurrency limits
- program information

Public accessibility does not establish authorization.

When authorization or scope is unclear, testing must not proceed.

## 4. Secure Execution

Security-sensitive operations must use the controlled execution architecture.

The executor provides:

- argument-array execution
- no shell=True execution
- timeout controls
- output limits
- environment controls
- scope enforcement
- rate limiting
- concurrency controls
- secret redaction

AI components must not bypass these controls.

## 5. Asset Intelligence

V6 introduces an asset intelligence layer.

The asset pipeline is:

Recon
-> Normalization
-> Deduplication
-> Technology Fingerprinting
-> Relationship Graph
-> Asset Repository

Supported asset categories include:

- DOMAIN
- SUBDOMAIN
- URL
- ENDPOINT
- IP
- SERVICE

Assets receive stable identifiers so observations from multiple sources can be correlated.

## 6. Asset Normalization

Normalization converts observations from different tools into canonical asset representations.

Normalization supports:

- domain normalization
- URL normalization
- asset-type normalization
- canonical identifiers

The objective is to prevent duplicate representations of the same asset.

## 7. Asset Deduplication

Asset deduplication uses stable asset identifiers.

Multiple observations can be merged while preserving:

- sources
- technologies
- metadata
- parent relationships
- scope status
- first-seen information
- last-seen information

## 8. Technology Fingerprinting

Technology fingerprinting is observation-based.

It can derive technology information from supplied observations such as:

- HTTP headers
- response bodies
- cookies

Fingerprinting does not itself perform network access.

## 9. Asset Relationships

Assets can be represented as relationships such as:

Domain
+-- Subdomain
    +-- URL
        +-- Endpoint

Parent-child relationships allow the framework to construct an asset graph.

## 10. Findings

Findings retain the established lifecycle:

CANDIDATE
-> NEEDS_REVIEW
-> CONFIRMED
-> REPORTED

Additional states include:

- DUPLICATE
- REJECTED

V6 extends the finding model while preserving compatibility with the existing finding APIs.

## 11. Finding Correlation

Multiple tools may observe the same underlying issue.

The correlation layer combines observations and evidence so that multiple tool outputs can contribute to one finding.

Correlation is deterministic and does not automatically convert an observation into a confirmed vulnerability.

Human review remains part of the lifecycle.

## 12. Finding Confidence

Confidence represents the framework's assessment of supporting observations.

Confidence does not replace human review or authorization.

## 13. Evidence

Evidence is structured and associated with findings.

Evidence can contain:

- evidence ID
- finding ID
- target
- source
- timestamp
- tool output
- request metadata
- response metadata
- reproduction information
- confidence
- SHA-256 integrity value

Sensitive information is sanitized before evidence is persisted.

## 14. Evidence Integrity

Evidence integrity uses hashing to provide an integrity reference for collected evidence.

The integrity value is derived from the evidence content and identifying metadata.


## 15. Evidence Sanitization

Sensitive values must be redacted before storage or reporting.

The sanitizer supports sensitive headers and credential-like values.

Synthetic secrets used by tests are test fixtures and are not operational credentials.

## 16. Resumable Jobs

V6 introduces checkpoint and resume support.

A job can progress through pipeline stages while maintaining checkpoint information.

The architecture supports recovery from interrupted execution without requiring the entire workflow to restart.

## 17. Pipeline Stages

The V6 stage model includes:

- scope
- recon
- asset intelligence
- discovery
- detection
- correlation
- evidence
- review
- report
- completed

## 18. Database Migrations

V6 introduces migration infrastructure for controlled database evolution.

Migration changes are versioned and applied through the migration runner.

The migration architecture is designed to preserve existing data while allowing new V6 structures to be introduced.


## 19. Planning

V6 introduces deterministic planning.

The planner can represent the intended execution plan before active operations occur.

A dry-run plan allows operators to inspect the proposed workflow without performing network testing.


## 20. Reporting

Reporting consumes structured findings and evidence.

Reporting components include:

- templates
- exporters

Reports should distinguish observations, evidence, validation status, and confirmed findings.

## 21. AI Architecture

AI is optional and disabled by default.

The safety architecture is:

AI
-> Policy Engine
-> Scope Guard
-> Secure Executor
-> Evidence
-> Human Review

AI must not:

- expand scope
- remove exclusions
- disable rate limits
- disable concurrency limits
- execute arbitrary shell commands
- approve destructive operations
- independently confirm findings

## 22. Tool Registry

The framework supports controlled tool adapters for the configured security research toolchain.

The existing tool registry includes:

- subfinder
- amass
- assetfinder
- httpx
- gau
- waybackurls
- ffuf
- linkfinder
- nuclei
- dalfox
- sqlmap

Tools must operate within the configured authorization and scope boundaries.

## 23. Safety Model

The framework is intended for authorized security research.

The operator is responsible for:

- authorization
- rules of engagement
- target scope
- excluded targets
- rate limits
- permitted techniques
- impact restrictions

Higher-impact testing requires appropriate additional authorization.

When authorization or scope is unclear:

DO NOT TEST.

## 24. V6 Package Layout

```text
bhairava/
+-- assets/
|   +-- models.py
|   +-- normalizer.py
|   +-- deduplicator.py
|   +-- fingerprint.py
|   +-- graph.py
|   +-- repository.py
+-- evidence/
|   +-- collector.py
|   +-- integrity.py
|   +-- models.py
|   +-- sanitizer.py
|   +-- store.py
+-- findings/
|   +-- correlator.py
|   +-- confidence.py
|   +-- deduplicator.py
|   +-- lifecycle.py
+-- jobs/
|   +-- checkpoint.py
|   +-- resume.py
|   +-- stages.py
+-- migrations/
|   +-- runner.py
+-- planning/
|   +-- planner.py
|   +-- models.py
+-- reporting/
    +-- templates.py
    +-- exporters.py

## 25. Verification
The V6 implementation has been regression-tested before integration.
The verified test suite contains:
152 tests passed.
The implementation should continue to pass the full regression suite before future architectural changes are merged.
## 26. Compatibility Principle
V6 is additive.
Existing public APIs should not be removed merely to introduce V6 functionality.
Where V6 introduces new models or lifecycle representations, compatibility adapters should preserve established interfaces where practical.
## 27. Development Rule
Every future architectural change should follow:
Design
-> Implement
-> Unit tests
-> Full regression
-> Diff check
-> Secret review
-> Commit
-> Pull request
-> CI
-> Review
-> Merge
