from __future__ import annotations

from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..repositories.admin import NotificationRepository, ReportRepository
from ..repositories.collections import CollectionRepository
from ..repositories.comments import CommentRepository
from ..repositories.recipes import RecipeRepository
from ..security import admin_required, login_required
from ..serializers import comment_dict, recipe_dict
from ..utils import clean_text, parse_positive_int, save_image

VALID_LABELS = {"breakfast", "lunch", "dinner", "snack", "dessert"}
VALID_STATUSES = {"published", "archived", "suspended"}



def _recipe_form_values():
    title = clean_text(request.form.get("title"), max_length=120)
    description = clean_text(request.form.get("description"), max_length=1000)
    ingredients = clean_text(request.form.get("ingredients"), max_length=5000)
    steps = clean_text(request.form.get("steps"), max_length=10000)
    cuisine = clean_text(request.form.get("cuisines"), max_length=50).lower()
    label = clean_text(request.form.get("labels"), max_length=30).lower()

    if not all((title, description, ingredients, steps, cuisine, label)):
        raise ValueError("All recipe fields are required.")
    if label not in VALID_LABELS:
        raise ValueError("Select a valid recipe label.")

    preparation_time = parse_positive_int(request.form.get("time"), "Preparation time")
    calories = parse_positive_int(request.form.get("calories"), "Calories")
    return (
        title,
        description,
        ingredients,
        steps,
        preparation_time,
        calories,
        cuisine,
        label,
    )


