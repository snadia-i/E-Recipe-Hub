import sqlite3

def get_db():
    conn = sqlite3.connect('instance/database2.db')
    conn.row_factory = sqlite3.Row
    return conn

class Comment:
    @staticmethod
    def get_all_comments():
        """Fetch all comments from the database."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comment")
            comments = cursor.fetchall()
            conn.close()
            return comments
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_comment_by_id(comment_id):
        """Fetch a single comment by its ID."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comment WHERE commentID = ?", (comment_id,))
            comment = cursor.fetchone()
            conn.close()
            return comment
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    @staticmethod
    def get_comments_by_user_id(user_id):
        """Fetch all comments made by a specific user."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM comment WHERE userID = ?", (user_id,))
            comments = cursor.fetchall()
            conn.close()
            return comments
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def get_comments_by_recipe_id(recipe_id):
        """Fetch all comments for a specific recipe, including user names."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            query = """
                SELECT comment.commentID, comment.commentText, comment.commentTime, user.userName
                FROM comment
                JOIN user ON comment.userID = user.userID
                WHERE comment.recipeID = ?
            """
            cursor.execute(query, (recipe_id,))
            comments = cursor.fetchall()
            conn.close()
            return [{'commentID': row[0], 'commentText': row[1], 'commentTime': row[2], 'userName': row[3]} for row in comments]
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    @staticmethod
    def add_comment(recipe_id, user_id, comment_text):
        """Add a new comment to the database."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO comment (recipeID, userID, commentText) VALUES (?, ?, ?)", (recipe_id, user_id, comment_text))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    @staticmethod
    def create_comment(comment_text, user_id, recipe_id):
        """Create a new comment and return its ID."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO comment (commentText, userID, recipeID) VALUES (?, ?, ?)",
                (comment_text, user_id, recipe_id)
            )
            conn.commit()
            comment_id = cursor.lastrowid
            conn.close()
            return comment_id
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None

    @staticmethod
    def update_comment_text(comment_id, new_text):
        """Update the text of an existing comment."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE comment SET commentText = ? WHERE commentID = ?",
                (new_text, comment_id)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False

    @staticmethod
    def delete_comment(comment_id):
        """Delete a comment by its ID."""
        try:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM comment WHERE commentID = ?", (comment_id,))
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return False