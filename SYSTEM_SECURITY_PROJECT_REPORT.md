# CocoScan System Security Project Report

**Assessment date:** 2026-11-10  
**System:** CocoScan  
**Scope:** Flask web application, Supabase database and Storage, local security state, PWA clients, TFLite inference, backups, CI security controls  
**Security baseline:** OWASP Top 10:2025

> This report describes controls implemented in the repository and evidence obtained from local automated testing. It is not a penetration-test certificate, a Supabase configuration attestation, or a guarantee that deployment infrastructure is secure.

## Executive Summary

CocoScan has implemented a substantial application-security baseline:

- CSRF protection and security headers, including enforced CSP.
- Role-based and object-level authorization for reports and workflow actions.
- Signed, scoped offline capability tokens.
- Secure session-cookie defaults and logout cleanup.
- TFLite-only inference with SHA-256 model verification.
- Pinned dependencies, Dependabot, pip-audit, Bandit, and Gitleaks CI.
- Encrypted database backups using Fernet.
- Hash-chained local audit logs with integrity verification and optional webhook alerting.
- SQLite-backed rate limiting for login, prediction, and report submission endpoints.
- Private Supabase Storage compatibility using short-lived signed URLs.

Automated evidence at the time of this report:

| Check | Result |
|---|---:|
| Python regression suite | **214 passed** |
| `pip-audit -r requirements.txt` | **No known vulnerabilities** |
| `bandit -r app model main.py -ll` | **No issues identified** |
| Gitleaks | Configured in GitHub Actions; run the workflow before release |
| Authenticated penetration test | **Not yet performed** |

## 1. System and Assets

### 1.1 Architecture and asset inventory

| Asset | Purpose | Protection |
|---|---|---|
| Flask application in [`main.py`](./main.py) | Web routes, sessions, report workflows, APIs, admin functions | Role checks, object authorization, CSRF, headers, rate limits, validation |
| Supabase PostgreSQL | Users, profiles, reports, chats, visits, schedules, audit-related application data | Supabase RLS, authenticated client access, application authorization |
| Supabase Storage `reports` bucket | Report, supporting, visit, and dataset images | Bucket configured private; application requests short-lived signed URLs |
| Local security SQLite database | OTP metadata, lockouts, remember-token hashes, rate limits, audit chain | Filesystem access control; sensitive values hashed where applicable; not database-level encrypted |
| Local push SQLite database | Web Push subscriptions and browser key material | Filesystem access control; excluded from Git; not database-level encrypted |
| `model/pest_classifier.tflite` | Production pest classifier | TFLite-only loader and SHA-256 verification through `PEST_MODEL_SHA256` |
| Encrypted backup archives | Database recovery copies | Fernet encryption; `.json.gz.enc`; key supplied through environment/secret manager |
| VAPID private key | Signs Web Push notifications | Environment variable preferred; generated file `app/vapid_private.pem` is Git-ignored |
| CI workflows | Dependency and source security checks | GitHub Actions with read-only repository permissions |
| PWA/static frontend | Farmer and staff browser interface | CSP, CSRF token injection, secure cookies, browser-side validation |

### 1.2 Trust boundaries

1. Browser to Flask: HTTPS is required in production; cookies are HttpOnly/SameSite and CSRF is enforced for unsafe methods.
2. Flask to Supabase: Supabase client uses the configured HTTPS project URL.
3. Flask to external APIs: Brevo, Geoapify, Nominatim, weather services, and optional alert webhook use HTTPS endpoints.
4. Flask to local files: model, SQLite databases, upload/cache directories, and encrypted backups are local deployment assets.
5. Supabase Storage to browser: private object paths are converted to short-lived signed URLs.

## 2. Authentication and Access Control

### 2.1 Authentication

