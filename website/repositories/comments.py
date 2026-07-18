from __future__ import annotations

from ..database import get_db


class CommentRepository:
    @staticmethod
    def by_id(comment_id: int):
        return get_db().execute(
            "SELECT * FROM comment WHERE commentID = ?", (comment_id,)
        ).fetchone()

    @staticmethod
    def by_recipe(recipe_id: int):
        return get_db().execute(
            """
            SELECT c.commentID, c.commentText, c.commentTime, c.userID, u.userName
            FROM comment c
            JOIN users u ON u.userID = c.userID
            WHERE c.recipeID = ?
            ORDER BY c.commentTime ASC, c.commentID ASC
            """,
            (recipe_id,),
        ).fetchall()

    @staticmethod
    def create(recipe_id: int, user_id: int, text: str) -> int:
        db = get_db()
        cursor = db.execute(
            "INSERT INTO comment (recipeID, userID, commentText) VALUES (?, ?, ?)",
            (recipe_id, user_id, text),
        )
        db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def delete(comment_id: int) -> bool:
        db = get_db()
        cursor = db.execute("DELETE FROM comment WHERE commentID = ?", (comment_id,))
        db.commit()
        return cursor.rowcount == 1


Comment = CommentRepository
