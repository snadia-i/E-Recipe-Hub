from __future__ import annotations


from flask import flash, jsonify, redirect, render_template, request, session, url_for

from ..database import DatabaseIntegrityError
from ..repositories.admin import NotificationRepository
from ..repositories.recipes import RecipeRepository
from ..repositories.users import UserRepository
from ..security import admin_required, hash_password, login_required, password_matches
from ..serializers import recipe_dict
from ..utils import clean_text, save_image


def register_user_routes(app) -> None:
    @app.route("/profile")
    @login_required
    def profile():
        user = UserRepository.by_id(int(session["user_id"]))
        if not user:
            session.clear()
            flash("Your account could not be found.", "error")
            return redirect(url_for("login"))

        recipes = RecipeRepository.by_user(user["userID"])
        notifications = NotificationRepository.all(user["userPackage"])
        return render_template(
            "profile.html", user=user, recipes=recipes, notifications=notifications
        )

    @app.route("/profile/edit_profile", methods=["POST"])
    @login_required
    def edit_profile():
        user = UserRepository.by_id(int(session["user_id"]))
        if not user:
            return redirect(url_for("login"))

        username = clean_text(request.form.get("userName"), max_length=30)
        email = clean_text(request.form.get("userEmail"), max_length=254).lower()
        bio = clean_text(request.form.get("userBio"), max_length=500)

        if len(username) < 3:
            flash("Username must contain at least 3 characters.", "error")
            return redirect(url_for("profile"))
        if "@" not in email:
            flash("Enter a valid email address.", "error")
            return redirect(url_for("profile"))

        username_owner = UserRepository.by_username(username)
        if username_owner and username_owner["userID"] != user["userID"]:
            flash("That username is already in use.", "error")
            return redirect(url_for("profile"))
        email_owner = UserRepository.by_email(email)
        if email_owner and email_owner["userID"] != user["userID"]:
            flash("That email address is already in use.", "error")
            return redirect(url_for("profile"))

        profile_picture = user["userProfilePic"]
        header_picture = user["userHeaderPic"]
        try:
            profile_picture = save_image(request.files.get("userProfilePic")) or profile_picture
            header_picture = save_image(request.files.get("userHeaderPic")) or header_picture
        except ValueError as error:
            flash(str(error), "error")
            return redirect(url_for("profile"))

        try:
            updated = UserRepository.update_profile(
                user["userID"],
                username,
                email,
                bio,
                profile_picture,
                header_picture,
            )
        except DatabaseIntegrityError:
            updated = False

        if updated:
            session["user"] = username
            flash("Profile updated successfully.", "success")
        else:
            flash("Profile update failed.", "error")
        return redirect(url_for("profile"))

    @app.route("/profile/change_password", methods=["POST"])
    @login_required
    def change_password():
        user = UserRepository.by_id(int(session["user_id"]))
        current_password = request.form.get("currentPassword") or ""
        new_password = request.form.get("newPassword") or ""
        confirm_password = request.form.get("confirmPassword") or ""

        if not user or not password_matches(user["userPassword"], current_password):
            flash("The current password is incorrect.", "error")
        elif len(new_password) < 8:
            flash("The new password must be at least 8 characters long.", "error")
        elif new_password == current_password:
            flash("The new password must be different from the current password.", "error")
        elif new_password != confirm_password:
            flash("The new passwords do not match.", "error")
        elif UserRepository.update_password(user["userID"], hash_password(new_password)):
            flash("Password changed successfully.", "success")
        else:
            flash("Password change failed.", "error")

        return redirect(url_for("profile"))

    @app.route("/user/<int:id>")
    @admin_required
    def get_user(id: int):
        user = UserRepository.by_id(id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(
            {
                "userID": user["userID"],
                "userName": user["userName"],
                "userEmail": user["userEmail"],
                "userBio": user["userBio"],
                "userPackage": user["userPackage"],
                "userHeaderPic": user["userHeaderPic"],
                "userProfilePic": user["userProfilePic"],
                "userStatus": user["userStatus"],
            }
        )

    @app.route("/user/username/<string:username>")
    @admin_required
    def get_user_by_username(username: str):
        user = UserRepository.by_username(username)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(
            {
                "userID": user["userID"],
                "userName": user["userName"],
                "userEmail": user["userEmail"],
                "userBio": user["userBio"],
                "userPackage": user["userPackage"],
                "userHeaderPic": user["userHeaderPic"],
                "userProfilePic": user["userProfilePic"],
                "userStatus": user["userStatus"],
            }
        )

    @app.route("/user/<int:id>/recipes")
    @admin_required
    def get_user_recipes(id: int):
        return jsonify({"recipes": [recipe_dict(row) for row in RecipeRepository.by_user(id)]})
