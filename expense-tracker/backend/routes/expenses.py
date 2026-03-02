from flask import Blueprint, request, jsonify, g
from ..services.auth_service import require_auth
from ..services import expense_service
from ..services.expense_service import ExpenseError, EXPENSE_CATEGORIES

expenses_bp = Blueprint("expenses", __name__)


def _get_or_404(expense_id):
    expense = expense_service.get_expense_by_id(expense_id)
    if not expense:
        return None, (jsonify({"error": "Expense not found"}), 404)
    return expense, None


@expenses_bp.get("/categories")
def categories():
    return jsonify({"categories": EXPENSE_CATEGORIES})


@expenses_bp.get("/")
@require_auth
def list_expenses():
    return jsonify(expense_service.get_expenses_for_user(g.current_user))


@expenses_bp.post("/")
@require_auth
def create():
    try:
        expense = expense_service.create_expense(g.current_user, request.get_json(silent=True) or {})
    except ExpenseError as e:
        return jsonify({"error": str(e)}), e.status
    return jsonify(expense), 201


@expenses_bp.get("/<int:expense_id>")
@require_auth
def get_expense(expense_id):
    expense, err = _get_or_404(expense_id)
    if err: return err
    return jsonify(expense)


@expenses_bp.patch("/<int:expense_id>")
@require_auth
def update(expense_id):
    expense, err = _get_or_404(expense_id)
    if err: return err
    try:
        updated = expense_service.update_expense(expense, g.current_user, request.get_json(silent=True) or {})
    except ExpenseError as e:
        return jsonify({"error": str(e)}), e.status
    return jsonify(updated)


@expenses_bp.get("/<int:expense_id>/history")
@require_auth
def history(expense_id):
    expense, err = _get_or_404(expense_id)
    if err: return err
    return jsonify(expense_service.get_history(expense_id))


@expenses_bp.post("/<int:expense_id>/submit")
@require_auth
def submit(expense_id):
    expense, err = _get_or_404(expense_id)
    if err: return err
    try:
        return jsonify(expense_service.submit_expense(expense, g.current_user))
    except ExpenseError as e:
        return jsonify({"error": str(e)}), e.status


@expenses_bp.post("/<int:expense_id>/approve")
@require_auth
def approve(expense_id):
    expense, err = _get_or_404(expense_id)
    if err: return err
    note = (request.get_json(silent=True) or {}).get("note", "")
    try:
        return jsonify(expense_service.approve_expense(expense, g.current_user, note))
    except ExpenseError as e:
        return jsonify({"error": str(e)}), e.status


@expenses_bp.post("/<int:expense_id>/reject")
@require_auth
def reject(expense_id):
    expense, err = _get_or_404(expense_id)
    if err: return err
    note = (request.get_json(silent=True) or {}).get("note", "")
    try:
        return jsonify(expense_service.reject_expense(expense, g.current_user, note))
    except ExpenseError as e:
        return jsonify({"error": str(e)}), e.status


@expenses_bp.post("/<int:expense_id>/reopen")
@require_auth
def reopen(expense_id):
    expense, err = _get_or_404(expense_id)
    if err: return err
    try:
        return jsonify(expense_service.reopen_expense(expense, g.current_user))
    except ExpenseError as e:
        return jsonify({"error": str(e)}), e.status
