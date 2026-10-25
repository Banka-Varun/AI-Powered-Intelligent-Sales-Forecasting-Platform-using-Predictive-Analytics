Prepared 25 October 2026.

Command: `python -m pytest -q`

Result: 18 passed in 0.85 seconds, with one upstream Starlette warning about its HTTPX test-client integration being deprecated. The warning did not fail any test.

Environment: Python 3.12, FastAPI 0.162.0, Pydantic 2.14.1, SQLAlchemy 2.1.6, pytest 9.1.1, HTTPX 0.28.1. See requirements files for compatible version ranges; installed versions on another machine can differ.

Verified using isolated, temporary SQLite databases:

- Health endpoint and complete create/read/update/delete workflow.
- Email normalization and case-insensitive duplicate handling.
- Duplicate updates roll back other field changes.
- Invalid email, blank name, unknown stage and unknown field rejection.
- Empty/null update rejection and optional-phone clearing.
- Search, literal wildcard handling, pagination and limits.
- Mixed valid/invalid/duplicate CSV rows, repeat imports and row reporting.
- Malformed headers, invalid encoding, empty file data and column count errors.
- File size and row limits without partial writes.
- Persisted records surviving an application restart.

Not verified: the user's PostgreSQL service/password/schema, execution on Windows, real frontend integration, concurrency under load, authentication/authorization, AI scoring or team-repository integration. Do not describe those as tested or complete. Run the README demonstration against local PostgreSQL before evaluation.
