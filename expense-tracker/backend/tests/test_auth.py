from .conftest import auth


def test_login_success(client):
    r = client.post("/auth/login", json={"email": "emp@test.com", "password": "pass"})
    assert r.status_code == 200
    data = r.get_json()
    assert "token" in data
    assert data["user"]["role"] == "employee"


def test_login_wrong_password(client):
    assert client.post("/auth/login", json={"email": "emp@test.com", "password": "wrong"}).status_code == 401


def test_login_missing_fields(client):
    assert client.post("/auth/login", json={"email": "emp@test.com"}).status_code == 400


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401


def test_me_returns_user(client, emp_token):
    r = client.get("/auth/me", headers=auth(emp_token))
    assert r.status_code == 200
    assert r.get_json()["email"] == "emp@test.com"
