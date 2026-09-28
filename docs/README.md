# BHAIRAVA-BB Documentation

## Architecture

- [BHAIRAVA-BB V6 Architecture](architecture/BHAIRAVA-BB-V6-ARCHITECTURE.md)

## Core Architecture

BHAIRAVA-BB V6 follows this pipeline:

1. Scope
2. Recon
3. Asset Intelligence
4. Discovery
5. Detection
6. Finding Correlation
7. Evidence
8. Review
9. Report

## Safety

All active security operations require appropriate authorization and must remain within the configured scope and rules of engagement.

When authorization or scope is unclear, do not test.

## V6 Components

| Component | Purpose |
|---|---|
| Assets | Asset normalization, deduplication and relationships |
| Findings | Correlation, confidence and lifecycle |
| Evidence | Structured evidence and integrity |
| Jobs | Checkpoint and resume |
| Migrations | Database evolution |
| Planning | Deterministic dry-run planning |
| Reporting | Templates and exporters |

## Verification

The current V6 implementation has been validated with the full automated test suite.

Current baseline:

**152 tests passed.**

## Evidence Integrity

Evidence is sanitized and associated with integrity metadata before persistence.

## Database Migrations

V6 uses versioned migration infrastructure for controlled database evolution.

## Deterministic Planning

V6 supports deterministic dry-run planning before active operations.