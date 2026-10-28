# Measured engineering evidence

This file records reproducible results rather than estimated performance claims.

## Local verification — 28 October 2026

| Check | Result | Environment |
|---|---:|---|
| Backend/API suite | 28 passed in 6.41 seconds | Python 3.12, isolated local test database |
| Frontend component suite | 1 passed in 4.60 seconds | Vitest + jsdom |
| Production frontend build | Passed in 1.24 seconds; 147.63 kB JavaScript, 48.01 kB gzip | Vite production build |

The local duration is a development-machine observation, not a production latency guarantee.

## CI verification

Every push to `main` and every pull request runs:

1. all backend authentication, ownership and CRUD tests against a real PostgreSQL 16 service;
2. the Arabic React component test;
3. a TypeScript check and production Vite build;
4. JUnit report publication as a downloadable workflow artifact.

The repository badge links directly to the latest workflow result. Individual pull requests retain their own checks, discussion and merge history.

## Tested usage scenarios

- successful and failed login;
- rejected short, whitespace-only and unexpected login fields;
- anonymous access rejection;
- malformed, expired and invalid-subject token rejection;
- non-Bearer authentication rejection;
- deleted-account token rejection;
- corrupted password-hash fail-closed behavior;
- owner-scoped task listing;
- cross-user update denial;
- cross-user deletion denial;
- administrator override;
- invalid enum, length and server-owned input rejection;
- missing-resource update and deletion behavior;
- rejected updates leave persisted task data unchanged;
- complete task create, list, update and delete workflow;
- Arabic login-to-dashboard rendering.
