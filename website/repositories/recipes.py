from __future__ import annotations

from ..database import get_db


RECIPE_COLUMNS = """
    r.recipeID, r.recipeTitle, r.recipeDescription, r.recipeIngredients,
    r.recipeSteps, r.recipePic, r.recipeTime, r.recipeCalories,
    r.recipeLabel, r.recipeCuisine, r.recipeStatus, r.userID,
    r.createdAt, r.updatedAt
"""

LIKE_COUNT = "(SELECT COUNT(*) FROM recipe_like rl WHERE rl.recipeID = r.recipeID) AS likeCount"


class RecipeRepository:
    @staticmethod
    def all():
        return get_db().execute(
            f"""
            SELECT {RECIPE_COLUMNS}, u.userName, {LIKE_COUNT}
            FROM recipe r
            JOIN users u ON u.userID = r.userID
            ORDER BY r.recipeID ASC
            """
        ).fetchall()

    @staticmethod
    def published():
        return get_db().execute(
            f"""
            SELECT {RECIPE_COLUMNS}, u.userName, {LIKE_COUNT}
            FROM recipe r
            JOIN users u ON u.userID = r.userID
            WHERE r.recipeStatus = 'published'
            ORDER BY r.recipeID ASC
            """
        ).fetchall()

    @staticmethod
    def by_id(recipe_id: int):
        return get_db().execute(
            f"""
            SELECT {RECIPE_COLUMNS}, u.userName, {LIKE_COUNT}
            FROM recipe r
            JOIN users u ON u.userID = r.userID
            WHERE r.recipeID = ?
            """,
            (recipe_id,),
        ).fetchone()

    @staticmethod
    def by_user(user_id: int):
        return get_db().execute(
            f"""
            SELECT {RECIPE_COLUMNS}, {LIKE_COUNT}
            FROM recipe r
            WHERE r.userID = ?
            ORDER BY r.recipeID ASC
            """,
            (user_id,),
        ).fetchall()

    @staticmethod
    def create(title, description, ingredients, steps, image_url, preparation_time,
               calories, label, cuisine, status, user_id: int) -> int:
        db = get_db()
        cursor = db.execute(
            """
            INSERT INTO recipe (
                recipeTitle, recipeDescription, recipeIngredients, recipeSteps,
                recipePic, recipeTime, recipeCalories, recipeLabel,
                recipeCuisine, recipeStatus, userID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, description, ingredients, steps, image_url, preparation_time,
             calories, label, cuisine, status, user_id),
        )
        db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def update(recipe_id, title, description, ingredients, steps, preparation_time,
               calories, cuisine, label, image_url) -> bool:
        db = get_db()
        cursor = db.execute(
            """
            UPDATE recipe
            SET recipeTitle = ?, recipeDescription = ?, recipeIngredients = ?,
                recipeSteps = ?, recipeTime = ?, recipeCalories = ?,
                recipeCuisine = ?, recipeLabel = ?,
                recipePic = COALESCE(?, recipePic), updatedAt = CURRENT_TIMESTAMP
            WHERE recipeID = ?
            """,
            (title, description, ingredients, steps, preparation_time, calories,
             cuisine, label, image_url, recipe_id),
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def delete(recipe_id: int) -> bool:
        db = get_db()
        cursor = db.execute("DELETE FROM recipe WHERE recipeID = ?", (recipe_id,))
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def update_status(recipe_id: int, status: str) -> bool:
        db = get_db()
        cursor = db.execute(
            "UPDATE recipe SET recipeStatus = ?, updatedAt = CURRENT_TIMESTAMP WHERE recipeID = ?",
            (status, recipe_id),
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def is_liked(recipe_id: int, user_id: int) -> bool:
        return get_db().execute(
            "SELECT 1 FROM recipe_like WHERE recipeID = ? AND userID = ?",
            (recipe_id, user_id),
        ).fetchone() is not None

    @staticmethod
    def toggle_like(recipe_id: int, user_id: int) -> tuple[bool, int]:
        db = get_db()
        existing = db.execute(
            "SELECT 1 FROM recipe_like WHERE recipeID = ? AND userID = ?",
            (recipe_id, user_id),
        ).fetchone()
        liked = existing is None
        if liked:
            db.execute("INSERT INTO recipe_like (recipeID, userID) VALUES (?, ?)", (recipe_id, user_id))
        else:
            db.execute("DELETE FROM recipe_like WHERE recipeID = ? AND userID = ?", (recipe_id, user_id))
        count = db.execute(
            "SELECT COUNT(*) AS count FROM recipe_like WHERE recipeID = ?", (recipe_id,)
        ).fetchone()["count"]
        db.commit()
        return liked, int(count)

    @staticmethod
    def like_count(recipe_id: int) -> int:
        row = get_db().execute(
            "SELECT COUNT(*) AS count FROM recipe_like WHERE recipeID = ?", (recipe_id,)
        ).fetchone()
        return int(row["count"])

    @staticmethod
    def search(query: str):
        term = f"%{query.lower()}%"
        return get_db().execute(
            f"""
            SELECT {RECIPE_COLUMNS}, {LIKE_COUNT}
            FROM recipe r
            WHERE r.recipeStatus = 'published'
              AND (LOWER(r.recipeTitle) LIKE ? OR LOWER(r.recipeDescription) LIKE ?
                   OR LOWER(r.recipeIngredients) LIKE ? OR LOWER(r.recipeCuisine) LIKE ?)
            ORDER BY r.createdAt DESC, r.recipeID DESC
            """,
            (term, term, term, term),
        ).fetchall()

    @staticmethod
    def filter(cuisines: list[str], labels: list[str]):
        conditions = ["r.recipeStatus = 'published'"]
        parameters: list[str] = []
        if cuisines:
            placeholders = ",".join("?" for _ in cuisines)
            conditions.append(f"LOWER(r.recipeCuisine) IN ({placeholders})")
            parameters.extend(item.lower() for item in cuisines)
        if labels:
            placeholders = ",".join("?" for _ in labels)
            conditions.append(f"LOWER(r.recipeLabel) IN ({placeholders})")
            parameters.extend(item.lower() for item in labels)
        return get_db().execute(
            f"""
            SELECT {RECIPE_COLUMNS}, {LIKE_COUNT}
            FROM recipe r
            WHERE {' AND '.join(conditions)}
            ORDER BY r.createdAt DESC, r.recipeID DESC
            """,
            parameters,
        ).fetchall()

    @staticmethod
    def sort(sort_by: str, order: str):
        columns = {"title": "LOWER(r.recipeTitle)", "time": "r.recipeTime", "calories": "r.recipeCalories"}
        direction = "DESC" if order.lower() == "desc" else "ASC"
        return get_db().execute(
            f"""
            SELECT {RECIPE_COLUMNS}, {LIKE_COUNT}
            FROM recipe r
            WHERE r.recipeStatus = 'published'
            ORDER BY {columns[sort_by]} {direction}, r.recipeID DESC
            """
        ).fetchall()


Recipe = RecipeRepository