- Users authenticate through the `/login` flow against Supabase user records.
- Passwords are verified with Werkzeug password-hash verification in [`app/password_utils.py`](./app/password_utils.py).
- Passwords are not stored in plaintext.
- Failed login attempts are tracked and account lockout is applied.
- OTP codes are generated with secure randomness and stored as HMAC digests using an OTP pepper.
- Remember-me tokens are stored as hashes and restricted to farmer sessions.
- Offline authentication uses a signed, scoped, expiring farmer capability token rather than browser-readable identity cookies.

### 2.2 RBAC and BOLA/BFLA prevention

Roles include:

- Farmer
- Agriculturist
- LGU
- Admin

Authorization is enforced by `require_role` and centralized report authorization in [`main.py`](./main.py). Report access checks ownership, assignment, and staff permissions before returning report details or allowing mutations. Workflow transitions are checked against a server-side transition map rather than trusting client-provided status values.

This addresses:

- **BOLA:** users cannot retrieve or mutate reports outside their authorized ownership/assignment scope.
- **BFLA:** role decorators prevent lower-privileged users from invoking administrative or staff-only functions.

Required production evidence: execute authenticated cross-user and cross-role tests using two farmer accounts, an agriculturist, an LGU account, and an admin account.

## 3. Session Management

Configured in [`main.py`](./main.py):

- `SESSION_COOKIE_HTTPONLY=True`
- `SESSION_COOKIE_SAMESITE="Lax"`
- `SESSION_COOKIE_SECURE=True` in production
- Session inactivity/expiration handling
- Session clearing on logout
- Remember-me token validation, expiry, rotation/cleanup, and logout deletion
- Offline capability cookie is HttpOnly, scoped, signed, and expiring
- Sensitive routes send `Cache-Control: no-store`

The application does not treat legacy browser-readable offline identity cookies as production authentication.

## 4. Input Handling and Data Protection

### 4.1 Validation and injection resistance

- Login, signup, report, location, email, password, and upload inputs use application validators.
- Database queries use Supabase query builders or bound SQLite parameters.
- Dynamic SQL placeholder lists are generated only from trusted list lengths; values remain bound parameters.
- Jinja autoescaping and explicit escaping are used for rendered audit values and user-controlled content.
- Upload handling validates image content, size, type, and storage limits before persistence.
- Path traversal is blocked for backup retrieval and deletion.

### 4.2 Encryption and sensitive data

**In transit**

- Supabase and external service integrations use HTTPS endpoints.
- HSTS is sent for secure requests.
- Production deployment must terminate TLS at the application or trusted reverse proxy.

**At rest**

- Passwords: salted password hashes, not plaintext.
- OTPs: HMAC digests, not plaintext.
- Remember-me tokens: hashes, not plaintext.
- Backups: Fernet-encrypted archives.
- TFLite model: integrity-verified, not confidential.
- Local SQLite databases: currently plaintext files protected by filesystem permissions; SQLCipher or a managed encrypted database is recommended for production.
- Supabase database and Storage encryption at rest: must be verified in the Supabase project/provider configuration; RLS is authorization, not encryption.

## 5. Configuration, Components, and Network

- Secrets are loaded from environment variables and `.env` is Git-ignored.
- `.env.example` documents required configuration without real secrets.
- VAPID private keys, local databases, backups, uploads, caches, and certificates are Git-ignored.
- A previously tracked plaintext backup was removed from Git tracking and backups are now ignored.
- CSP is enforced through `Content-Security-Policy`.
- Current CSP still permits `unsafe-inline` for compatibility; migrate inline scripts/styles to nonces, hashes, or external files as a future hardening task.
- Rate limits apply to login, prediction, and report submission mutations.
- Dependabot is configured for pip and GitHub Actions.
- `pip-audit` reports no known vulnerabilities.
- Bandit reports no issues.
- Gitleaks is configured in `.github/workflows/security.yml` and must be run in GitHub Actions before release.

Production configuration must include:

