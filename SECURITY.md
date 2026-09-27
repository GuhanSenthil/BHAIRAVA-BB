# Scope, Authorization, Notice & Testing Rules

## 1. Explicit Authorization and Consent Required

**BHAIRAVA-BB must only be used against systems for which the operator has explicit authorization to perform the intended security activity.**

Before conducting any testing, the operator must establish that:

1. The target owner or authorized program has granted permission.
2. The intended target is explicitly within the authorized scope.
3. The intended testing technique is permitted.
4. Applicable rate limits and testing restrictions are understood.
5. Any required notification, consent, or rules-of-engagement requirements have been satisfied.

A publicly accessible domain, IP address, API, application, service, or device **does not constitute authorization**.

### Notice and Consent

Where the target owner, security program, organization, contract, or rules of engagement require advance notice or consent, **that notice and consent must be obtained before testing begins**.

The operator should retain appropriate evidence of authorization, such as:

- Bug-bounty program rules and scope
- Written authorization
- Rules of engagement
- Testing authorization emails
- Contractual authorization
- Internal security-testing approval

Do not assume authorization from silence, accessibility, ownership of a related domain, or authorization for a different asset.

**BHAIRAVA-BB does not provide, create, or infer authorization. The operator must establish authorization independently.**

---

## 2. Passive Testing

Passive activities generally avoid intentionally sending security-testing traffic to the target infrastructure.

Examples may include:

- Reviewing publicly available information
- Reviewing public DNS records
- Certificate-transparency research
- Reviewing publicly available historical URLs
- Analyzing previously collected datasets
- Local analysis of downloaded or provided artifacts
- Reviewing public documentation and metadata

Even passive reconnaissance must respect:

- Applicable law
- Terms of service
- Bug-bounty rules
- Privacy requirements
- Program-specific restrictions
- Restrictions on automated collection

**Passive does not automatically mean authorized.** If a program prohibits a particular information source or collection technique, that restriction must be followed.

---

## 3. Active Testing

Active testing intentionally interacts with the target or its infrastructure.

Examples include:

- HTTP requests generated for vulnerability discovery
- Port or service probing
- Automated endpoint fuzzing
- Parameter testing
- Vulnerability scanning
- Nuclei scanning
- Dalfox testing
- SQL injection testing
- Authentication testing
- Access-control testing
- Any validation that intentionally sends security-testing payloads

**Active testing requires explicit authorization for the target and the intended testing activity.**

Before active testing, verify:

```text
Authorization
    ↓
Target in Scope
    ↓
Technique Permitted
    ↓
Rate Limits Confirmed
    ↓
Excluded Assets Confirmed
    ↓
Scope Guard Validation
    ↓
Active Testing
```

If any required authorization or scope condition is missing, **do not perform the active test**.

---

## 4. Higher-Impact Testing

Testing that could affect availability, data integrity, confidentiality, accounts, or production systems requires additional explicit authorization where applicable.

Examples include:

- Destructive payloads
- Denial-of-service testing
- Resource-exhaustion testing
- Data modification
- Data deletion
- Credential attacks
- Account lockout testing
- Exploit chains that may alter system state
- Actions involving real user data
- Actions that could disrupt production services

These activities must not be performed merely because the target is within a general bug-bounty scope.

**A target being in scope does not automatically mean every testing technique is authorized.**

---

## 5. Scope Guard Requirement

BHAIRAVA-BB's **Scope Guard is a mandatory security boundary**.

Every active operation must pass scope validation before the external tool or network operation is executed.

The framework must respect:

- Authorized domains
- Authorized URLs
- Authorized hosts
- Explicit exclusions
- Program-specific restrictions
- Configured rate limits
- Configured concurrency limits

Out-of-scope targets must be blocked.

**Operators must never bypass, disable, or weaken Scope Guard to conduct testing.**

---

## 6. Operator Responsibility

The operator is responsible for:

- Obtaining authorization
- Confirming consent or required notice
- Understanding the rules of engagement
- Configuring the correct scope
- Respecting exclusions
- Respecting rate limits
- Selecting only permitted testing techniques
- Protecting collected information
- Reporting vulnerabilities according to the applicable program rules

BHAIRAVA-BB is a security research framework. **It is not an authorization mechanism and does not grant permission to test any target.**

### Final Notice

> **USE BHAIRAVA-BB ONLY ON TARGETS YOU ARE AUTHORIZED TO TEST.**
>
> **OBTAIN REQUIRED NOTICE AND CONSENT BEFORE ACTIVE TESTING.**
>
> **PASSIVE RESEARCH MUST STILL COMPLY WITH APPLICABLE RULES.**
>
> **ACTIVE TESTING REQUIRES EXPLICIT AUTHORIZATION FOR THE TARGET AND INTENDED TECHNIQUE.**
>
> **WHEN AUTHORIZATION OR SCOPE IS UNCLEAR, DO NOT TEST.**
