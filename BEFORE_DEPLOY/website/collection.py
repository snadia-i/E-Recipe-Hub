import sqlite3

def get_db():
    """Returns a database connection."""
    conn = sqlite3.connect('instance/database2.db')
    conn.row_factory = sqlite3.Row
    return conn

class Collection:

    @staticmethod
    def get_collections_by_user_id(user_id):
        """Fetch collections with size and image for a specific user."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.collectionID, c.collectionName, 
                    COUNT(r.recipeID) AS collectionSize, 
                    COALESCE(MIN(r.recipePic), 'https://i.pinimg.com/474x/c3/9c/56/c39c56bc405dde5bfd4a92cfdb22f4fd.jpg') AS collectionPic
                FROM collection c
                LEFT JOIN recipe r ON c.recipeID = r.recipeID
                WHERE c.userID = ?
                GROUP BY c.collectionID, c.collectionName
            """, (user_id,))

            collections = cursor.fetchall()
            conn.close()
            return collections
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_recipes_by_collection(collection_id):
        """Fetch recipes for a specific collection using a junction table."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            
            # Get all recipeIDs for this collection
            cursor.execute("""
                SELECT r.recipeID, r.recipeTitle, r.recipeDescription, 
                    r.recipePic, r.recipeTime, r.recipeCalories, r.recipeCuisine
                FROM collection c
                JOIN recipe r ON c.recipeID = r.recipeID
                WHERE c.collectionID = ?
            """, (collection_id,))

            recipes = cursor.fetchall()
            conn.close()

            # Return formatted recipe details
            return [
                {
                    'recipeID': row[0],
                    'recipeTitle': row[1],
                    'recipeDescription': row[2],
                    'recipePic': row[3],
                    'recipeTime': row[4],
                    'recipeCalories': row[5],
                    'recipeCuisine': row[6]
                }
                for row in recipes
            ]

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def create_collection(user_id, collection_name):
        """Create a new collection with a manually managed collectionID."""
        try:
            conn = get_db()
            cursor = conn.cursor()

            # Fetch the highest current collectionID and increment it
            cursor.execute("SELECT COALESCE(MAX(collectionID), 0) FROM collection")
            max_id = cursor.fetchone()[0]
            new_collection_id = max_id + 1

            # Insert the new collection
            cursor.execute("""
                INSERT INTO collection (collectionID, collectionName, userID)
                VALUES (?, ?, ?)
            """, (new_collection_id, collection_name, user_id))

            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    @staticmethod
    def add_recipe_to_collection(collection_id, recipe_id):
        try:
            conn = sqlite3.connect('instance/database2.db')
            cursor = conn.cursor()

            # Step 1: Check if collectionID exists and fetch collectionName and userID
            cursor.execute("SELECT collectionName, userID FROM collection WHERE collectionID = ?", (collection_id,))
            result = cursor.fetchone()

            if not result:
                print(f"Collection {collection_id} does not exist.")  # Debugging
                conn.close()
                return False  # Return False if collectionID is invalid

            collection_name, user_id = result  # Extract collection name and user ID
            print(f"Adding recipe {recipe_id} to collection '{collection_name}' (ID: {collection_id}, User: {user_id})")  # Debugging

            # Step 2: Insert into the correct many-to-many relationship table (collection_recipe)
            cursor.execute(
                "INSERT INTO collection (collectionID, collectionName, userID, recipeID) VALUES (?, ? , ?, ?)",
                (collection_id, collection_name, user_id, recipe_id)
            )

            conn.commit()
            conn.close()
            return True

        except sqlite3.IntegrityError:
            print(f"Recipe {recipe_id} is already in collection {collection_id}.")  # Debugging
            return False  # Prevent duplicate entries

        except sqlite3.Error as e:
            print(f"Database error: {e}")  # Debugging
            return False


