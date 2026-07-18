from __future__ import annotations

import re

from flask import current_app, flash, redirect, render_template, request, session, url_for

from ..database import DatabaseIntegrityError
from ..repositories.admin import AdminRepository
from ..repositories.users import UserRepository
from ..security import csrf_token, hash_password, password_is_hashed, password_matches
from ..utils import clean_text

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


def register_auth_routes(app) -> None:
    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        if request.method == "GET":
            return render_template("login.html", active_tab="signup")

        username = clean_text(request.form.get("username"), max_length=30)
        email = clean_text(request.form.get("email"), max_length=254).lower()
        password = request.form.get("password") or ""

        if not USERNAME_PATTERN.fullmatch(username):
            flash("Username must be 3–30 characters and use only letters, numbers, dots, dashes, or underscores.", "error")
            return render_template("login.html", active_tab="signup"), 400
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            flash("Enter a valid email address.", "error")
            return render_template("login.html", active_tab="signup"), 400
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("login.html", active_tab="signup"), 400
        if UserRepository.by_username(username):
            flash("That username is already taken.", "error")
            return render_template("login.html", active_tab="signup"), 409
        if UserRepository.by_email(email):
            flash("That email address is already registered.", "error")
            return render_template("login.html", active_tab="signup"), 409

        try:
            UserRepository.create(
                username,
                hash_password(password),
                email,
                current_app.config["DEFAULT_PROFILE_IMAGE"],
                current_app.config["DEFAULT_HEADER_IMAGE"],
            )
        except DatabaseIntegrityError:
            flash("Unable to create the account because the username or email already exists.", "error")
            return render_template("login.html", active_tab="signup"), 409

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("login"))

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            return render_template("login.html", active_tab="login")

        username = clean_text(request.form.get("username"), max_length=30)
        password = request.form.get("password") or ""
        user = UserRepository.by_username(username)

        if user and password_matches(user["userPassword"], password):
            if user["userStatus"] == "suspended":
                session.clear()
                return redirect(url_for("suspended_user_page"))

            if not password_is_hashed(user["userPassword"]):
                UserRepository.update_password(user["userID"], hash_password(password))

            session.clear()
            csrf_token()
            session.update(
                user_id=user["userID"],
                user=user["userName"],
                role="user",
                userPackage=user["userPackage"],
            )
            return redirect(url_for("main"))

        admin = AdminRepository.by_username(username)
        if admin and password_matches(admin["adminPassword"], password):
            if not password_is_hashed(admin["adminPassword"]):
                AdminRepository.update_password(admin["adminID"], hash_password(password))

            session.clear()
            csrf_token()
            session.update(
                admin_id=admin["adminID"],
                user=admin["adminName"],
                role="admin",
            )
            return redirect(url_for("adminhome"))

        flash("Invalid username or password.", "error")
        return redirect(url_for("login"))

    @app.route("/logout", methods=["GET", "POST"])
    def logout():
        session.clear()
        flash("You have been logged out.", "info")
        return redirect(url_for("main"))

    @app.route("/suspended_user_page")
    def suspended_user_page():
        return render_template("suspended.html")