```env
FLASK_ENV=production
COOKIE_SECURE=true
FLASK_SECRET_KEY=<random-secret>
SUPABASE_URL=https://<project>.supabase.co
SUPABASE_KEY=<least-privilege-key>
PEST_MODEL_SHA256=<approved-model-sha256>
BACKUP_ENCRYPTION_KEY=<fernet-key>
VAPID_PRIVATE_KEY=<vapid-private-key>
```

Never commit actual values.

## 6. Logging, Backup, and Incident Response

### 6.1 Logging

Audit events include login failures, lockouts, 2FA verification, session events, backup actions, and destructive administrative actions.

Local audit entries contain:

- Timestamp
- User email and role
- Action
- Details
- IP address
- Previous hash
- Entry hash

`verify_audit_log_integrity()` detects altered entries or broken chain predecessors, emits a critical log, and can notify `SECURITY_ALERT_WEBHOOK_URL`.

Operational recommendation: forward logs to an external append-only or SIEM service so an attacker cannot erase both the application and its local audit evidence.

### 6.2 Backups

Database backups are:

1. Serialized as JSON.
2. Compressed with gzip.
3. Encrypted with Fernet.
4. Written as `.json.gz.enc`.
5. Downloadable only through an admin-protected route.

Use a dedicated `BACKUP_ENCRYPTION_KEY`, store it in a secret manager, and test restoration regularly. Existing legacy plaintext backups must be securely deleted or migrated. If a plaintext backup was ever pushed remotely, purge it from history and rotate exposed credentials.

### 6.3 Incident response

On suspected compromise:

1. Disable the affected account/key or deployment.
2. Rotate `FLASK_SECRET_KEY`, Supabase keys, VAPID keys, Brevo keys, webhook secrets, and backup keys as applicable.
3. Revoke active sessions and remember-me tokens.
4. Preserve external logs and verify the audit chain.
5. Check Supabase audit logs, Storage access logs, CI logs, and reverse-proxy logs.
6. Restore only from a verified encrypted backup.
7. Record the incident, affected data, timeline, containment, and corrective actions.

## 7. Standards and Compliance

CocoScan’s controls support:

- OWASP Top 10:2025 awareness and risk treatment.
- ISO/IEC 25010 quality characteristics: security, reliability, maintainability, and functional suitability.
- Data-minimization and purpose-limitation practices for user, location, image, and report data.
- Least privilege through role authorization and restricted service credentials.
- Accountability through audit logging and administrative action records.

Formal compliance requires organizational policies, data-retention decisions, data-subject processes, vendor assessments, a documented threat model, and legal/privacy review. This repository alone cannot establish regulatory compliance.

## 8. Testing and Evidence

### 8.1 Verified automated evidence

Run from the repository root:

```bash
./.venv/bin/pytest -q
./.venv/bin/pip-audit -r requirements.txt
./.venv/bin/bandit -r app model main.py -ll
```

Expected current results:

- `214 passed`
- `No known vulnerabilities found`
- `No issues identified`

Gitleaks runs in GitHub Actions:

1. Push the branch or open a pull request.
2. Open **GitHub → Actions → Security checks**.
3. Confirm the `Scan tracked files for secrets` step succeeds.
4. Save the workflow URL, commit SHA, date, and result as release evidence.

### 8.2 Required production evidence

Before production approval, attach:

- GitHub Actions run URLs for pip-audit, Bandit, and Gitleaks.
- Full pytest output and commit SHA.
- Supabase Storage screenshot/export showing the `reports` bucket is private.
- Supabase RLS policy export for users, reports, chats, visits, and Storage objects.
- Successful signed-URL browser test showing an image loads while an unauthenticated direct object URL returns 401/404.
- Backup creation output and proof that the archive is not a gzip plaintext file.
- Backup restoration test using a non-production environment.
- TLS scan or reverse-proxy configuration proving HTTPS and HSTS.
- Authenticated authorization test matrix for farmer/agriculturist/LGU/admin roles.
- Penetration-test report, test scope, dates, findings, severity, remediation, and retest evidence.

