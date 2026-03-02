import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app, g
from ..db import get_db


def generate_token(user_id: int, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def _extract_user():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None, "Missing or malformed Authorization header"
    token = auth_header.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        return None, "Token expired"
    except jwt.InvalidTokenError:
        return None, "Invalid token"

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (payload["sub"],)).fetchone()
    if not row:
        return None, "User not found"
    return row, None


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user, err = _extract_user()
        if err:
            return jsonify({"error": err}), 401
        g.current_user = user
        return f(*args, **kwargs)
    return wrapper
