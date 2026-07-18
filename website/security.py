from __future__ import annotations

import hmac
import secrets
from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import abort, flash, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

F = TypeVar("F", bound=Callable[..., Any])


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def password_matches(stored_password: str, supplied_password: str) -> bool:
    """Support current password hashes and upgrade-friendly legacy plaintext."""
    if not stored_password:
        return False

    if stored_password.startswith(("scrypt:", "pbkdf2:", "argon2:")):
        try:
            return check_password_hash(stored_password, supplied_password)
        except ValueError:
            return False

    return hmac.compare_digest(stored_password, supplied_password)


def password_is_hashed(stored_password: str) -> bool:
    return stored_password.startswith(("scrypt:", "pbkdf2:", "argon2:"))


def csrf_token() -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf() -> None:
    if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
        return

    supplied = (
        request.headers.get("X-CSRFToken")
        or request.form.get("_csrf_token")
        or ((request.get_json(silent=True) or {}).get("csrf_token"))
    )
    expected = session.get("_csrf_token")

    if not supplied or not expected or not hmac.compare_digest(supplied, expected):
        abort(400, description="Invalid or missing CSRF token.")


def _json_request() -> bool:
    return request.is_json or "application/json" in request.headers.get("Accept", "")


def login_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not session.get("user_id") or session.get("role") != "user":
            if _json_request():
                return jsonify({"error": "Authentication required"}), 401
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return cast(F, wrapped)


def admin_required(view: F) -> F:
    @wraps(view)
    def wrapped(*args: Any, **kwargs: Any):
        if not session.get("admin_id") or session.get("role") != "admin":
            if _json_request():
                return jsonify({"error": "Administrator access required"}), 403
            flash("Administrator access is required.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return cast(F, wrapped)
