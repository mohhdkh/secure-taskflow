# Security policy

## Supported version

Security fixes are applied to the latest commit on `main`.

## Reporting a vulnerability

Please do not open a public issue for a suspected vulnerability. Contact the maintainer through the LinkedIn address in the repository README and include:

- the affected endpoint or component;
- a minimal reproduction using synthetic data;
- the expected security boundary and observed behavior;
- any suggested mitigation.

Do not test against systems or accounts you do not own or have explicit permission to assess.

## Demonstrated controls

- Argon2 password hashing;
- expiring JWT authentication;
- database-backed current-user resolution;
- server-side owner scoping for reads and mutations;
- indistinguishable `404` responses for inaccessible task records;
- PostgreSQL-backed authorization tests in CI;
- no production credentials or customer data in the repository.
