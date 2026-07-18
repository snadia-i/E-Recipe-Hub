from __future__ import annotations

import pytest

from website import create_app
from website.database import get_db
from website.repositories.admin import AdminRepository
from website.repositories.users import UserRepository
from website.security import hash_password


@pytest.fixture()
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_PATH": str(tmp_path / "test.db"),
            "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        }
    )
    with application.app_context():
        UserRepository.create(
            "alice",
            hash_password("Password123!"),
            "alice@example.com",
            "/static/images/mingyu.jpg",
            "/static/images/view.jpg",
        )
        AdminRepository.create(
            "admin1",
            hash_password("Admin123!"),
            "admin@example.com",
            "/static/images/mingyu.jpg",
        )
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


def csrf(client) -> str:
    with client.session_transaction() as session:
        return session["_csrf_token"]


def login(client, username: str, password: str):
    client.get("/login")
    return client.post(
        "/login",
        data={"_csrf_token": csrf(client), "username": username, "password": password},
    )


def test_user_can_create_recipe_without_upload(client, app):
    assert login(client, "alice", "Password123!").status_code == 302
    response = client.post(
        "/createrecipe",
        data={
            "_csrf_token": csrf(client),
            "title": "Simple Rice",
            "description": "A basic rice recipe.",
            "ingredients": "Rice\nWater",
            "steps": "Wash rice.\nCook rice.",
            "time": "25",
            "calories": "210",
            "cuisines": "asian",
            "labels": "dinner",
        },
        follow_redirects=False,
    )
    assert response.status_code == 302
    with app.app_context():
        recipe = get_db().execute(
            "SELECT * FROM recipe WHERE recipeTitle = 'Simple Rice'"
        ).fetchone()
        assert recipe is not None
        assert recipe["recipePic"].endswith("AyamGorengBerempah-1260.jpg")


def test_collection_uses_junction_table(client, app):
    assert login(client, "alice", "Password123!").status_code == 302
    create = client.post(
        "/collection/create",
        json={"collectionName": "Quick meals"},
        headers={"X-CSRFToken": csrf(client)},
    )
    assert create.status_code == 201
    with app.app_context():
        columns = {
            row["name"] for row in get_db().execute("PRAGMA table_info(collection)")
        }
        assert "recipeID" not in columns
        assert get_db().execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='collection_recipe'"
        ).fetchone()


def test_admin_routes_are_protected(client):
    assert client.get("/manage").status_code == 302
    assert login(client, "admin1", "Admin123!").status_code == 302
    assert client.get("/manage").status_code == 200


def test_legacy_plaintext_password_is_upgraded(client, app):
    with app.app_context():
        db = get_db()
        db.execute(
            """
            INSERT INTO users (
                userName, userPassword, userEmail, userPackage, userStatus,
                userBio, userProfilePic, userHeaderPic
            ) VALUES ('legacy', 'legacy-pass', 'legacy@example.com', 'free', 'active', '', '', '')
            """
        )
        db.commit()

    assert login(client, "legacy", "legacy-pass").status_code == 302
    with app.app_context():
        stored = get_db().execute(
            "SELECT userPassword FROM users WHERE userName = 'legacy'"
        ).fetchone()["userPassword"]
        assert stored.startswith(("scrypt:", "pbkdf2:"))
