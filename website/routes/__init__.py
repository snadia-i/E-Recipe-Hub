from .admin import register_admin_routes
from .auth import register_auth_routes
from .collections import register_collection_routes
from .recipes import register_recipe_routes
from .user import register_user_routes


def register_routes(app) -> None:
    register_auth_routes(app)
    register_recipe_routes(app)
    register_user_routes(app)
    register_collection_routes(app)
    register_admin_routes(app)
