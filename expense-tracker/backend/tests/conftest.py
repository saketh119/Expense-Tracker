import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from backend.app import create_app
from backend.db import get_db, _hash_password


@pytest.fixture(scope="session")
def app():
    app = create_app({
        "TESTING": True,
        "DATABASE": ":memory:",
        "SECRET_KEY": "test-secret",
    })
    # Seed test users (seeding already happens in init_db but we need predictable state)
    with app.app_context():
        db = get_db()
        # Remove auto-seeded users and add test users  
        db.execute("DELETE FROM users")
        db.execute("INSERT INTO users (name, email, role, password_hash) VALUES (?, ?, ?, ?)",
                   ("Test Employee", "emp@test.com", "employee", _hash_password("pass")))
        db.execute("INSERT INTO users (name, email, role, password_hash) VALUES (?, ?, ?, ?)",
                   ("Test Manager", "mgr@test.com", "manager", _hash_password("pass")))
        db.commit()
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def emp_token(client):
    r = client.post("/auth/login", json={"email": "emp@test.com", "password": "pass"})
    return r.get_json()["token"]


@pytest.fixture
def mgr_token(client):
    r = client.post("/auth/login", json={"email": "mgr@test.com", "password": "pass"})
    return r.get_json()["token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}
