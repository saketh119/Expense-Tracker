#!/usr/bin/env python3
"""
Test runner — no external dependencies needed.
Run from project root: python3 run_tests.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backend.app import create_app
from backend.db import get_db, _hash_password

app = create_app({"TESTING": True, "DATABASE": ":memory:", "SECRET_KEY": "test"})

with app.app_context():
    db = get_db()
    db.execute("DELETE FROM users")
    db.execute("INSERT INTO users (name,email,role,password_hash) VALUES (?,?,?,?)",
               ("Test Employee", "emp@test.com", "employee", _hash_password("pass")))
    db.execute("INSERT INTO users (name,email,role,password_hash) VALUES (?,?,?,?)",
               ("Test Manager", "mgr@test.com", "manager", _hash_password("pass")))
    db.commit()

client = app.test_client()

results = []
failed = []


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    results.append((name, status))
    if not cond:
        failed.append(name)
        print(f"  ✗ FAIL  {name}" + (f" — {detail}" if detail else ""))
    else:
        print(f"  ✓ PASS  {name}")


def get_token(email):
    r = client.post("/auth/login", json={"email": email, "password": "pass"})
    return r.get_json()["token"]


def create_exp(token, **kw):
    return client.post(
        "/expenses/",
        json={"title": "Test", "amount": 100, "category": "travel", **kw},
        headers=auth(token),
    )


print("\n── Auth ─────────────────────────────────────────────────────────────")
r = client.post("/auth/login", json={"email": "emp@test.com", "password": "pass"})
check("login success", r.status_code == 200 and "token" in r.get_json())

check("login wrong password → 401",
      client.post("/auth/login", json={"email": "emp@test.com", "password": "wrong"}).status_code == 401)

check("login missing fields → 400",
      client.post("/auth/login", json={"email": "emp@test.com"}).status_code == 400)

check("GET /auth/me without token → 401", client.get("/auth/me").status_code == 401)

emp_token = get_token("emp@test.com")
mgr_token = get_token("mgr@test.com")

r = client.get("/auth/me", headers=auth(emp_token))
check("GET /auth/me returns correct user",
      r.status_code == 200 and r.get_json()["email"] == "emp@test.com")

print("\n── Expense validation ───────────────────────────────────────────────")
check("create expense → 201 draft",
      create_exp(emp_token).status_code == 201 and create_exp(emp_token).get_json()["status"] == "draft")

check("negative amount → 400", create_exp(emp_token, amount=-10).status_code == 400)
check("zero amount → 400",     create_exp(emp_token, amount=0).status_code == 400)
check("invalid category → 400", create_exp(emp_token, category="unicorn").status_code == 400)
check("missing title → 400",
      client.post("/expenses/", json={"amount": 50, "category": "meals"}, headers=auth(emp_token)).status_code == 400)

print("\n── Approval flow ────────────────────────────────────────────────────")
eid = create_exp(emp_token).get_json()["id"]
r = client.post(f"/expenses/{eid}/submit", headers=auth(emp_token))
check("submit → submitted", r.status_code == 200 and r.get_json()["status"] == "submitted")

r = client.post(f"/expenses/{eid}/approve", json={"note": "Looks good"}, headers=auth(mgr_token))
check("approve → approved", r.status_code == 200 and r.get_json()["status"] == "approved")

r = client.get(f"/expenses/{eid}/history", headers=auth(emp_token))
check("audit trail has 3 entries", len(r.get_json()) == 3)

print("\n── Rejection + reopen flow ──────────────────────────────────────────")
eid2 = create_exp(emp_token).get_json()["id"]
client.post(f"/expenses/{eid2}/submit", headers=auth(emp_token))
r = client.post(f"/expenses/{eid2}/reject", json={"note": "Missing receipt"}, headers=auth(mgr_token))
check("reject → rejected", r.get_json()["status"] == "rejected")

r = client.post(f"/expenses/{eid2}/reopen", headers=auth(emp_token))
check("reopen → draft", r.get_json()["status"] == "draft")

print("\n── Invalid state transitions → 409 ─────────────────────────────────")
eid3 = create_exp(emp_token).get_json()["id"]
check("approve draft → 409",
      client.post(f"/expenses/{eid3}/approve", headers=auth(mgr_token)).status_code == 409)

client.post(f"/expenses/{eid3}/submit", headers=auth(emp_token))
check("double submit → 409",
      client.post(f"/expenses/{eid3}/submit", headers=auth(emp_token)).status_code == 409)

check("reject approved → 409",
      client.post(f"/expenses/{eid}/reject", headers=auth(mgr_token)).status_code == 409)

print("\n── Authorization guards ─────────────────────────────────────────────")
eid4 = create_exp(emp_token).get_json()["id"]
client.post(f"/expenses/{eid4}/submit", headers=auth(emp_token))
check("employee cannot approve → 403",
      client.post(f"/expenses/{eid4}/approve", headers=auth(emp_token)).status_code == 403)

check("employee cannot reject → 403",
      client.post(f"/expenses/{eid4}/reject", headers=auth(emp_token)).status_code == 403)

eid5 = create_exp(emp_token).get_json()["id"]
client.post(f"/expenses/{eid5}/submit", headers=auth(emp_token))
check("edit submitted expense → 409",
      client.patch(f"/expenses/{eid5}", json={"title": "x"}, headers=auth(emp_token)).status_code == 409)

print("\n── Misc ─────────────────────────────────────────────────────────────")
check("expense not found → 404",
      client.get("/expenses/999999", headers=auth(emp_token)).status_code == 404)

check("categories endpoint returns list",
      "categories" in client.get("/expenses/categories").get_json())

# Summary
total = len(results)
passed = sum(1 for _, r in results if r == "PASS")
print(f"\n{'─'*60}")
print(f"  {passed}/{total} tests passed")
if failed:
    print(f"  Failed: {', '.join(failed)}")
    sys.exit(1)
else:
    print("  All tests passed ✓")
