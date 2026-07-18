from __future__ import annotations


from flask import jsonify, render_template, request, session

from ..database import DatabaseIntegrityError
from ..repositories.collections import CollectionRepository
from ..repositories.recipes import RecipeRepository
from ..security import login_required
from ..serializers import collection_dict, recipe_dict
from ..utils import clean_text


def register_collection_routes(app) -> None:
    @app.route("/collection")
    @login_required
    def collection():
        collections = CollectionRepository.by_user(int(session["user_id"]))
        payload = [collection_dict(row) for row in collections]
        if request.accept_mimetypes.best == "application/json":
            return jsonify({"collections": payload})
        return render_template("collection.html", collections=payload)

    @app.route("/collection/<int:collection_id>/recipes")
    @login_required
    def get_collection_recipes(collection_id: int):
        if not CollectionRepository.belongs_to(collection_id, int(session["user_id"])):
            return jsonify({"error": "Collection not found"}), 404
        rows = CollectionRepository.recipes(collection_id, int(session["user_id"]))
        return jsonify({"recipes": [recipe_dict(row) for row in rows]})

    @app.route("/collection/create", methods=["POST"])
    @login_required
    def create_collection():
        data = request.get_json(silent=True) or {}
        name = clean_text(data.get("collectionName"), max_length=80)
        if not name:
            return jsonify({"error": "Collection name is required"}), 400
        try:
            collection_id = CollectionRepository.create(int(session["user_id"]), name)
        except DatabaseIntegrityError:
            return jsonify({"error": "A collection with that name already exists"}), 409
        return jsonify(
            {
                "message": "Collection created successfully",
                "collectionID": collection_id,
            }
        ), 201

    @app.route("/collection/<int:collection_id>/delete", methods=["POST"])
    @app.route("/delete_collection/<int:collection_id>", methods=["POST"])
    @login_required
    def delete_collection(collection_id: int):
        deleted = CollectionRepository.delete(collection_id, int(session["user_id"]))
        if not deleted:
            return jsonify({"error": "Collection not found"}), 404
        return jsonify({"success": True})

    @app.route("/recipe/<int:recipe_id>/collection", methods=["POST"])
    @login_required
    def save_recipe_to_collection(recipe_id: int):
        recipe = RecipeRepository.by_id(recipe_id)
        if not recipe or recipe["recipeStatus"] != "published":
            return jsonify({"error": "Recipe not found"}), 404

        data = request.get_json(silent=True) or {}
        try:
            collection_id = int(data.get("collectionID"))
        except (TypeError, ValueError):
            return jsonify({"error": "A valid collection ID is required"}), 400

        added = CollectionRepository.add_recipe(
            collection_id, recipe_id, int(session["user_id"])
        )
        if not CollectionRepository.belongs_to(collection_id, int(session["user_id"])):
            return jsonify({"error": "Collection not found"}), 404
        if not added:
            return jsonify({"error": "Recipe is already in this collection"}), 409
        return jsonify({"success": True})

    @app.route(
        "/collection/<int:collection_id>/recipe/<int:recipe_id>/remove", methods=["POST"]
    )
    @login_required
    def remove_recipe_from_collection(collection_id: int, recipe_id: int):
        removed = CollectionRepository.remove_recipe(
            collection_id, recipe_id, int(session["user_id"])
        )
        if not removed:
            return jsonify({"error": "Saved recipe not found"}), 404
        return jsonify({"success": True})
