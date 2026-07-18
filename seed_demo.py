from __future__ import annotations

"""Create demonstration records only when the database is empty.

This guard prevents the demo script from adding sample accounts to an existing
project database containing real users and recipes.
"""

from website import create_app
from website.database import get_db
from website.repositories.admin import AdminRepository, NotificationRepository, ReportRepository
from website.repositories.collections import CollectionRepository
from website.repositories.comments import CommentRepository
from website.repositories.recipes import RecipeRepository
from website.repositories.users import UserRepository
from website.security import hash_password


app = create_app()

with app.app_context():
    db = get_db()
    existing_users = db.execute("SELECT COUNT(*) AS count FROM user").fetchone()["count"]
    existing_recipes = db.execute("SELECT COUNT(*) AS count FROM recipe").fetchone()["count"]
    existing_admins = db.execute("SELECT COUNT(*) AS count FROM admin").fetchone()["count"]

    if existing_users or existing_recipes or existing_admins:
        print("Demo data was not created because this database already contains project data.")
        print("Use your existing usernames and passwords to log in.")
        raise SystemExit(0)

    admin_id = AdminRepository.create(
        "admin1",
        hash_password("Admin123!"),
        "admin@example.com",
        "/static/images/mingyu.jpg",
    )
    alice_id = UserRepository.create(
        "alice",
        hash_password("Password123!"),
        "alice@example.com",
        "/static/images/mingyu.jpg",
        "/static/images/view.jpg",
    )
    bob_id = UserRepository.create(
        "bob",
        hash_password("Password123!"),
        "bob@example.com",
        "/static/images/mingyu.jpg",
        "/static/images/green.jpg",
    )

    ayam_id = RecipeRepository.create(
        "Ayam Goreng Berempah",
        "A fragrant Malaysian fried chicken coated with toasted spices.",
        "1 whole chicken, cut into pieces\n4 stalks lemongrass\n5 shallots\n4 cloves garlic\n2 tbsp coriander seeds\nSalt to taste",
        "Blend the aromatics and spices.\nMarinate the chicken for at least 2 hours.\nDeep-fry until golden and fully cooked.\nFry the remaining spice mixture until crisp and serve over the chicken.",
        "/static/images/AyamGorengBerempah-1260.jpg",
        55,
        520,
        "dinner",
        "malay",
        "published",
        alice_id,
    )
    roast_id = RecipeRepository.create(
        "Crispy Spiced Chicken",
        "Juicy chicken roasted with coriander, curry leaves, and warming spices.",
        "Chicken pieces\nCoriander powder\nTurmeric\nCurry leaves\nCooking oil\nSalt",
        "Mix the spices with oil.\nCoat the chicken evenly.\nRoast until browned and cooked through.\nRest for five minutes before serving.",
        "/static/images/5c75b49e200ddca8181bc51154043fde.jpg",
        50,
        470,
        "dinner",
        "asian",
        "published",
        bob_id,
    )
    collection_id = CollectionRepository.create(alice_id, "Weekend favourites")
    CollectionRepository.add_recipe(collection_id, roast_id, alice_id)
    RecipeRepository.toggle_like(roast_id, alice_id)
    CommentRepository.create(roast_id, alice_id, "The spice blend worked really well!")
    ReportRepository.create(
        "Ingredient quantity needs checking",
        "The salt quantity is not stated clearly.",
        alice_id,
        bob_id,
        roast_id,
    )
    NotificationRepository.create(
        "Welcome to E-Recipe Hub",
        "Discover, publish, and organise your favourite recipes.",
        "all",
    )
    NotificationRepository.create(
        "New premium collection tools",
        "Premium users can now create additional recipe collections.",
        "premium",
    )

print("Demo data created.")
print("User: alice / Password123!")
print("Admin: admin1 / Admin123!")
