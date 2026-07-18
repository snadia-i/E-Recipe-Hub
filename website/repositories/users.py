from __future__ import annotations

from ..database import get_db


class UserRepository:
    @staticmethod
    def all():
        return get_db().execute("SELECT * FROM users ORDER BY LOWER(userName)").fetchall()

    @staticmethod
    def by_id(user_id: int):
        return get_db().execute("SELECT * FROM users WHERE userID = ?", (user_id,)).fetchone()

    @staticmethod
    def by_username(username: str):
        return get_db().execute(
            "SELECT * FROM users WHERE LOWER(userName) = LOWER(?)", (username,)
        ).fetchone()

    @staticmethod
    def by_email(email: str):
        return get_db().execute(
            "SELECT * FROM users WHERE LOWER(userEmail) = LOWER(?)", (email,)
        ).fetchone()

    @staticmethod
    def create(
        username: str,
        password_hash: str,
        email: str,
        profile_picture: str,
        header_picture: str,
    ) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO users (
                userName, userPassword, userEmail, userPackage, userStatus,
                userBio, userProfilePic, userHeaderPic
            ) VALUES (?, ?, ?, 'free', 'active', '', ?, ?)
            """,
            (username, password_hash, email, profile_picture, header_picture),
        )
        db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def update_profile(
        user_id: int,
        username: str,
        email: str,
        bio: str,
        profile_picture: str,
        header_picture: str,
    ) -> bool:
        db = get_db()
        cursor = db.execute(
            """
            UPDATE users
            SET userName = ?, userEmail = ?, userBio = ?,
                userProfilePic = ?, userHeaderPic = ?
            WHERE userID = ?
            """,
            (username, email, bio, profile_picture, header_picture, user_id),
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def update_password(user_id: int, password_hash: str) -> bool:
        db = get_db()
        cursor = db.execute(
            "UPDATE users SET userPassword = ? WHERE userID = ?", (password_hash, user_id)
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def update_status(user_id: int, status: str) -> bool:
        db = get_db()
        cursor = db.execute(
            "UPDATE users SET userStatus = ? WHERE userID = ?", (status, user_id)
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def delete(user_id: int) -> bool:
        db = get_db()
        cursor = db.execute("DELETE FROM users WHERE userID = ?", (user_id,))
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def recipes(user_id: int):
        return get_db().execute(
            "SELECT * FROM recipe WHERE userID = ? ORDER BY createdAt DESC, recipeID DESC",
            (user_id,),
        ).fetchall()


# Compatibility alias for older imports.
RegisteredUser = UserRepository
