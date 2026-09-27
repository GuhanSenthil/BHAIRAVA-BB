# Troubleshooting

## Installation

### `bhairava` command not found

Use:

```bash
python -m bhairava --version
Windows PowerShell:
.\.venv\Scripts\Activate.ps1
python -m bhairava --version
### `ModuleNotFoundError: bhairava`
cd C:\Users\guhan\BHAIRAVA-BB-v2
.\.venv\Scripts\Activate.ps1
python -c "import bhairava; print(bhairava.__version__)"
## Version

```bash
bhairava --version
python --version
## Tests

```bash
pytest -q
Currently verified:

```text
124 passed
The number may change as tests are added.

## Ruff

```bash
ruff check .
Expected successful result:

```text
All checks passed!
## Scope Guard

### Target is blocked

Check:

```bash
bhairava config validate
bhairava scope --help
Review:

- hostname
- URL
- protocol
- exclusions
- wildcard rules
- authorization document

Do not bypass Scope Guard.

### Target unexpectedly allowed

Stop the operation.

Review the authorization configuration and treat a genuine
scope-boundary failure as a security defect.

## External tools

```bash
bhairava tools
For an individual dependency:

```bash
<tool> --version
Do not execute an external security tool against a target until the
target and intended technique are authorized.

## Pipeline

Inspect:

```bash
bhairava pipeline --help
Use dry-run where supported:

```bash
bhairava pipeline --dry-run
If dry-run unexpectedly performs network activity, stop and investigate.

## Jobs

Inspect:

```bash
bhairava jobs --help
Before resuming a security-testing job, verify:

- authorization is still valid
- scope has not changed
- exclusions remain correct
- rate limits remain correct
- intended stages remain authorized

## AI

Inspect:

```bash
bhairava agent --help
AI should not:

- expand scope
- remove exclusions
- disable rate limits
- disable timeouts
- generate arbitrary shell commands
- approve destructive actions
- independently confirm findings

Unexpected behavior should be treated as a security defect.

## Secrets

Never put API keys, passwords, tokens, cookies, or private keys in:

- source files
- README files
- scope files
- issue reports
- evidence
- Git commits

If a real credential is exposed, rotate it immediately.

## Evidence

Before sharing evidence:

- remove secrets
- verify target authorization
- check disclosure rules
- distinguish candidates from confirmed findings

## Security defects

If a problem affects Scope Guard, executor isolation, secret handling,
or AI policy enforcement, follow `SECURITY.md` before public disclosure.

## Getting help

Include:

- BHAIRAVA-BB version
- Python version
- operating system
- exact command
- expected behavior
- actual behavior
- sanitized output

Never include secrets or unauthorized target information.

---

**When authorization, scope, or safety behavior is unclear:
STOP THE OPERATION AND VERIFY BEFORE CONTINUING.**