def register_recipe_routes(app) -> None:
    @app.route("/")
    def main():
        recipes = RecipeRepository.published()
        notifications = []
        if session.get("role") == "user" and session.get("userPackage"):
            notifications = NotificationRepository.all(session["userPackage"])
        return render_template("userhome.html", recipes=recipes, notifications=notifications)

    @app.route("/userhome")
    def userhome():
        return main()

    @app.route("/recipe/<int:id>")
    def get_recipe(id: int):
        recipe = RecipeRepository.by_id(id)
        if not recipe:
            return render_template("404.html"), 404

        is_owner = session.get("role") == "user" and session.get("user_id") == recipe["userID"]
        is_admin = session.get("role") == "admin"
        if recipe["recipeStatus"] != "published" and not (is_owner or is_admin):
            return render_template("404.html"), 404

        user_liked = False
        user_collected = False
        if session.get("role") == "user" and session.get("user_id"):
            user_id = int(session["user_id"])
            user_liked = RecipeRepository.is_liked(id, user_id)
            user_collected = CollectionRepository.is_saved_by_user(id, user_id)

        return render_template(
            "recipe.html",
            recipe=recipe,
            like_count=recipe["likeCount"],
            comments=CommentRepository.by_recipe(id),
            user_liked=user_liked,
            user_collected=user_collected,
            can_edit=is_owner,
        )

    @app.route("/api/recipe/<int:id>")
    @login_required
    def get_recipe_data(id: int):
        recipe = RecipeRepository.by_id(id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        return jsonify(
            {
                "recipeID": recipe["recipeID"],
                "userID": recipe["userID"],
                "reportSenderUserID": session["user_id"],
            }
        )

    @app.route("/createrecipe", methods=["GET", "POST"])
    @login_required
    def createrecipe():
        if request.method == "GET":
            return render_template("createrecipe.html")

        try:
            values = _recipe_form_values()
            image_url = save_image(request.files.get("recipe_image"))
        except ValueError as error:
            flash(str(error), "error")
            return render_template("createrecipe.html"), 400

        recipe_id = RecipeRepository.create(
            *values[:4],
            image_url or current_app.config["DEFAULT_RECIPE_IMAGE"],
            values[4],
            values[5],
            values[7],
            values[6],
            "published",
            int(session["user_id"]),
        )
        flash("Recipe published successfully.", "success")
        return redirect(url_for("get_recipe", id=recipe_id))

    @app.route("/edit_recipe/<int:recipe_id>", methods=["GET", "POST"])
    @login_required
    def edit_recipe(recipe_id: int):
        recipe = RecipeRepository.by_id(recipe_id)
        if not recipe:
            return render_template("404.html"), 404
        if recipe["userID"] != session["user_id"]:
            return jsonify({"error": "You may only edit your own recipes."}), 403

        if request.method == "GET":
            return render_template("editrecipe.html", recipe=recipe)

        try:
            values = _recipe_form_values()
            image_url = save_image(request.files.get("recipe_image"))
        except ValueError as error:
            flash(str(error), "error")
            return render_template("editrecipe.html", recipe=recipe), 400

        updated = RecipeRepository.update(
            recipe_id,
            values[0],
            values[1],
            values[2],
            values[3],
            values[4],
            values[5],
            values[6],
            values[7],
            image_url,
        )
        flash("Recipe updated successfully." if updated else "Recipe update failed.", "success" if updated else "error")
        return redirect(url_for("edit_recipe", recipe_id=recipe_id))

    @app.route("/recipe/<int:id>/likes")
    def get_recipe_like_count(id: int):
        if not RecipeRepository.by_id(id):
            return jsonify({"error": "Recipe not found"}), 404
        return jsonify({"recipeID": id, "likeCount": RecipeRepository.like_count(id)})

    @app.route("/recipe/<int:id>/like", methods=["POST"])
    @login_required
    def like_recipe(id: int):
        recipe = RecipeRepository.by_id(id)
        if not recipe or recipe["recipeStatus"] != "published":
            return jsonify({"error": "Recipe not found"}), 404
        liked, count = RecipeRepository.toggle_like(id, int(session["user_id"]))
        return jsonify({"success": True, "liked": liked, "likeCount": count})

    @app.route("/recipe/<int:id>/comments")
    def get_recipe_comments(id: int):
        if not RecipeRepository.by_id(id):
            return jsonify({"error": "Recipe not found"}), 404
        return jsonify({"comments": [comment_dict(row) for row in CommentRepository.by_recipe(id)]})

    @app.route("/recipe/<int:id>/comment", methods=["POST"])
    @login_required
    def add_comment(id: int):
        recipe = RecipeRepository.by_id(id)
        if not recipe or recipe["recipeStatus"] != "published":
            return jsonify({"error": "Recipe not found"}), 404

        text = clean_text(request.form.get("comment"), max_length=500)
        if not text:
            return jsonify({"error": "Comment text is required"}), 400
        CommentRepository.create(id, int(session["user_id"]), text)
        comments = [comment_dict(row) for row in CommentRepository.by_recipe(id)]
        return jsonify({"success": True, "comments": comments})

    @app.route("/recipe/<int:recipe_id>/comment/<int:comment_id>", methods=["DELETE"])
    def delete_comment(recipe_id: int, comment_id: int):
        if session.get("role") not in {"user", "admin"}:
            return jsonify({"error": "Authentication required"}), 401
        comment = CommentRepository.by_id(comment_id)
        if not comment or comment["recipeID"] != recipe_id:
            return jsonify({"error": "Comment not found"}), 404
        is_owner = session.get("role") == "user" and comment["userID"] == session.get("user_id")
        if not is_owner and session.get("role") != "admin":
            return jsonify({"error": "You cannot delete this comment"}), 403
        return jsonify({"success": CommentRepository.delete(comment_id)})

    @app.route("/search")
    def search():
        query = clean_text(request.args.get("q"), max_length=100)
        if not query:
            return jsonify([])
        return jsonify([recipe_dict(row) for row in RecipeRepository.search(query)])

    @app.route("/filter", methods=["POST"])
    def filter_recipe():
        data = request.get_json(silent=True) or {}
        cuisines = [clean_text(item, max_length=50) for item in data.get("cuisines", []) if clean_text(item)]
        labels = [clean_text(item, max_length=30) for item in data.get("labels", []) if clean_text(item)]
        return jsonify([recipe_dict(row) for row in RecipeRepository.filter(cuisines, labels)])

    @app.route("/sort", methods=["POST"])
    def sort_recipes():
        data = request.get_json(silent=True) or {}
        sort_by = data.get("sort_by", "title")
        order = data.get("order", "asc")
        if sort_by not in {"title", "time", "calories"}:
            return jsonify({"error": "Invalid sorting field"}), 400
        if order not in {"asc", "desc"}:
            return jsonify({"error": "Invalid sorting direction"}), 400
        return jsonify([recipe_dict(row) for row in RecipeRepository.sort(sort_by, order)])

    @app.route("/admin/recipe/<int:id>")
    @admin_required
    def get_recipe_admin(id: int):
        recipe = RecipeRepository.by_id(id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        return jsonify(recipe_dict(recipe))

    @app.route("/recipe/update_status/<int:recipe_id>", methods=["POST"])
    def update_recipe_status(recipe_id: int):
        recipe = RecipeRepository.by_id(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        status = clean_text(request.form.get("status"), max_length=20)
        if status not in VALID_STATUSES:
            return jsonify({"error": "Invalid recipe status"}), 400

        if session.get("role") == "admin":
            allowed = True
        else:
            allowed = (
                session.get("role") == "user"
                and session.get("user_id") == recipe["userID"]
                and status in {"published", "archived"}
            )
        if not allowed:
            return jsonify({"error": "Permission denied"}), 403

        RecipeRepository.update_status(recipe_id, status)
        return jsonify({"message": "Recipe status updated", "status": status})

    @app.route("/recipe/delete/<int:recipe_id>", methods=["POST"])
    def delete_recipe(recipe_id: int):
        recipe = RecipeRepository.by_id(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        allowed = session.get("role") == "admin" or (
            session.get("role") == "user" and session.get("user_id") == recipe["userID"]
        )
        if not allowed:
            return jsonify({"error": "Permission denied"}), 403
        RecipeRepository.delete(recipe_id)
        return jsonify({"message": "Recipe deleted successfully"})

    @app.route("/report/create/<int:recipe_id>", methods=["POST"])
    @app.route(
        "/report/create/<int:recipe_id>/<int:sender_id>/<int:reported_user_id>",
        methods=["POST"],
    )
    @login_required
    def create_report(
        recipe_id: int, sender_id: int | None = None, reported_user_id: int | None = None
    ):
        del sender_id, reported_user_id
        recipe = RecipeRepository.by_id(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404
        if recipe["userID"] == session["user_id"]:
            flash("You cannot report your own recipe.", "error")
            return redirect(url_for("get_recipe", id=recipe_id))

        title = clean_text(request.form.get("title"), max_length=120)
        details = clean_text(request.form.get("details"), max_length=2000)
        if not title or not details:
            flash("A report title and details are required.", "error")
            return redirect(url_for("get_recipe", id=recipe_id))

        ReportRepository.create(
            title,
            details,
            int(session["user_id"]),
            int(recipe["userID"]),
            recipe_id,
        )
        flash("Report submitted successfully.", "success")
        return redirect(url_for("get_recipe", id=recipe_id))
