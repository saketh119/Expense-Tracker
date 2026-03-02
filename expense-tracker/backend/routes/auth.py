from flask import Blueprint, request, jsonify, g
from ..db import get_db, check_password
from ..services.auth_service import generate_token, require_auth

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if not user or not check_password(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(user["id"], user["role"])
    return jsonify({
        "token": token,
        "user": {"id": user["id"], "name": user["name"], "email": user["email"], "role": user["role"]},
    })


@auth_bp.get("/me")
@require_auth
def me():
    u = g.current_user
    return jsonify({"id": u["id"], "name": u["name"], "email": u["email"], "role": u["role"]})
