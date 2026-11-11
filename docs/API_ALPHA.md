# Alpha API contract

The frontend and API use the same origin. Requests and responses use JSON except
for HTML/static pages, download headers, and 204 responses. Existing `/api`
addresses remain stable. The shared frontend request helper sends the session
cookie and `X-CSRF-Token`; all POST, PATCH, PUT and DELETE requests require a
valid token obtained from `GET /api/auth/csrf`.

| Method and path | Contract | Access / success |
|---|---|---|
| GET /api/auth/csrf | Obtain CSRF token | Public / 200 |
| POST /api/auth/register | email, password; no role field | Public, throttled / 201 |
| POST /api/auth/login | email, password; rotates browser session | Public, throttled / 200 |
| POST /api/auth/logout | Revoke current server session | Signed in / 204 |
| GET /api/me | user_id, email, role, permit_id only | Owner / 200 |
| PATCH /api/me/permit | Integer permit_id referencing an existing permit | Owner / 200 |
| GET /api/me/export | Own account and classes; attachment JSON | Owner / 200 |
| DELETE /api/me | Current password; live account, classes and sessions deleted | Student owner / 204 |
| GET /api/permits, /api/buildings | Available catalog choices | Signed in / 200 |
| GET /api/classes | Signed-in user's classes | Owner / 200 |
| POST /api/classes | title, weekday 0-6, HH:MM start/end, building_id | Owner / 201 |
| PATCH /api/classes/{id} | Known changed fields only; valid full result required | Owner / 200 |
| DELETE /api/classes/{id} | Remove an owned class | Owner / 204 |
| GET /api/classes/next | Next weekly occurrence | Signed in / 200 |
| GET /api/recommendations | Class, best lot, up to two alternatives, reason and provisional flag | Signed in / 200 |
| GET /api/admin/lots | Lot records and accepted permit IDs | Admin / 200 |
| PATCH /api/admin/lots/{id} | available_spaces and/or status | Admin / 200 |
| PUT /api/admin/lots/{id}/permits | Replace permit_ids list atomically | Admin / 200 |
| GET /api/admin/history | At most 50 newest changes with actor ID and timestamp | Admin / 200 |
| GET /api/health | Database connectivity only | Public / 200 |

Errors use `{"error":{"code":400,"message":"..."}}`. Codes: 400 invalid
input, 401 unauthenticated/expired session or wrong password, 403 role/CSRF
failure, 404 missing or unowned class, 409 duplicate signup, 413 oversized body,
429 authentication limit with Retry-After, and 500/503 generic database errors.
Database exception parameters and password hashes never appear in API output.

Example: POST /api/classes with
`{"title":"Database Systems","weekday":2,"start_time":"10:00","end_time":"11:00","building_id":1}`
creates the record under the session's user, never a caller-supplied owner ID.
The client refreshes the schedule and recommendation after success. A class
response is returned from the transaction context; commit must succeed first.

SQLAlchemy parameterizes values. `validators.py` checks class shape and domain
constraints; `services.py` ranks eligible lots independently of UI markup.
`http.py` standardizes the JSON boundary. No CORS access is enabled. Responses
for all API paths use Cache-Control: no-store. Audit responses are bounded;
schedule/catalog lists are appropriate for a small alpha but are not paginated.

## Schema evolution

0001 created seven core tables. 0002 added lot_update. 0003 adds auth_session
(SHA-256 token digest, owner FK with cascade deletion, expiry) and auth_limit
(HMAC identifier, attempt count, window expiry). Both new expiry columns are
indexed. No plaintext passwords, raw session tokens, attempted emails, or IP
addresses are added to these tables. `alembic_version` records the revision.
SQLite foreign keys and existing uniqueness/check constraints remain enabled.

Lot status/count changes and permit-rule changes each commit with their audit
row in the same transaction. A status-only update preserves the count timestamp.
Account deletion cascades to classes and sessions. Administrator deletion is
blocked in this UI to preserve references in lot history.
