import sqlite3

def get_db():
    conn = sqlite3.connect('instance/database2.db')
    conn.row_factory = sqlite3.Row
    return conn

class Recipe:
    @staticmethod
    def get_all_recipes():
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipe")
            recipes = cursor.fetchall()
            conn.close()
            return recipes
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_recipe_by_id(recipe_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipe WHERE recipeID = ?", (recipe_id,))
            recipe = cursor.fetchone()
            conn.close()
            return recipe
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None
        
    @staticmethod
    def get_recipe_by_user_id(user_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipe WHERE userID = ?", (user_id,))
            recipes = cursor.fetchall()
            conn.close()
            return recipes
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        
    @staticmethod
    def like_recipe(recipe_id, user_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO `like` (recipeID, userID) VALUES (?, ?)", (recipe_id, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
    
    @staticmethod
    def unlike_recipe(recipe_id, user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM like WHERE recipeID = ? AND userID = ?", (recipe_id, user_id))
        conn.commit()
        conn.close()
        return True
        
    @staticmethod
    def has_user_liked(recipe_id, user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM like WHERE recipeID = ? AND userID = ?", (recipe_id, user_id))
        like = cursor.fetchone()
        conn.close()
        return like is not None
        
    @staticmethod
    def get_recipe_like_count(recipe_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM `like` WHERE recipeID = ?", (recipe_id,))
            result = cursor.fetchone()
            conn.close()
            return result[0] if result else 0  # result[0] holds the like count
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return 0
        
    @staticmethod
    def add_to_collection(recipe_id, user_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO collection (recipeID, userID) VALUES (?, ?)", (recipe_id, user_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    @staticmethod
    def remove_from_collection(recipe_id, user_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM collection WHERE recipeID = ? AND userID = ?", (recipe_id, user_id))
        conn.commit()
        conn.close()
        return True


    @staticmethod
    def suspend_recipe(recipe_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE recipe SET recipeStatus = 'suspended' WHERE recipeID = ?", (recipe_id,))
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def archive_recipe(recipe_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("UPDATE recipe SET recipeStatus = 'archived' WHERE recipeID = ?", (recipe_id,))
            conn.commit()
        finally:
            conn.close()


    @staticmethod
    def search_recipe(query):
        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            SELECT recipeID, recipeTitle, recipePic, recipeDescription, recipeTime, recipeCalories, recipeCuisine
            FROM recipe
            WHERE recipeTitle LIKE ? OR recipeDescription LIKE ?
        """, (f"%{query}%", f"%{query}%"))

        results = cursor.fetchall()

        recipe = [
            {
                "recipeID": row[0],
                "recipeTitle": row[1],
                "recipePic": row[2],
                "recipeDescription": row[3],
                "recipeTime": row[4],
                "recipeCalories": row[5],
                "recipeCuisine": row[6]
            }
            for row in results
        ]

        return recipe
        
    @staticmethod
    def create_recipe(title, description, ingredients, steps, image_path, time, calories, label, cuisine, status, user_id):
        """Insert a new recipe into the database."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            print("Database connection established.")
            cursor.execute("""
                INSERT INTO recipe (
                    recipeTitle, recipeDescription, recipeIngredients, recipeSteps, 
                    recipePic, recipeTime, recipeCalories, recipeLabel, 
                    recipeCuisine, recipeStatus, userID
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, ingredients, steps, image_path, time, calories, label, cuisine, status, user_id))

            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        
    @staticmethod
    def save_recipe(title, description, ingredients, preparation_time, calories, cuisines, servings, labels, steps, image_path, status):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recipe (title, description, ingredients, time, calories, cuisines, servings, labels, steps, recipeStatus, image) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (title, description, ingredients, preparation_time, calories, cuisines, servings, labels, steps, status, image_path))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False
        
    @staticmethod
    def update_recipe(recipe_id, title, description, ingredients, steps, time, calories, cuisines, labels, image_url=None):
        try:
            conn = get_db()
            cursor = conn.cursor()
            print("Database connection established. YEY")
            cursor.execute("""
                UPDATE recipe 
                SET recipeTitle = ?, recipeDescription = ?, recipeIngredients = ?, recipeSteps = ?, 
                    recipeTime = ?, recipeCalories = ?, recipeCuisine = ?, recipeLabel = ?, recipePic = COALESCE(?, recipePic)
                WHERE recipeID = ?
            """, (title, description, ingredients, steps, time, calories, cuisines, labels, image_url, recipe_id))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    @staticmethod
    def get_published_recipes():
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM recipe WHERE recipeStatus = 'published'")
            recipes = cursor.fetchall()
            conn.close()
            return recipes
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        
    @staticmethod
    def delete_recipe(recipe_id):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recipe WHERE recipeID = ?", (recipe_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise False
        

    @staticmethod
    def update_recipe_status(recipe_id, new_status):
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE recipe
                SET recipeStatus = ?
                WHERE recipeID = ?
            """, (new_status, recipe_id))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
