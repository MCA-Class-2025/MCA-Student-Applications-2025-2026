# MenoCare Account and Database Options

This decision applies when MenoCare moves beyond session-only demonstration data. Real symptom, bleeding and medication records are sensitive health information. A hosting provider's compliance features do not make the application compliant by themselves; consent, access control, retention, deletion, auditing, incident response and organizational policies remain application-owner responsibilities.

## Recommended development path

For the next account prototype, use **Supabase Auth plus hosted PostgreSQL with Row Level Security (RLS)**. It provides one integrated authentication and relational-data platform and supports per-user database policies. Development must use synthetic records until the appropriate agreement and high-compliance configuration are in place.

For a real healthcare deployment, reassess Supabase against AWS and Azure based on the country, clinical partner, legal obligations, expected scale and available engineering support.

## Options

| Option | Best fit | Advantages | Main limitations |
| --- | --- | --- | --- |
| Supabase Auth + hosted PostgreSQL | Current prototype and controlled pilot | Integrated authentication, relational PostgreSQL, JWTs and database-level RLS; quickest transition from this Python prototype | A healthcare deployment requires the applicable plan, HIPAA add-on and BAA for US PHI; the application owner remains responsible for RLS, keys, consent and other controls |
| Amazon Cognito + Amazon RDS PostgreSQL | Larger production deployment with AWS expertise | Cognito and RDS are listed as HIPAA-eligible services under the AWS shared-responsibility model; strong infrastructure and audit ecosystem | More services, configuration, operational work and cost; application compliance is still the owner's responsibility |
| Microsoft Entra identity + Azure Database for PostgreSQL | Health systems already using Microsoft/Azure | Azure PostgreSQL lists HIPAA/HITECH and HITRUST among its certifications; strong enterprise identity and policy tooling | Higher setup and governance complexity for a small student project |
| Local SQLite | Offline development and automated tests only | Simple, inexpensive and no external account required | Not appropriate for secure multi-user access, remote synchronization or production health records |

Official references:

- [Supabase Auth](https://supabase.com/docs/guides/auth)
- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase HIPAA projects](https://supabase.com/docs/guides/platform/hipaa-projects)
- [AWS HIPAA-eligible services](https://aws.amazon.com/compliance/hipaa-eligible-services-reference/)
- [Azure Database for PostgreSQL compliance](https://learn.microsoft.com/en-us/azure/postgresql/security/security-compliance)

## Proposed Supabase schema

| Table | Purpose |
| --- | --- |
| `profiles` | Minimal account preferences; no password storage because authentication owns credentials |
| `consents` | Versioned consent, privacy-notice acceptance and withdrawal timestamps |
| `check_ins` | Quick symptom and daily-impact entries owned by one authenticated user |
| `events` | Symptom, bleeding and medication-change events owned by one user |
| `user_preferences` | Theme, text size, reduced-motion and default summary settings |
| `audit_events` | Security-relevant account and data operations without copying sensitive note content |
| `deletion_requests` | User-initiated account/data deletion workflow and completion status |

Every user-data table must have RLS enabled so an authenticated user can access only their own rows. Administrative service credentials must never be placed in the browser, repository, screenshots or downloadable reports. Authentication, authorization, consent and deletion behavior require automated negative tests before any real user records are accepted.
