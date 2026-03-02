# ExpenseFlow — Expense Approval System

A small, well-structured expense approval system built for the Better Software engineering assessment.

> **Stack:** Python 3 + Flask · React 18 · SQLite

---

## Quick Start

### Backend

```bash
cd expense-tracker
pip install flask PyJWT   # only 2 dependencies needed
python run.py
# → http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Demo Accounts

| Email            | Password      | Role     |
|------------------|---------------|----------|
| alice@demo.com   | password123   | Employee |
| bob@demo.com     | password123   | Employee |
| carol@demo.com   | password123   | Manager  |

---

## What It Does

Employees create expense reports. Managers approve or reject them.
Every state change is logged in an immutable audit trail.

### State Machine

```
DRAFT ──→ SUBMITTED ──→ APPROVED  (terminal)
              │
              └────────→ REJECTED ──→ DRAFT (reopen)
```

This is the core of the system. Every transition is validated and enforced
in a single function (`expense_service._transition()`). Routes never touch
the status field directly.

---

## Technical Decisions

### 1. No ORM — raw sqlite3

Flask-SQLAlchemy is an excellent library, but it adds a dependency and an
abstraction layer. For a system of this size, raw sqlite3 is more readable:
you can read every query and understand exactly what hits the database.
The schema lives in one `SCHEMA` string in `db.py` — reproducible and auditable.

**Tradeoff:** Adding a PostgreSQL backend in production would require swapping
`sqlite3` for `psycopg2` and adjusting some SQL dialects (e.g. `datetime('now')` → `NOW()`).
This would be isolated to `db.py`.

### 2. Service layer owns all logic

Routes are deliberately thin — they parse HTTP input, call a service function,
and return JSON. All business logic lives in `expense_service.py`.

This means:
- The state machine can be tested without an HTTP client
- New routes can reuse existing service functions
- A new interface (CLI, async worker) would be trivially addable

### 3. `ExpenseError` for domain errors

A custom exception class carries both the message and the HTTP status code.
This avoids repeating `400`/`409`/`403` magic numbers in every route handler
and keeps error logic co-located with the business rule that produces it.

### 4. Explicit state machine dict

```python
VALID_TRANSITIONS = {
    "draft":     ["submitted"],
    "submitted": ["approved", "rejected"],
    "rejected":  ["draft"],
    "approved":  [],
}
```

This is a data structure, not imperative `if/elif` chains. Adding a new status
or transition is a one-line change. The dict is also directly referenced in
`claude.md` to constrain AI code generation.

### 5. SQLite for portability

Chosen so the project runs with `python run.py` and zero external services.
The schema uses `CHECK` constraints to enforce the status enum at the database
level — not just at the application level.

### 6. JWT with role in payload

The JWT payload carries `sub` (user id) and `role`. This avoids a database
lookup on every request to check the user's role. The risk is that if a user's
role changes, existing tokens are stale until they expire (8 hours by default).
Acceptable for this scope; in production you'd use shorter expiry or a token
revocation list.

---

## Project Structure

```
expense-tracker/
├── run.py                      # WSGI entrypoint
├── claude.md                   # AI guidance constraints
├── backend/
│   ├── app.py                  # Flask factory + CORS + seeding
│   ├── db.py                   # Schema, connection management, password hashing
│   ├── routes/
│   │   ├── auth.py             # POST /auth/login, GET /auth/me
│   │   └── expenses.py         # CRUD + state transitions (thin layer)
│   ├── services/
│   │   ├── auth_service.py     # JWT generation + @require_auth decorator
│   │   └── expense_service.py  # All business logic + state machine
│   └── tests/
│       ├── conftest.py         # In-memory DB fixtures
│       ├── test_auth.py        # Auth route tests
│       └── test_expenses.py    # State machine + validation + authz tests
└── frontend/
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx
        └── App.jsx             # Single-file React app
```

---

## API Reference

| Method | Path                        | Auth     | Description              |
|--------|-----------------------------|----------|--------------------------|
| POST   | /auth/login                 | None     | Get JWT token            |
| GET    | /auth/me                    | Any      | Current user info        |
| GET    | /expenses/                  | Any      | List expenses            |
| POST   | /expenses/                  | Employee | Create expense (draft)   |
| GET    | /expenses/:id               | Any      | Get expense detail       |
| PATCH  | /expenses/:id               | Owner    | Edit (draft only)        |
| GET    | /expenses/:id/history       | Any      | Audit trail              |
| POST   | /expenses/:id/submit        | Owner    | Draft → Submitted        |
| POST   | /expenses/:id/approve       | Manager  | Submitted → Approved     |
| POST   | /expenses/:id/reject        | Manager  | Submitted → Rejected     |
| POST   | /expenses/:id/reopen        | Owner    | Rejected → Draft         |

---

## Running Tests

Tests use Flask's built-in test client with an in-memory SQLite database.
No external test runner setup needed.

```bash
python3 run_tests.py
```

Tests cover:
- Valid and invalid authentication
- Full approval lifecycle
- Full rejection + reopen lifecycle  
- Every invalid state transition (409)
- Every authorization guard (403)
- Input validation (400) — bad amount, missing title, invalid category
- 404 handling

---

## Risks and Weaknesses

**Known limitations I'd address in production:**

1. **No pagination** — `GET /expenses/` returns all records. Fine at this scale; add `LIMIT/OFFSET` or cursor pagination before production.

2. **Password hashing is SHA-256** — Simple and dependency-free, but bcrypt or argon2 is the production standard. SHA-256 is fast, which is a liability for password hashing.

3. **In-memory sessions** — JWT tokens are not revocable. A user whose role changes or who is deactivated will retain access until token expiry.

4. **No rate limiting** — The login endpoint has no brute-force protection.

5. **SQLite in production** — SQLite has write concurrency limits. Swap `db.py`'s connection string and dialect for PostgreSQL before deploying.

6. **Frontend is not production-built** — The React app runs in dev mode. Run `npm run build` for a proper production bundle.

---

## Extension Approach

The system is designed to be extended in specific, bounded ways:

**Adding a new expense category:** Add the string to `EXPENSE_CATEGORIES` in `expense_service.py` and `db.py`.

**Adding a new state (e.g. "pending_finance"):** Add it to `VALID_TRANSITIONS` in `expense_service.py`, add a CHECK constraint in the schema, add a route, add tests.

**Adding a new role (e.g. "finance_team"):** Update the authorization table in `claude.md` first, then update role checks in `expense_service.py`.

**Switching to PostgreSQL:** Change `DATABASE` config and replace `sqlite3` with `psycopg2` in `db.py`. Replace `datetime('now')` with `NOW()`. No other files change.

---

## AI Usage

This project was built with Claude (Anthropic). Here's how I used and verified AI-generated code:

- **What AI generated:** Initial boilerplate, function stubs, test cases, README draft
- **What I reviewed carefully:** The state machine logic (`VALID_TRANSITIONS`, `_transition()`), all authorization guards, SQL queries for injection safety
- **What I wrote myself / corrected:** The `db.py` in-memory connection management for testing (AI initially used `Flask-SQLAlchemy` which wasn't available), the `claude.md` constraints file
- **How I verified:** Ran all 18 tests against the actual code; tested every user flow manually through the UI

The `claude.md` file was written to constrain future AI usage — it documents the architecture decisions AI must respect and the patterns it must follow, particularly around the state machine and SQL safety.
