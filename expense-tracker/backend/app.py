from flask import Flask, request, make_response
from .db import init_db
from .routes.auth import auth_bp
from .routes.expenses import expenses_bp
import logging
import sys


def create_app(config=None):
    app = Flask(__name__)

    app.config["DATABASE"] = "expenses.db"
    app.config["SECRET_KEY"] = "dev-secret-change-in-prod"
    app.config["JWT_EXPIRY_HOURS"] = 8

    if config:
        app.config.update(config)

    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
        return response

    @app.before_request
    def handle_options():
        if request.method == "OPTIONS":
            resp = make_response()
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, DELETE, OPTIONS"
            return resp

    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(expenses_bp, url_prefix="/expenses")

    with app.app_context():
        init_db(app)

    return app
