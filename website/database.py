from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from flask import current_app, g

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # Local SQLite-only development can still import the app.
    psycopg = None
    dict_row = None


SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    userID INTEGER PRIMARY KEY AUTOINCREMENT,
    userName TEXT NOT NULL UNIQUE COLLATE NOCASE,
    userPassword TEXT NOT NULL,
    userEmail TEXT NOT NULL UNIQUE COLLATE NOCASE,
    userPackage TEXT NOT NULL DEFAULT 'free' CHECK (userPackage IN ('free', 'premium')),
    userStatus TEXT NOT NULL DEFAULT 'active' CHECK (userStatus IN ('active', 'suspended')),
    userBio TEXT NOT NULL DEFAULT '',
    userProfilePic TEXT,
    userHeaderPic TEXT
);

CREATE TABLE IF NOT EXISTS admin (
    adminID INTEGER PRIMARY KEY AUTOINCREMENT,
    adminName TEXT NOT NULL UNIQUE COLLATE NOCASE,
    adminPassword TEXT NOT NULL,
    adminEmail TEXT NOT NULL UNIQUE COLLATE NOCASE,
    adminProfilePic TEXT
);

CREATE TABLE IF NOT EXISTS recipe (
    recipeID INTEGER PRIMARY KEY AUTOINCREMENT,
    recipeTitle TEXT NOT NULL,
    recipeDescription TEXT NOT NULL,
    recipeIngredients TEXT NOT NULL,
    recipeSteps TEXT NOT NULL,
    recipePic TEXT,
    recipeTime INTEGER NOT NULL CHECK (recipeTime > 0),
    recipeCalories INTEGER NOT NULL CHECK (recipeCalories > 0),
    recipeLabel TEXT NOT NULL,
    recipeCuisine TEXT NOT NULL,
    recipeStatus TEXT NOT NULL DEFAULT 'published'
        CHECK (recipeStatus IN ('published', 'archived', 'suspended')),
    userID INTEGER NOT NULL,
    createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userID) REFERENCES users(userID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS collection (
    collectionID INTEGER PRIMARY KEY AUTOINCREMENT,
    collectionName TEXT NOT NULL,
    userID INTEGER NOT NULL,
    createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (userID, collectionName),
    FOREIGN KEY (userID) REFERENCES users(userID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS collection_recipe (
    collectionID INTEGER NOT NULL,
    recipeID INTEGER NOT NULL,
    savedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collectionID, recipeID),
    FOREIGN KEY (collectionID) REFERENCES collection(collectionID) ON DELETE CASCADE,
    FOREIGN KEY (recipeID) REFERENCES recipe(recipeID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recipe_like (
    userID INTEGER NOT NULL,
    recipeID INTEGER NOT NULL,
    likedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (userID, recipeID),
    FOREIGN KEY (userID) REFERENCES users(userID) ON DELETE CASCADE,
    FOREIGN KEY (recipeID) REFERENCES recipe(recipeID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comment (
    commentID INTEGER PRIMARY KEY AUTOINCREMENT,
    commentTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commentText TEXT NOT NULL CHECK (length(commentText) BETWEEN 1 AND 500),
    userID INTEGER NOT NULL,
    recipeID INTEGER NOT NULL,
    FOREIGN KEY (userID) REFERENCES users(userID) ON DELETE CASCADE,
    FOREIGN KEY (recipeID) REFERENCES recipe(recipeID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report (
    reportID INTEGER PRIMARY KEY AUTOINCREMENT,
    reportTitle TEXT NOT NULL,
    reportTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reportStatus TEXT NOT NULL DEFAULT 'pending'
        CHECK (reportStatus IN ('pending', 'resolved', 'dismissed')),
    reportDetails TEXT NOT NULL,
    reportSenderUserID INTEGER NOT NULL,
    reportedUserID INTEGER NOT NULL,
    reportedRecipeID INTEGER NOT NULL,
    FOREIGN KEY (reportedUserID) REFERENCES users(userID) ON DELETE CASCADE,
    FOREIGN KEY (reportSenderUserID) REFERENCES users(userID) ON DELETE CASCADE,
    FOREIGN KEY (reportedRecipeID) REFERENCES recipe(recipeID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notification (
    notiID INTEGER PRIMARY KEY AUTOINCREMENT,
    notiTime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notiTitle TEXT NOT NULL,
    notiDetails TEXT NOT NULL,
    notiReceiver TEXT NOT NULL CHECK (notiReceiver IN ('free', 'premium', 'all'))
);

CREATE INDEX IF NOT EXISTS idx_recipe_status ON recipe(recipeStatus);
CREATE INDEX IF NOT EXISTS idx_recipe_user ON recipe(userID);
CREATE INDEX IF NOT EXISTS idx_comment_recipe ON comment(recipeID);
CREATE INDEX IF NOT EXISTS idx_report_status ON report(reportStatus);
CREATE INDEX IF NOT EXISTS idx_notification_receiver ON notification(notiReceiver);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    userID SERIAL PRIMARY KEY,
    userName TEXT NOT NULL UNIQUE,
    userPassword TEXT NOT NULL,
    userEmail TEXT NOT NULL UNIQUE,
    userPackage TEXT NOT NULL DEFAULT 'free' CHECK (userPackage IN ('free', 'premium')),
    userStatus TEXT NOT NULL DEFAULT 'active' CHECK (userStatus IN ('active', 'suspended')),
    userBio TEXT NOT NULL DEFAULT '',
    userProfilePic TEXT,
    userHeaderPic TEXT
);

CREATE TABLE IF NOT EXISTS admin (
    adminID SERIAL PRIMARY KEY,
    adminName TEXT NOT NULL UNIQUE,
    adminPassword TEXT NOT NULL,
    adminEmail TEXT NOT NULL UNIQUE,
    adminProfilePic TEXT
);

CREATE TABLE IF NOT EXISTS recipe (
    recipeID SERIAL PRIMARY KEY,
    recipeTitle TEXT NOT NULL,
    recipeDescription TEXT NOT NULL,
    recipeIngredients TEXT NOT NULL,
    recipeSteps TEXT NOT NULL,
    recipePic TEXT,
    recipeTime INTEGER NOT NULL CHECK (recipeTime > 0),
    recipeCalories INTEGER NOT NULL CHECK (recipeCalories > 0),
    recipeLabel TEXT NOT NULL,
    recipeCuisine TEXT NOT NULL,
    recipeStatus TEXT NOT NULL DEFAULT 'published'
        CHECK (recipeStatus IN ('published', 'archived', 'suspended')),
    userID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    createdAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection (
    collectionID SERIAL PRIMARY KEY,
    collectionName TEXT NOT NULL,
    userID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    createdAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (userID, collectionName)
);

CREATE TABLE IF NOT EXISTS collection_recipe (
    collectionID INTEGER NOT NULL REFERENCES collection(collectionID) ON DELETE CASCADE,
    recipeID INTEGER NOT NULL REFERENCES recipe(recipeID) ON DELETE CASCADE,
    savedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collectionID, recipeID)
);

CREATE TABLE IF NOT EXISTS recipe_like (
    userID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    recipeID INTEGER NOT NULL REFERENCES recipe(recipeID) ON DELETE CASCADE,
    likedAt TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (userID, recipeID)
);

CREATE TABLE IF NOT EXISTS comment (
    commentID SERIAL PRIMARY KEY,
    commentTime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commentText TEXT NOT NULL CHECK (length(commentText) BETWEEN 1 AND 500),
    userID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    recipeID INTEGER NOT NULL REFERENCES recipe(recipeID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS report (
    reportID SERIAL PRIMARY KEY,
    reportTitle TEXT NOT NULL,
    reportTime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reportStatus TEXT NOT NULL DEFAULT 'pending'
        CHECK (reportStatus IN ('pending', 'resolved', 'dismissed')),
    reportDetails TEXT NOT NULL,
    reportSenderUserID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    reportedUserID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    reportedRecipeID INTEGER NOT NULL REFERENCES recipe(recipeID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notification (
    notiID SERIAL PRIMARY KEY,
    notiTime TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notiTitle TEXT NOT NULL,
    notiDetails TEXT NOT NULL,
    notiReceiver TEXT NOT NULL CHECK (notiReceiver IN ('free', 'premium', 'all'))
);

CREATE INDEX IF NOT EXISTS idx_recipe_status ON recipe(recipeStatus);
CREATE INDEX IF NOT EXISTS idx_recipe_user ON recipe(userID);
CREATE INDEX IF NOT EXISTS idx_comment_recipe ON comment(recipeID);
CREATE INDEX IF NOT EXISTS idx_report_status ON report(reportStatus);
CREATE INDEX IF NOT EXISTS idx_notification_receiver ON notification(notiReceiver);
"""

_CANONICAL_KEYS = {
    key.lower(): key
    for key in (
        "userID userName userPassword userEmail userPackage userStatus userBio userProfilePic userHeaderPic "
        "adminID adminName adminPassword adminEmail adminProfilePic "
        "recipeID recipeTitle recipeDescription recipeIngredients recipeSteps recipePic recipeTime "
        "recipeCalories recipeLabel recipeCuisine recipeStatus createdAt updatedAt "
        "collectionID collectionName collectionSize collectionPic savedAt "
        "likedAt likeCount commentID commentTime commentText "
        "reportID reportTitle reportTime reportStatus reportDetails reportSenderUserID reportedUserID "
        "reportedRecipeID reportSenderUser reportedUser relatedRecipe "
        "notiID notiTime notiTitle notiDetails notiReceiver count"
    ).split()
}

_ID_COLUMNS = {
    "users": "userID",
    "admin": "adminID",
    "recipe": "recipeID",
    "collection": "collectionID",
    "comment": "commentID",
    "report": "reportID",
    "notification": "notiID",
}


def _normalize_row(row: dict[str, Any] | None):
    if row is None:
        return None
    return {_CANONICAL_KEYS.get(str(key).lower(), key): value for key, value in row.items()}


class PostgresCursorResult:
    def __init__(self, cursor, *, prefetched=None, lastrowid=None):
        self._cursor = cursor
        self._prefetched = prefetched
        self._prefetched_used = False
        self.lastrowid = lastrowid
        self.rowcount = cursor.rowcount

    def fetchone(self):
        if self._prefetched is not None and not self._prefetched_used:
            self._prefetched_used = True
            return _normalize_row(self._prefetched)
        return _normalize_row(self._cursor.fetchone())

    def fetchall(self):
        rows = []
        if self._prefetched is not None and not self._prefetched_used:
            rows.append(_normalize_row(self._prefetched))
            self._prefetched_used = True
        rows.extend(_normalize_row(row) for row in self._cursor.fetchall())
        return rows


class PostgresConnection:
    def __init__(self, database_url: str):
        if psycopg is None:
            raise RuntimeError("PostgreSQL support requires psycopg. Install requirements.txt.")
        self._connection = psycopg.connect(database_url, row_factory=dict_row)

    @staticmethod
    def _translate(query: str) -> str:
        translated = query.replace("?", "%s")
        translated = re.sub(
            r"INSERT\s+OR\s+IGNORE\s+INTO",
            "INSERT INTO",
            translated,
            flags=re.IGNORECASE,
        )
        if re.search(r"INSERT\s+INTO\s+collection_recipe", translated, re.I) and "ON CONFLICT" not in translated.upper():
            translated = translated.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
        return translated

    def execute(self, query: str, parameters: Iterable[Any] | None = None):
        translated = self._translate(query)
        params = tuple(parameters or ())
        insert_match = re.match(r"\s*INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)", translated, re.I)
        id_column = None
        if insert_match and "RETURNING" not in translated.upper():
            table = insert_match.group(1).lower()
            id_column = _ID_COLUMNS.get(table)
            if id_column:
                translated = translated.rstrip().rstrip(";") + f" RETURNING {id_column}"

        cursor = self._connection.cursor()
        cursor.execute(translated, params)
        prefetched = None
        lastrowid = None
        if id_column:
            prefetched = cursor.fetchone()
            if prefetched:
                lastrowid = next(iter(prefetched.values()))
        return PostgresCursorResult(cursor, prefetched=prefetched, lastrowid=lastrowid)

    def commit(self):
        self._connection.commit()

    def rollback(self):
        self._connection.rollback()

    def close(self):
        self._connection.close()


if psycopg is not None:
    DatabaseIntegrityError = (sqlite3.IntegrityError, psycopg.IntegrityError)
else:
    DatabaseIntegrityError = sqlite3.IntegrityError


def _sqlite_connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA journal_mode = WAL")
    return connection


def using_postgres() -> bool:
    return bool(current_app.config.get("DATABASE_URL"))


def get_db():
    if "db" not in g:
        database_url = current_app.config.get("DATABASE_URL", "")
        if database_url:
            g.db = PostgresConnection(database_url)
        else:
            g.db = _sqlite_connect(Path(current_app.config["DATABASE_PATH"]))
    return g.db


def close_db(_error=None) -> None:
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def _sqlite_table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (table_name,)
    ).fetchone() is not None


def _sqlite_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    if not _sqlite_table_exists(connection, table_name):
        return set()
    return {row["name"] for row in connection.execute(f'PRAGMA table_info("{table_name}")')}


def _migrate_sqlite_user_table(connection: sqlite3.Connection) -> None:
    if _sqlite_table_exists(connection, "user") and not _sqlite_table_exists(connection, "users"):
        connection.execute('ALTER TABLE "user" RENAME TO users')


def _migrate_legacy_collection(connection: sqlite3.Connection) -> None:
    columns = _sqlite_columns(connection, "collection")
    if "recipeID" not in columns:
        return
    connection.execute("ALTER TABLE collection RENAME TO collection_legacy")
    connection.executescript(
        """
        CREATE TABLE collection (
            collectionID INTEGER PRIMARY KEY AUTOINCREMENT,
            collectionName TEXT NOT NULL,
            userID INTEGER NOT NULL,
            createdAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (userID, collectionName),
            FOREIGN KEY (userID) REFERENCES users(userID) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS collection_recipe (
            collectionID INTEGER NOT NULL,
            recipeID INTEGER NOT NULL,
            savedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (collectionID, recipeID),
            FOREIGN KEY (collectionID) REFERENCES collection(collectionID) ON DELETE CASCADE,
            FOREIGN KEY (recipeID) REFERENCES recipe(recipeID) ON DELETE CASCADE
        );
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO collection (collectionID, collectionName, userID)
        SELECT collectionID, MAX(collectionName), MAX(userID)
        FROM collection_legacy GROUP BY collectionID
        """
    )
    connection.execute(
        """
        INSERT OR IGNORE INTO collection_recipe (collectionID, recipeID)
        SELECT collectionID, recipeID FROM collection_legacy WHERE recipeID IS NOT NULL
        """
    )
    connection.execute("DROP TABLE collection_legacy")


def _ensure_sqlite_legacy_columns(connection: sqlite3.Connection) -> None:
    report_columns = _sqlite_columns(connection, "report")
    if report_columns and "reportTitle" not in report_columns:
        connection.execute("ALTER TABLE report ADD COLUMN reportTitle TEXT NOT NULL DEFAULT 'Recipe report'")

    recipe_columns = _sqlite_columns(connection, "recipe")
    if recipe_columns and "createdAt" not in recipe_columns:
        connection.execute("ALTER TABLE recipe ADD COLUMN createdAt TIMESTAMP")
        connection.execute("UPDATE recipe SET createdAt = CURRENT_TIMESTAMP WHERE createdAt IS NULL")
    recipe_columns = _sqlite_columns(connection, "recipe")
    if recipe_columns and "updatedAt" not in recipe_columns:
        connection.execute("ALTER TABLE recipe ADD COLUMN updatedAt TIMESTAMP")
        connection.execute("UPDATE recipe SET updatedAt = CURRENT_TIMESTAMP WHERE updatedAt IS NULL")

    collection_columns = _sqlite_columns(connection, "collection")
    if collection_columns and "createdAt" not in collection_columns:
        connection.execute("ALTER TABLE collection ADD COLUMN createdAt TIMESTAMP")
        connection.execute("UPDATE collection SET createdAt = CURRENT_TIMESTAMP WHERE createdAt IS NULL")


def _migrate_legacy_likes(connection: sqlite3.Connection) -> None:
    if _sqlite_table_exists(connection, "like"):
        connection.execute(
            'INSERT OR IGNORE INTO recipe_like (userID, recipeID) SELECT userID, recipeID FROM "like"'
        )


def _split_statements(script: str):
    return [statement.strip() for statement in script.split(";") if statement.strip()]


def init_database() -> None:
    database_url = current_app.config.get("DATABASE_URL", "")
    if database_url:
        connection = PostgresConnection(database_url)
        try:
            for statement in _split_statements(POSTGRES_SCHEMA):
                connection.execute(statement)
            connection.commit()
        finally:
            connection.close()
        return

    database_path = Path(current_app.config["DATABASE_PATH"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = _sqlite_connect(database_path)
    try:
        _migrate_sqlite_user_table(connection)
        _migrate_legacy_collection(connection)
        connection.executescript(SQLITE_SCHEMA)
        _ensure_sqlite_legacy_columns(connection)
        _migrate_legacy_likes(connection)
        connection.commit()
    finally:
        connection.close()


def init_app(app) -> None:
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_database()
