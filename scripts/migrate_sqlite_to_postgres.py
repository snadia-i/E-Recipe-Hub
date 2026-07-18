#!/usr/bin/env python3
"""Copy the included SQLite data into the PostgreSQL database in DATABASE_URL."""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from website.database import POSTGRES_SCHEMA  # noqa: E402

TABLES = [
    ("__users_source__", "users", ["userID", "userName", "userPassword", "userEmail", "userPackage", "userStatus", "userBio", "userProfilePic", "userHeaderPic"]),
    ("admin", "admin", ["adminID", "adminName", "adminPassword", "adminEmail", "adminProfilePic"]),
    ("recipe", "recipe", ["recipeID", "recipeTitle", "recipeDescription", "recipeIngredients", "recipeSteps", "recipePic", "recipeTime", "recipeCalories", "recipeLabel", "recipeCuisine", "recipeStatus", "userID", "createdAt", "updatedAt"]),
    ("collection", "collection", ["collectionID", "collectionName", "userID", "createdAt"]),
    ("collection_recipe", "collection_recipe", ["collectionID", "recipeID", "savedAt"]),
    ("recipe_like", "recipe_like", ["userID", "recipeID", "likedAt"]),
    ("comment", "comment", ["commentID", "commentTime", "commentText", "userID", "recipeID"]),
    ("report", "report", ["reportID", "reportTitle", "reportTime", "reportStatus", "reportDetails", "reportSenderUserID", "reportedUserID", "reportedRecipeID"]),
    ("notification", "notification", ["notiID", "notiTime", "notiTitle", "notiDetails", "notiReceiver"]),
]

DELETE_ORDER = ["collection_recipe", "recipe_like", "comment", "report", "collection", "recipe", "notification", "admin", "users"]
SEQUENCES = {
    "users": "userID", "admin": "adminID", "recipe": "recipeID", "collection": "collectionID",
    "comment": "commentID", "report": "reportID", "notification": "notiID",
}


def split_statements(script: str):
    return [part.strip() for part in script.split(";") if part.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(PROJECT_ROOT / "instance" / "database2.db"))
    parser.add_argument("--reset", action="store_true", help="Delete current PostgreSQL rows first.")
    args = parser.parse_args()

    database_url = (os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("NEON_DATABASE_URL") or "").strip()
    if not database_url:
        raise SystemExit("DATABASE_URL is missing. Run `vercel env pull .env.local` or export it first.")

    source_path = Path(args.source)
    if not source_path.exists():
        raise SystemExit(f"SQLite source not found: {source_path}")

    source = sqlite3.connect(source_path)
    source.row_factory = sqlite3.Row
    target = psycopg.connect(database_url)
    try:
        with target.cursor() as cursor:
            for statement in split_statements(POSTGRES_SCHEMA):
                cursor.execute(statement)
            if args.reset:
                for table in DELETE_ORDER:
                    cursor.execute(f"DELETE FROM {table}")

            for source_table, target_table, columns in TABLES:
                if source_table == "__users_source__":
                    names = {row[0] for row in source.execute("SELECT name FROM sqlite_master WHERE type=\'table\'")}
                    source_table = "users" if "users" in names else "user"
                available = {row[1] for row in source.execute(f'PRAGMA table_info("{source_table}")')}
                selected = [column for column in columns if column in available]
                if not selected:
                    print(f"Skipping {source_table}: table or columns not found")
                    continue
                rows = source.execute(
                    f'SELECT {", ".join(selected)} FROM "{source_table}"'
                ).fetchall()
                if not rows:
                    print(f"{target_table}: 0 rows")
                    continue
                placeholders = ", ".join(["%s"] * len(selected))
                update_columns = [c for c in selected if c.lower() not in {"userid", "adminid", "recipeid", "collectionid", "commentid", "reportid", "notiid"}]
                conflict = " DO NOTHING"
                query = f"INSERT INTO {target_table} ({', '.join(selected)}) VALUES ({placeholders}) ON CONFLICT{conflict}"
                cursor.executemany(query, [tuple(row[column] for column in selected) for row in rows])
                print(f"{target_table}: copied {len(rows)} rows")

            for table, id_column in SEQUENCES.items():
                cursor.execute(
                    f"SELECT setval(pg_get_serial_sequence('{table}', '{id_column.lower()}'), COALESCE((SELECT MAX({id_column}) FROM {table}), 1), true)"
                )
        target.commit()
        print("Migration completed successfully.")
    except Exception:
        target.rollback()
        raise
    finally:
        source.close()
        target.close()


if __name__ == "__main__":
    main()
