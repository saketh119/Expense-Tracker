"""
All expense business logic is centralised here.
Routes are thin; this module owns correctness and state transitions.
"""
from flask import current_app, g
from ..db import get_db

EXPENSE_CATEGORIES = ["travel", "meals", "software", "equipment", "training", "other"]

# Valid transitions: {from_status: [allowed_to_statuses]}
VALID_TRANSITIONS = {
    "draft":     ["submitted"],
    "submitted": ["approved", "rejected"],
    "rejected":  ["draft"],
    "approved":  [],   # terminal
}


class ExpenseError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _parse_amount(raw):
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ExpenseError("amount must be a valid number")
    if value <= 0:
        raise ExpenseError("amount must be greater than 0")
    if value > 1_000_000:
        raise ExpenseError("amount exceeds maximum allowed value")
    return round(value, 2)


def _validate_category(cat: str) -> str:
    if cat not in EXPENSE_CATEGORIES:
        raise ExpenseError(f"category must be one of: {', '.join(EXPENSE_CATEGORIES)}")
    return cat


def _validate_title(title) -> str:
    title = (title or "").strip()
    if not title:
        raise ExpenseError("title is required")
    if len(title) > 200:
        raise ExpenseError("title must be 200 characters or fewer")
    return title


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_expense(user, data: dict) -> dict:
    db = get_db()
    title    = _validate_title(data.get("title"))
    amount   = _parse_amount(data.get("amount"))
    category = _validate_category(data.get("category", ""))
    desc     = (data.get("description") or "").strip()

    cur = db.execute(
        """INSERT INTO expenses (user_id, title, amount, category, description, status)
           VALUES (?, ?, ?, ?, ?, 'draft')""",
        (user["id"], title, amount, category, desc),
    )
    expense_id = cur.lastrowid
    _record_history(db, expense_id, None, "draft", user["id"], "Created")
    db.commit()
    current_app.logger.info("Expense %s created by user %s", expense_id, user["id"])
    return _get_expense(db, expense_id)


def update_expense(expense: dict, actor, data: dict) -> dict:
    if expense["status"] != "draft":
        raise ExpenseError("Only draft expenses can be edited", 409)
    if expense["user_id"] != actor["id"]:
        raise ExpenseError("You can only edit your own expenses", 403)

    db = get_db()
    fields, params = [], []

    if "title" in data:
        fields.append("title = ?"); params.append(_validate_title(data["title"]))
    if "amount" in data:
        fields.append("amount = ?"); params.append(_parse_amount(data["amount"]))
    if "category" in data:
        fields.append("category = ?"); params.append(_validate_category(data["category"]))
    if "description" in data:
        fields.append("description = ?"); params.append(data["description"].strip())

    if fields:
        fields.append("updated_at = datetime('now')")
        params.append(expense["id"])
        db.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?", params)
        db.commit()

    return _get_expense(db, expense["id"])


def get_expenses_for_user(user) -> list:
    db = get_db()
    if user["role"] == "manager":
        rows = db.execute(
            """SELECT e.*, u.name as owner_name FROM expenses e
               JOIN users u ON u.id = e.user_id
               ORDER BY e.created_at DESC"""
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT e.*, u.name as owner_name FROM expenses e
               JOIN users u ON u.id = e.user_id
               WHERE e.user_id = ?
               ORDER BY e.created_at DESC""",
            (user["id"],),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


# ---------------------------------------------------------------------------
# State transitions
# ---------------------------------------------------------------------------

def _transition(expense: dict, new_status: str, actor, note: str = "") -> dict:
    current_status = expense["status"]
    if new_status not in VALID_TRANSITIONS.get(current_status, []):
        raise ExpenseError(
            f"Cannot move expense from '{current_status}' to '{new_status}'", 409
        )
    db = get_db()
    db.execute(
        "UPDATE expenses SET status = ?, updated_at = datetime('now') WHERE id = ?",
        (new_status, expense["id"]),
    )
    _record_history(db, expense["id"], current_status, new_status, actor["id"], note)
    db.commit()
    current_app.logger.info(
        "Expense %s: %s → %s by user %s", expense["id"], current_status, new_status, actor["id"]
    )
    return _get_expense(db, expense["id"])


def submit_expense(expense: dict, actor) -> dict:
    if expense["user_id"] != actor["id"]:
        raise ExpenseError("You can only submit your own expenses", 403)
    return _transition(expense, "submitted", actor)


def approve_expense(expense: dict, actor, note: str = "") -> dict:
    if actor["role"] != "manager":
        raise ExpenseError("Only managers can approve expenses", 403)
    return _transition(expense, "approved", actor, note)


def reject_expense(expense: dict, actor, note: str = "") -> dict:
    if actor["role"] != "manager":
        raise ExpenseError("Only managers can reject expenses", 403)
    return _transition(expense, "rejected", actor, note)


def reopen_expense(expense: dict, actor) -> dict:
    if expense["user_id"] != actor["id"]:
        raise ExpenseError("You can only reopen your own expenses", 403)
    return _transition(expense, "draft", actor, "Reopened for revision")


def get_history(expense_id: int) -> list:
    db = get_db()
    rows = db.execute(
        """SELECT h.*, u.name as changer_name FROM expense_status_history h
           JOIN users u ON u.id = h.changed_by_id
           WHERE h.expense_id = ?
           ORDER BY h.timestamp ASC""",
        (expense_id,),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "from_status": r["from_status"],
            "to_status": r["to_status"],
            "changed_by": r["changer_name"],
            "note": r["note"],
            "timestamp": r["timestamp"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def get_expense_by_id(expense_id: int):
    db = get_db()
    return _get_expense(db, expense_id)


def _get_expense(db, expense_id: int):
    row = db.execute(
        """SELECT e.*, u.name as owner_name FROM expenses e
           JOIN users u ON u.id = e.user_id
           WHERE e.id = ?""",
        (expense_id,),
    ).fetchone()
    return _row_to_dict(row) if row else None


def _row_to_dict(row) -> dict:
    d = dict(row)
    d["amount"] = float(d["amount"])
    return d


def _record_history(db, expense_id, from_status, to_status, changed_by_id, note):
    db.execute(
        """INSERT INTO expense_status_history
           (expense_id, from_status, to_status, changed_by_id, note)
           VALUES (?, ?, ?, ?, ?)""",
        (expense_id, from_status, to_status, changed_by_id, note),
    )
