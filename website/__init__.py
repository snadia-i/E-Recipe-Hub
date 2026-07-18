from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for

from .config import Config, database_path
from .database import init_app as init_database_app
from .repositories.users import UserRepository
from .routes import register_routes
from .security import csrf_token, validate_csrf


def create_app(test_config: dict | None = None) -> Flask:
    project_root = Path(__file__).resolve().parent.parent
    public_static = project_root / "public" / "static"
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder=str(public_static),
        static_url_path="/static",
    )
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    if app.config.get("IS_VERCEL") and not app.config.get("DATABASE_URL"):
        raise RuntimeError(
            "DATABASE_URL is required on Vercel. Connect Neon or Supabase before deploying."
        )

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    if not app.config.get("DATABASE_PATH"):
        app.config["DATABASE_PATH"] = str(
            database_path(app.instance_path, app.config["DATABASE_NAME"])
        )
    if not app.config.get("UPLOAD_FOLDER"):
        app.config["UPLOAD_FOLDER"] = str(public_static / "uploads")
    if not app.config.get("IS_VERCEL"):
        Path(app.config["UPLOAD_FOLDER"]).mkdir(parents=True, exist_ok=True)

    init_database_app(app)
    app.jinja_env.globals["csrf_token"] = csrf_token

    @app.before_request
    def protect_requests_and_check_account():
        validate_csrf()
        if request.endpoint == "static":
            return None

        if session.get("role") == "user" and session.get("user_id"):
            user = UserRepository.by_id(int(session["user_id"]))
            if not user:
                session.clear()
                return redirect(url_for("login"))
            if user["userStatus"] == "suspended":
                session.clear()
                return redirect(url_for("suspended_user_page"))
            session["user"] = user["userName"]
            session["userPackage"] = user["userPackage"]
        return None

    register_routes(app)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "database": "postgres" if app.config.get("DATABASE_URL") else "sqlite"})

    @app.errorhandler(400)
    def bad_request(error):
        if request.is_json or request.accept_mimetypes.best == "application/json":
            return jsonify({"error": getattr(error, "description", "Bad request")}), 400
        return render_template("400.html", message=getattr(error, "description", None)), 400

    @app.errorhandler(404)
    def not_found(_error):
        if request.is_json or request.accept_mimetypes.best == "application/json":
            return jsonify({"error": "Resource not found"}), 404
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def file_too_large(_error):
        if request.is_json:
            return jsonify({"error": "Uploaded file is too large"}), 413
        return render_template("400.html", message="Uploaded files must be 4 MB or smaller."), 413

    return app
