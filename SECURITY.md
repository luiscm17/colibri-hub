# Security Policy

## Reporting a vulnerability

**Do not open a public issue for a security vulnerability.** Disclosures stay
private until the maintainers have triaged and fixed the issue.

Report a suspected vulnerability privately using the GitHub Security
Advisories workflow for this repository:

1. Open **Security** → **Advisories** → **New draft security advisory** on the
   repository.
2. Fill in the advisory form with the details below.
3. Do not publish the advisory or request a CVE until the maintainers confirm
   the issue is resolved.

Alternatively, if you know the maintainers, report directly to them by email
or private message.

## What to include

- **Type**: what class of vulnerability it is (e.g. SQL injection, privilege
  escalation, information disclosure, dependency issue).
- **Affected component**: the bounded context, endpoint, migration, or
  dependency involved.
- **Steps to reproduce**: minimal, with inputs and state required. Redact all
  credentials, secrets, and personally identifiable data.
- **Impact**: what an attacker could do, and under which conditions.
- **Suggested fix** (optional): if you have a patch or mitigation, include it.

## What to expect

- **Acknowledgement**: maintainers confirm receipt within a few business days.
- **Triage**: the report is assessed against current releases and branches.
- **Fix and disclosure**: after a fix ships, the advisory is published with
  affected versions and mitigation guidance.

## Scope

This policy covers the Colibri Hub repository: the Python backend
(`backend/`), the React frontend (`frontend/`), the Supabase migrations
(`supabase/`), and the project documentation. Vulnerabilities in third-party
dependencies should be reported here when they affect this repository's
runtime.
