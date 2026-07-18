from __future__ import annotations

from flask import current_app

from ..database import get_db


class CollectionRepository:
    @staticmethod
    def by_user(user_id: int):
        default_image = current_app.config["DEFAULT_RECIPE_IMAGE"]
        return get_db().execute(
            """
            SELECT c.collectionID, c.collectionName,
                   COUNT(cr.recipeID) AS collectionSize,
                   COALESCE(MIN(r.recipePic), ?) AS collectionPic
            FROM collection c
            LEFT JOIN collection_recipe cr ON cr.collectionID = c.collectionID
            LEFT JOIN recipe r ON r.recipeID = cr.recipeID
            WHERE c.userID = ?
            GROUP BY c.collectionID, c.collectionName
            ORDER BY c.createdAt DESC, c.collectionID DESC
            """,
            (default_image, user_id),
        ).fetchall()

    @staticmethod
    def by_id(collection_id: int):
        return get_db().execute(
            "SELECT * FROM collection WHERE collectionID = ?", (collection_id,)
        ).fetchone()

    @staticmethod
    def belongs_to(collection_id: int, user_id: int) -> bool:
        row = get_db().execute(
            "SELECT 1 FROM collection WHERE collectionID = ? AND userID = ?",
            (collection_id, user_id),
        ).fetchone()
        return row is not None

    @staticmethod
    def create(user_id: int, name: str) -> int:
        db = get_db()
        cursor = db.execute(
            "INSERT INTO collection (collectionName, userID) VALUES (?, ?)",
            (name, user_id),
        )
        db.commit()
        return int(cursor.lastrowid)

    @staticmethod
    def delete(collection_id: int, user_id: int) -> bool:
        db = get_db()
        cursor = db.execute(
            "DELETE FROM collection WHERE collectionID = ? AND userID = ?",
            (collection_id, user_id),
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def recipes(collection_id: int, user_id: int):
        return get_db().execute(
            """
            SELECT r.recipeID, r.recipeTitle, r.recipeDescription, r.recipePic,
                   r.recipeTime, r.recipeCalories, r.recipeCuisine, r.recipeLabel
            FROM collection c
            JOIN collection_recipe cr ON cr.collectionID = c.collectionID
            JOIN recipe r ON r.recipeID = cr.recipeID
            WHERE c.collectionID = ? AND c.userID = ?
            ORDER BY cr.savedAt DESC
            """,
            (collection_id, user_id),
        ).fetchall()

    @staticmethod
    def add_recipe(collection_id: int, recipe_id: int, user_id: int) -> bool:
        if not CollectionRepository.belongs_to(collection_id, user_id):
            return False
        db = get_db()
        cursor = db.execute(
            "INSERT OR IGNORE INTO collection_recipe (collectionID, recipeID) VALUES (?, ?)",
            (collection_id, recipe_id),
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def remove_recipe(collection_id: int, recipe_id: int, user_id: int) -> bool:
        if not CollectionRepository.belongs_to(collection_id, user_id):
            return False
        db = get_db()
        cursor = db.execute(
            "DELETE FROM collection_recipe WHERE collectionID = ? AND recipeID = ?",
            (collection_id, recipe_id),
        )
        db.commit()
        return cursor.rowcount == 1

    @staticmethod
    def is_saved_by_user(recipe_id: int, user_id: int) -> bool:
        row = get_db().execute(
            """
            SELECT 1
            FROM collection_recipe cr
            JOIN collection c ON c.collectionID = cr.collectionID
            WHERE cr.recipeID = ? AND c.userID = ?
            LIMIT 1
            """,
            (recipe_id, user_id),
        ).fetchone()
        return row is not None

    @staticmethod
    def contains_recipe(collection_id: int, recipe_id: int) -> bool:
        row = get_db().execute(
            "SELECT 1 FROM collection_recipe WHERE collectionID = ? AND recipeID = ?",
            (collection_id, recipe_id),
        ).fetchone()
        return row is not None


Collection = CollectionRepository
