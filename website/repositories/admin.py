from __future__ import annotations

from ..database import get_db


class AdminRepository:
    @staticmethod
    def by_username(username: str):
        return get_db().execute(
            "SELECT * FROM admin WHERE LOWER(adminName) = LOWER(?)", (username,)
        ).fetchone()

    @staticmethod
    def by_id(admin_id: int):
        return get_db().execute(
            "SELECT * FROM admin WHERE adminID = ?", (admin_id,)
        ).fetchone()

    @staticmethod
    def create(username: str, password_hash: str, email: str, profile_picture: str) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO admin (adminName, adminPassword, adminEmail, adminProfilePic)
            VALUES (?, ?, ?, ?)
            """,
            (username, password_hash, email, profile_picture),
        )
        db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def update_password(admin_id: int, password_hash: str) -> bool:
        db = get_db()
        cursor = db.execute(
            "UPDATE admin SET adminPassword = ? WHERE adminID = ?",
            (password_hash, admin_id),
        )
        db.commit()
        return cursor.rowcount == 1


class ReportRepository:
    @staticmethod
    def all():
        return get_db().execute(
            """
            SELECT r.*, sender.userName AS reportSenderUser,
                   reported.userName AS reportedUser
            FROM report r
            JOIN users sender ON sender.userID = r.reportSenderUserID
            JOIN users reported ON reported.userID = r.reportedUserID
            ORDER BY CASE r.reportStatus
                WHEN 'pending' THEN 1
                WHEN 'resolved' THEN 2
                WHEN 'dismissed' THEN 3
                ELSE 4 END,
                r.reportTime DESC
            """
        ).fetchall()

    @staticmethod
    def by_id(report_id: int):
        return get_db().execute(
            """
            SELECT r.reportID, r.reportTitle, r.reportDetails, r.reportTime,
                   r.reportStatus, r.reportSenderUserID, r.reportedUserID,
                   r.reportedRecipeID AS relatedRecipe,
                   sender.userName AS reportSenderUser,
                   reported.userName AS reportedUser
            FROM report r
            JOIN users sender ON sender.userID = r.reportSenderUserID
            JOIN users reported ON reported.userID = r.reportedUserID
            WHERE r.reportID = ?
            """,
            (report_id,),
        ).fetchone()

    @staticmethod
    def create(
        title: str, details: str, sender_id: int, reported_user_id: int, recipe_id: int
    ) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO report (
                reportTitle, reportDetails, reportStatus,
                reportSenderUserID, reportedUserID, reportedRecipeID
            ) VALUES (?, ?, 'pending', ?, ?, ?)
            """,
            (title, details, sender_id, reported_user_id, recipe_id),
        )
        db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def update_status(report_id: int, status: str) -> bool:
        db = get_db()
        cursor = db.execute(
            "UPDATE report SET reportStatus = ? WHERE reportID = ?", (status, report_id)
        )
        db.commit()
        return cursor.rowcount == 1


class NotificationRepository:
    @staticmethod
    def all(receiver: str | None = None):
        if receiver:
            return get_db().execute(
                """
                SELECT * FROM notification
                WHERE notiReceiver IN (?, 'all')
                ORDER BY notiTime DESC, notiID DESC
                """,
                (receiver,),
            ).fetchall()
        return get_db().execute(
            "SELECT * FROM notification ORDER BY notiTime DESC, notiID DESC"
        ).fetchall()

    @staticmethod
    def by_id(notification_id: int):
        return get_db().execute(
            "SELECT * FROM notification WHERE notiID = ?", (notification_id,)
        ).fetchone()

    @staticmethod
    def create(title: str, details: str, receiver: str) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO notification (notiTitle, notiDetails, notiReceiver)
            VALUES (?, ?, ?)
            """,
            (title, details, receiver),
        )
        db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def update(notification_id: int, title: str, details: str, receiver: str) -> bool:
        db = get_db()
        cursor = db.execute(
            """
            UPDATE notification
            SET notiTitle = ?, notiDetails = ?, notiReceiver = ?
            WHERE notiID = ?
            """,
            (title, details, receiver, notification_id),
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def delete(notification_id: int) -> bool:
        db = get_db()
        cursor = db.execute(
            "DELETE FROM notification WHERE notiID = ?", (notification_id,)
        )
        db.commit()
        return cursor.rowcount == 1


Admin = AdminRepository
Report = ReportRepository
Notification = NotificationRepository
