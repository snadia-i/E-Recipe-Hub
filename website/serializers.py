from __future__ import annotations


def recipe_dict(recipe) -> dict:
    keys = (
        "recipeID",
        "recipeTitle",
        "recipeDescription",
        "recipeIngredients",
        "recipeSteps",
        "recipePic",
        "recipeTime",
        "recipeCalories",
        "recipeLabel",
        "recipeCuisine",
        "recipeStatus",
        "userID",
        "userName",
        "likeCount",
    )
    data = dict(recipe)
    return {key: data.get(key) for key in keys if key in data}


def comment_dict(comment) -> dict:
    data = dict(comment)
    return {
        "commentID": data.get("commentID"),
        "commentText": data.get("commentText"),
        "commentTime": data.get("commentTime"),
        "userID": data.get("userID"),
        "userName": data.get("userName"),
    }


def collection_dict(collection) -> dict:
    data = dict(collection)
    return {
        "collectionID": data.get("collectionID"),
        "collectionName": data.get("collectionName"),
        "collectionPic": data.get("collectionPic"),
        "collectionSize": data.get("collectionSize", 0),
    }
