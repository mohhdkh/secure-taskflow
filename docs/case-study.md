# Technical case study

## Problem

Small teams often track operational work in chat messages or spreadsheets. Ownership becomes unclear, status updates are inconsistent and there is no reliable permission boundary between a team member and an administrator.

## Engineering decision

Secure TaskFlow uses a deliberately small three-tier design:

1. A responsive Arabic RTL React client owns presentation and optimistic interaction.
2. FastAPI owns authentication, authorization and task business rules.
3. PostgreSQL owns relational integrity and durable state.

The API never trusts the UI to enforce ownership. Every read and mutation resolves the authenticated user and scopes the database operation on the server.

## Alternatives considered

| Alternative | Why it was not selected |
|---|---|
| Browser-only local storage | Fast to prototype, but provides no shared state or server-side access control |
| Firebase-only implementation | Productive for real-time use cases, but less explicit for demonstrating relational ownership rules |
| A single server-rendered application | Valid choice, but a separate API better demonstrates web/mobile client reuse |

## Quality strategy

- Backend integration tests cover health, authentication failure, expired and malformed tokens, corrupted stored credentials, invalid payloads, authorization boundaries, missing resources and the full task CRUD workflow.
- CI runs those tests against a real PostgreSQL 16 service, not only SQLite.
- The frontend component test mocks the HTTP boundary and verifies the Arabic login-to-dashboard flow.
- The production frontend build is part of the required GitHub Actions quality gate.

## Result

The repository is a compact, reviewable example of the same engineering habits used in larger systems: server-enforced permissions, typed boundaries, automated testing, reproducible containers and clear operational documentation.

