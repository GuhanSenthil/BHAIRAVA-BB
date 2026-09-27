# Scope Management

The Scope Guard is the authorization boundary for BHAIRAVA-BB.

BHAIRAVA-BB does not grant authorization to test a target. The operator
must obtain the required permission before active security testing.

## Scope file

A YAML scope configuration can contain authorized targets, exclusions,
and operational limits.

Example:

```yaml
program:
  name: "Example Authorized Program"

scope:
  domains:
    - "example.com"
    - "*.example.com"

  urls:
    - "https://example.com"

  excluded:
    - "admin.example.com"
    - "*.internal.example.com"

limits:
  requests_per_second: 5
  max_concurrency: 3
The exact accepted fields and matching semantics are determined by the
installed BHAIRAVA-BB implementation.

## Writing scope safely

Before an active operation:

1. Read the original authorization.
2. Identify explicitly authorized domains.
3. Identify explicitly authorized URLs.
4. Identify exclusions.
5. Identify prohibited techniques.
6. Identify request-rate restrictions.
7. Identify concurrency restrictions.
8. Identify required notice or consent.
9. Encode only authorized targets.
10. Validate the resulting scope.

Do not infer authorization from:

- DNS records
- search results
- certificates
- public accessibility
- links
- robots.txt
- third-party databases

Public accessibility is not authorization.

## Exclusions

Exclusions identify targets that must not be tested.

```yaml
scope:
  domains:
    - "*.example.com"

  excluded:
    - "admin.example.com"
Exclusions must take precedence over an otherwise matching authorization
rule.

## Scope validation

Validate the configuration:

```bash
bhairava config validate
Where supported:

```bash
bhairava scope validate https://example.com
A blocked target should result in the documented scope-violation exit
code.

## Rate limits

Respect the rate limits defined by the authorized program.

```yaml
limits:
  requests_per_second: 5
  max_concurrency: 3
If the program specifies a lower rate, use the lower rate.

Never increase the configured rate merely to finish faster.

## Passive versus active research

Passive research and active testing may have different authorization
requirements.

Do not assume that permission for passive research automatically grants
permission for active testing.

Follow the program rules and applicable law.

## Scope changes

If authorization changes:

1. Stop affected operations.
2. Update the scope configuration.
3. Validate the new configuration.
4. Confirm exclusions.
5. Confirm technique restrictions.
6. Resume only after authorization is clear.

AI-generated scope expansion is not authorization.

## Separate scope files

Keep separate scope files for separate authorized programs.

```text
config/
  program-a.yaml
  program-b.yaml
  scope.example.yaml
Do not mix unrelated programs into one authorization file.

## Secrets

Do not store credentials or API keys in scope files.

Never commit:

```text
.env
.env.local
*.key
*.pem
## When authorization is unclear

Stop.

If you cannot clearly determine whether a target or technique is
authorized, treat it as unauthorized until the owner or program provides
clarification.

---

**USE BHAIRAVA-BB ONLY ON TARGETS YOU ARE AUTHORIZED TO TEST.**

**ACTIVE TESTING REQUIRES EXPLICIT AUTHORIZATION FOR THE TARGET AND
INTENDED TECHNIQUE.**