### 8.3 Suggested authenticated penetration tests

Use test accounts and non-production data only:

1. Attempt to access another farmer’s report by changing the report ID.
2. Attempt staff/admin routes using farmer credentials.
3. Replay or tamper with offline capability tokens.
4. Submit state-changing requests without CSRF tokens.
5. Exhaust login, prediction, and upload rate limits.
6. Request an image using a public object URL, then use an authorized signed URL.
7. Test expired signed URLs.
8. Upload malformed, oversized, polyglot, and non-image files.
9. Test stored/reflected XSS in notes, names, chat, and audit-search values.
10. Modify workflow statuses to unauthorized transitions.
11. Test session fixation, logout invalidation, inactivity expiry, and remember-me expiry.
12. Attempt path traversal against backup download/delete routes.

Record each test as: test ID, account/role, request, expected result, actual result, evidence, severity, remediation, and retest result.

## OWASP Top 10:2025 Checklist

Reference: [OWASP Top 10:2025](https://top10.owasp.org/2025/)

| ID | Category | CocoScan status | Evidence / remaining work |
|---|---|---|---|
| A01:2025 | Broken Access Control | **Implemented; verify in pen test** | RBAC, report ownership/assignment checks, workflow authorization, signed private image URLs. Complete authenticated cross-tenant testing. |
| A02:2025 | Security Misconfiguration | **Partially implemented** | Secure headers, enforced CSP, secure cookies, private Storage, ignored secrets, `.env.example`. Verify production TLS, Supabase settings, filesystem permissions, and secret-manager configuration. |
| A03:2025 | Software Supply Chain Failures | **Implemented; continuous** | Pinned dependencies, Dependabot, pip-audit, Bandit, Gitleaks workflow. Review every dependency-update PR and retain scan evidence. |
| A04:2025 | Cryptographic Failures | **Partially implemented** | HTTPS integrations, password/OTP/token hashing, Fernet backups, model digest verification. Local SQLite remains plaintext; verify provider encryption and deploy encrypted disks/SQLCipher. |
| A05:2025 | Injection | **Implemented; verify in pen test** | Validators, bound SQL parameters, Jinja escaping, upload validation. Perform XSS, SQLi, template-injection, and external-URL testing. |
| A06:2025 | Insecure Design | **Implemented with residual review** | Threat-informed offline auth, object authorization, workflow state map, rate limits, backup controls. Maintain threat model and abuse-case review as features change. |
| A07:2025 | Authentication Failures | **Implemented; verify operationally** | Password hashing, lockout, OTP, secure sessions, token expiry, logout cleanup, offline capability scope. Test account recovery, session fixation, and MFA/OTP abuse. |
| A08:2025 | Software or Data Integrity Failures | **Implemented; verify deployment** | TFLite-only model, SHA-256 model verification, encrypted backups, audit hash chain, dependency scans. Protect model digest/key configuration and test restore integrity. |
| A09:2025 | Security Logging and Alerting Failures | **Implemented with deployment work** | Audit logging, hash-chain verification, critical alerts, optional webhook. Configure external log retention, alert routing, dashboards, and response ownership. |
| A10:2025 | Mishandling of Exceptional Conditions | **Partially implemented** | Explicit validation, upload/storage error handling, safe authorization failures, rate-limit responses, and backup-key validation. Test timeouts, dependency outages, malformed responses, disk-full, and restore failures. |

## Release Decision

**Application security baseline:** Ready for controlled staging validation.  
**Production release:** Conditional on:

1. Valid production secrets and encrypted host/database storage.
2. Successful GitHub Actions security workflow, including Gitleaks.
3. Removal or migration of all legacy plaintext backups.
4. Supabase private-bucket and RLS evidence.
5. Authenticated penetration testing and remediation/retest.
6. External monitoring and incident-response ownership.

