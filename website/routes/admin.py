from __future__ import annotations

from flask import flash, jsonify, redirect, render_template, request, session, url_for

from ..repositories.admin import AdminRepository, NotificationRepository, ReportRepository
from ..repositories.recipes import RecipeRepository
from ..repositories.users import UserRepository
from ..security import admin_required
from ..utils import clean_text

USER_STATUSES = {"active", "suspended"}
RECIPE_STATUSES = {"published", "archived", "suspended"}
REPORT_STATUSES = {"pending", "resolved", "dismissed"}
NOTIFICATION_RECEIVERS = {"free", "premium", "all"}


def register_admin_routes(app) -> None:
    @app.route("/adminhome")
    @admin_required
    def adminhome():
        admin = AdminRepository.by_id(int(session["admin_id"]))
        if not admin:
            session.clear()
            return redirect(url_for("login"))
        return render_template(
            "adminhome.html",
            admin_info=admin,
            reports=ReportRepository.all(),
            notifications=NotificationRepository.all(),
        )

    @app.route("/admin/<username>")
    @admin_required
    def get_admin(username: str):
        admin = AdminRepository.by_username(username)
        if not admin:
            return jsonify({"error": "Admin not found"}), 404
        return jsonify(
            {
                "adminID": admin["adminID"],
                "adminName": admin["adminName"],
                "adminEmail": admin["adminEmail"],
                "adminProfilePic": admin["adminProfilePic"],
            }
        )

    @app.route("/manage")
    @admin_required
    def manage():
        return render_template(
            "adminmanage.html",
            users=UserRepository.all(),
            recipes=RecipeRepository.all(),
        )

    @app.route("/user/update_status/<int:user_id>", methods=["POST"])
    @admin_required
    def update_user_status(user_id: int):
        status = clean_text(request.form.get("status"), max_length=20)
        if status not in USER_STATUSES:
            return jsonify({"error": "Invalid user status"}), 400
        if not UserRepository.update_status(user_id, status):
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User status updated", "status": status})

    @app.route("/user/delete/<int:user_id>", methods=["POST"])
    @admin_required
    def delete_user(user_id: int):
        if not UserRepository.delete(user_id):
            return jsonify({"error": "User not found"}), 404
        return jsonify({"message": "User deleted successfully"})

    @app.route("/reports")
    @admin_required
    def reports():
        return render_template("adminreport.html", reports=ReportRepository.all())

    @app.route("/report/<int:report_id>")
    @admin_required
    def get_report_details(report_id: int):
        report = ReportRepository.by_id(report_id)
        if not report:
            return jsonify({"error": "Report not found"}), 404
        return jsonify(dict(report))

    @app.route("/report/update_status/<int:id>", methods=["POST"])
    @admin_required
    def update_report_status(id: int):
        status = clean_text(request.form.get("status"), max_length=20)
        if status not in REPORT_STATUSES:
            return jsonify({"error": "Invalid report status"}), 400
        if not ReportRepository.update_status(id, status):
            return jsonify({"error": "Report not found"}), 404
        return jsonify({"message": "Report status updated", "status": status})

    @app.route("/notifications")
    @admin_required
    def notifications():
        return render_template(
            "adminnoti.html", notifications=NotificationRepository.all()
        )

    @app.route("/notification/<int:id>")
    @admin_required
    def get_notification(id: int):
        notification = NotificationRepository.by_id(id)
        if not notification:
            return jsonify({"error": "Notification not found"}), 404
        return jsonify(
            {
                "id": notification["notiID"],
                "title": notification["notiTitle"],
                "details": notification["notiDetails"],
                "receiver": notification["notiReceiver"],
            }
        )

    @app.route("/notification/create", methods=["POST"])
    @admin_required
    def create_notification():
        title = clean_text(request.form.get("title"), max_length=120)
        details = clean_text(request.form.get("details"), max_length=2000)
        receiver = clean_text(request.form.get("receiver"), max_length=20)
        if not title or not details or receiver not in NOTIFICATION_RECEIVERS:
            flash("Complete all notification fields with valid values.", "error")
        else:
            NotificationRepository.create(title, details, receiver)
            flash("Notification created successfully.", "success")
        return redirect(url_for("notifications"))

    @app.route("/notification/edit/<int:id>", methods=["POST"])
    @admin_required
    def edit_notification(id: int):
        title = clean_text(request.form.get("title"), max_length=120)
        details = clean_text(request.form.get("details"), max_length=2000)
        receiver = clean_text(request.form.get("receiver"), max_length=20)
        if not title or not details or receiver not in NOTIFICATION_RECEIVERS:
            flash("Complete all notification fields with valid values.", "error")
        elif NotificationRepository.update(id, title, details, receiver):
            flash("Notification updated successfully.", "success")
        else:
            flash("Notification not found.", "error")
        return redirect(url_for("notifications"))

    @app.route("/notification/delete/<int:id>", methods=["POST"])
    @admin_required
    def delete_notification(id: int):
        if NotificationRepository.delete(id):
            flash("Notification deleted.", "success")
        else:
            flash("Notification not found.", "error")
        return redirect(url_for("notifications"))
