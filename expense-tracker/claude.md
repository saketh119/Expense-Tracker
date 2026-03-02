# claude.md — AI Agent Guidance for ExpenseFlow

This file constrains AI code generation for this project.
Read it before writing any code. Deviate only with explicit human approval.

---

## 1. Architecture Boundaries

The codebase has three distinct layers. Never collapse them.

```
Routes   → validate HTTP input, call service, return JSON
Service  → own all business rules and state machine
DB layer → SQL only, no logic
```

**Never put business logic in routes.**
**Never put SQL in services.**
The `expense_service.py` module is the single source of truth for what is allowed.

---

## 2. State Machine — Do Not Bypass

All expense status transitions flow through `expense_service._transition()`.
This function is the only place a status change should occur.

```
VALID_TRANSITIONS = {
  "draft":     ["submitted"],
  "submitted": ["approved", "rejected"],
  "rejected":  ["draft"],
  "approved":  [],   # terminal — no transitions out
}
```

When adding a new transition:
1. Add it to `VALID_TRANSITIONS` first
2. Write a test for it
3. Add the route last

Never directly `UPDATE expenses SET status = ...` outside of `_transition()`.

---

## 3. Validation Rules

All validation lives in `expense_service.py`. New validators must:
- Raise `ExpenseError` (not generic exceptions)
- Include a descriptive message
- Be unit-tested for both valid and invalid inputs

Validation checklist for expenses:
- `title`: non-empty string, max 200 chars
- `amount`: numeric, > 0, ≤ 1,000,000, rounded to 2 decimal places
- `category`: must be in `EXPENSE_CATEGORIES`
- `status`: only changed via `_transition()`, never via PATCH

---

## 4. Authorization Rules

Every endpoint that modifies state must check both authentication AND authorization.

| Action   | Who can perform it               |
|----------|----------------------------------|
| Create   | Any authenticated user           |
| Edit     | Owner only, and only if draft    |
| Submit   | Owner only                       |
| Approve  | Manager role only                |
| Reject   | Manager role only                |
| Reopen   | Owner only, and only if rejected |
| View all | Manager sees all; employee sees own |

If a new role is added in the future, update this table first, then update code.

---

## 5. Audit Trail

Every status change MUST call `_record_history()`.
This is non-negotiable — the audit trail is a core feature, not optional.
If you add a new transition, verify a history record is created in tests.

---

## 6. Error Handling Patterns

Use `ExpenseError` for all domain errors:
```python
raise ExpenseError("message here", status=409)
```

Routes must catch `ExpenseError` and return:
```python
return jsonify({"error": str(e)}), e.status
```

Never let unhandled exceptions reach the client. Use `app.logger` to log unexpected errors.

---

## 7. Testing Requirements

Every new feature must include tests covering:
1. Happy path
2. Invalid inputs (expected failures)
3. Invalid state transitions
4. Authorization guards (wrong role, wrong owner)

Tests live in `backend/tests/`. Run via `python3 run_tests.py`.

Do not ship code without tests. Do not delete tests to make them pass.

---

## 8. Database

- Schema is defined in `backend/db.py` → `SCHEMA`
- All schema changes go there, using `CREATE TABLE IF NOT EXISTS`
- Foreign keys are enforced (`PRAGMA foreign_keys = ON`)
- Direct SQL in `db.py` layer only — use parameterized queries always

**Never use string formatting to build SQL queries.** Use `?` placeholders.

---

## 9. Frontend Constraints

- `API_BASE` is `http://localhost:5000` — configurable via `.env`
- All API calls go through the `apiFetch()` helper in `App.jsx`
- Token stored in `sessionStorage` — never `localStorage`
- No direct `fetch()` calls outside of `apiFetch()`
- All errors must be surfaced to the user, never swallowed silently

---

## 10. What AI Should NOT Do

- Do not add features not in the spec without being asked
- Do not refactor working code unless fixing a bug
- Do not add dependencies without checking they're available offline
- Do not write clever code — prefer readable over clever
- Do not use `eval`, dynamic SQL construction, or `exec`
- Do not add `print()` debugging statements to committed code
