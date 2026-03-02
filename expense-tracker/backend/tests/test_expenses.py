from .conftest import auth


def create_expense(client, token, **kwargs):
    payload = {"title": "Test expense", "amount": 100.0, "category": "travel", **kwargs}
    return client.post("/expenses/", json=payload, headers=auth(token))


# --- Creation & validation ---

def test_create_expense(client, emp_token):
    r = create_expense(client, emp_token)
    assert r.status_code == 201
    data = r.get_json()
    assert data["status"] == "draft"
    assert data["amount"] == 100.0


def test_create_missing_title(client, emp_token):
    r = client.post("/expenses/", json={"amount": 50, "category": "meals"}, headers=auth(emp_token))
    assert r.status_code == 400
    assert "title" in r.get_json()["error"]


def test_create_invalid_amount(client, emp_token):
    assert create_expense(client, emp_token, amount=-10).status_code == 400


def test_create_zero_amount(client, emp_token):
    assert create_expense(client, emp_token, amount=0).status_code == 400


def test_create_invalid_category(client, emp_token):
    assert create_expense(client, emp_token, category="unicorn").status_code == 400


# --- State machine: happy paths ---

def test_full_approval_flow(client, emp_token, mgr_token):
    expense_id = create_expense(client, emp_token).get_json()["id"]

    r = client.post(f"/expenses/{expense_id}/submit", headers=auth(emp_token))
    assert r.status_code == 200
    assert r.get_json()["status"] == "submitted"

    r = client.post(f"/expenses/{expense_id}/approve", json={"note": "Looks good"}, headers=auth(mgr_token))
    assert r.status_code == 200
    assert r.get_json()["status"] == "approved"

    r = client.get(f"/expenses/{expense_id}/history", headers=auth(emp_token))
    assert len(r.get_json()) == 3  # created, submitted, approved


def test_rejection_and_reopen(client, emp_token, mgr_token):
    expense_id = create_expense(client, emp_token).get_json()["id"]
    client.post(f"/expenses/{expense_id}/submit", headers=auth(emp_token))
    r = client.post(f"/expenses/{expense_id}/reject", json={"note": "Missing receipt"}, headers=auth(mgr_token))
    assert r.get_json()["status"] == "rejected"
    r = client.post(f"/expenses/{expense_id}/reopen", headers=auth(emp_token))
    assert r.get_json()["status"] == "draft"


# --- Invalid transitions ---

def test_cannot_approve_draft(client, emp_token, mgr_token):
    expense_id = create_expense(client, emp_token).get_json()["id"]
    assert client.post(f"/expenses/{expense_id}/approve", headers=auth(mgr_token)).status_code == 409


def test_cannot_double_submit(client, emp_token):
    expense_id = create_expense(client, emp_token).get_json()["id"]
    client.post(f"/expenses/{expense_id}/submit", headers=auth(emp_token))
    assert client.post(f"/expenses/{expense_id}/submit", headers=auth(emp_token)).status_code == 409


def test_approved_is_terminal(client, emp_token, mgr_token):
    expense_id = create_expense(client, emp_token).get_json()["id"]
    client.post(f"/expenses/{expense_id}/submit", headers=auth(emp_token))
    client.post(f"/expenses/{expense_id}/approve", headers=auth(mgr_token))
    assert client.post(f"/expenses/{expense_id}/reject", headers=auth(mgr_token)).status_code == 409


# --- Authorization guards ---

def test_employee_cannot_approve(client, emp_token):
    expense_id = create_expense(client, emp_token).get_json()["id"]
    client.post(f"/expenses/{expense_id}/submit", headers=auth(emp_token))
    assert client.post(f"/expenses/{expense_id}/approve", headers=auth(emp_token)).status_code == 403


def test_cannot_edit_submitted(client, emp_token):
    expense_id = create_expense(client, emp_token).get_json()["id"]
    client.post(f"/expenses/{expense_id}/submit", headers=auth(emp_token))
    assert client.patch(f"/expenses/{expense_id}", json={"title": "Changed"}, headers=auth(emp_token)).status_code == 409


def test_expense_not_found(client, emp_token):
    assert client.get("/expenses/999999", headers=auth(emp_token)).status_code == 404
