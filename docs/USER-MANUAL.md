# BHAIRAVA-BB User Manual

**Purpose:** Authorized bug bounty and security research.
**Coverage:** Operational guide and documented development milestones through V7.

> Version note: The inspected executable reports v1.0.0. Project milestone labels and package version are not necessarily the same.

## Contents

1. [Authorization and safe use](#1-authorization-and-safe-use)
2. [Installation and first checks](#2-installation-and-first-checks)
3. [Command reference](#3-command-reference)
4. [Scope configuration](#4-scope-configuration)
5. [AI configuration](#5-ai-configuration)
6. [Workflows](#6-workflows)
7. [Jobs and reports](#7-jobs-and-reports)
8. [Troubleshooting](#8-troubleshooting)
9. [V1–V7 documentation](#9-v1v7-documentation)
10. [Official references](#10-official-references)

## 1. Authorization and safe use

Use BHAIRAVA-BB only on systems you own or have explicit authorization to test. Public accessibility does not imply permission. Confirm the program policy, target scope, exclusions, request limits, and testing windows before running active operations. Start with scope validation and a pipeline dry run. Review findings manually and sanitize evidence before sharing it.

Examples use `example.com` as a placeholder. Replace it only with an authorized target.

## 2. Installation and first checks

The repository identifies Python 3.11+ as a requirement. Review `install.sh` before running it with elevated privileges.

```bash
git clone https://github.com/GuhanSenthil/BHAIRAVA-BB.git
cd BHAIRAVA-BB
chmod +x install.sh
sudo ./install.sh
bhairava --version
bhairava --help
bhairava status
bhairava tools
bhairava config validate
bhairava scope show
```

## 3. Command reference

Use `bhairava COMMAND --help` to verify options for your installed version.

### Global options

```bash
bhairava --help
bhairava --version
bhairava --no-color status
bhairava --scope config/scope.yaml scope show
```

### Scope and configuration

```bash
bhairava scope show
bhairava scope validate https://example.com
bhairava config validate
bhairava --scope config/scope.yaml config validate
```

Validate the target against your configured scope before testing. Use only systems you are explicitly authorized to assess.

### Reconnaissance

```bash
bhairava recon --target https://example.com
bhairava recon --target https://example.com --timeout 120 --data-dir data
```

### Endpoint discovery

```bash
bhairava discover --target https://example.com
bhairava discover --target https://example.com --timeout 120
bhairava discover --target https://example.com --active
```

The `--active` option may generate additional traffic. Use it only when the target authorization and program rules explicitly permit active discovery.

### Vulnerability scanning

```bash
bhairava scan --target https://example.com
bhairava scan --target https://example.com --severity critical,high
bhairava scan --target https://example.com --severity critical,high --timeout 600 --data-dir data
```

The scanner uses Nuclei according to the inspected CLI. Treat results as candidate findings and review them manually. Scan only authorized targets.

### Finding validation

```bash
bhairava validate --input data/findings/latest.json
bhairava validate --input data/findings/latest.json --timeout 300
```

The `--yes` option automatically approves impactful validators, including sqlmap according to CLI help. Use it only after reviewing authorization and potential impact.

### Report generation

```bash
bhairava report --input data/findings/latest.json --output reports --format markdown,json,html
bhairava report --input data/findings/latest.json --output reports --format markdown,json,html --target https://example.com --program \"Authorized Example Program\"
```

Supported report formats are `markdown`, `json`, and `html`. Review reports for accuracy and sensitive information before sharing them.

## 4. Pipeline execution

Start with a dry run:

```bash
bhairava pipeline --dry-run
```

Execute only after reviewing the scope and planned stages:

```bash
bhairava pipeline
bhairava pipeline --data-dir data --reports-dir reports --timeout 300
bhairava pipeline --resume JOB_ID
```

Replace `JOB_ID` with an actual job identifier. A dry run previews the plan; it does not guarantee that a live run will succeed.

## 5. Job management

```bash
bhairava jobs list
bhairava jobs list --limit 50 --data-dir data
bhairava jobs show JOB_ID
bhairava jobs cancel JOB_ID
bhairava jobs delete JOB_ID
```

Inspect jobs before deleting them because deletion can remove associated artifacts. The inspected CLI supports resumption through `pipeline --resume JOB_ID`; it does not expose a separate `jobs resume` command.

## 6. Troubleshooting

### Command not found

```bash
cd ~/BHAIRAVA-BB
.venv/bin/python -m bhairava --version
```

### Configuration or scope errors

```bash
bhairava config validate
bhairava scope show
bhairava scope validate https://example.com
```

Check YAML indentation, the selected scope file, target authorization, and exclusions. Do not bypass a scope rejection to force a scan.

### Missing external tools

```bash
bhairava tools
```

Install missing dependencies using their official documentation and the repository installation instructions.

### Check installed command options

```bash
bhairava --help
bhairava scan --help
bhairava pipeline --help
bhairava agent --help
```

### Exit codes

The existing scope-management documentation lists these codes:

| Code | Meaning |
|---:|---|
| 0 | Success |
| 1 | General error |
| 2 | Invalid configuration |
| 3 | Scope violation |
| 4 | Missing dependency |
| 5 | Validation failure |

## 7. V1–V7 documentation and further reading

This manual covers operational use and the documented V1–V7 development period. It does not claim that every historical feature is present in the current checkout. The inspected executable reports version `1.0.0`; milestone labels and package versions are different concepts.

- [Main README](../README.md)
- [Documentation index](README.md)
- [Architecture](architecture.md)
- [Scope management](scope-management.md)
- [Troubleshooting](troubleshooting.md)
- [V6 architecture](architecture/BHAIRAVA-BB-V6-ARCHITECTURE.md)
- [Changelog](../CHANGELOG.md)
- [Security policy](../SECURITY.md)
- [Contribution guide](../CONTRIBUTING.md)

## 8. Official references

- [BHAIRAVA-BB GitHub repository](https://github.com/GuhanSenthil/BHAIRAVA-BB)
- [Python documentation](https://docs.python.org/3/)
- [Git documentation](https://git-scm.com/doc)
- [Nuclei documentation](https://docs.projectdiscovery.io/tools/nuclei/overview)
- [ffuf repository](https://github.com/ffuf/ffuf)
- [LinkFinder repository](https://github.com/GerbenJavado/LinkFinder)
- [Ollama documentation](https://docs.ollama.com/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

**Maintenance:** When CLI options, configuration fields, dependencies, output paths, or safety controls change, update this manual and verify the commands against the relevant checkout before publishing.
