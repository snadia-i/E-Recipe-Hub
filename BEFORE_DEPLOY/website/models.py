import sqlite3
from os import path
import os

DB_NAME = "database2.db"
DB_PATH = path.join('instance', DB_NAME)
class DatabaseManager:
    @staticmethod
    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def init_db():
        os.makedirs('instance', exist_ok=True)

        try:
            conn = DatabaseManager.get_db()
            cursor = conn.cursor()

            # cursor.executescript("""
            #     CREATE TABLE IF NOT EXISTS user (
            #         userID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         userName TEXT NOT NULL UNIQUE,
            #         userPassword TEXT NOT NULL,
            #         userEmail TEXT NOT NULL,
            #         userPackage TEXT NOT NULL,
            #         userStatus TEXT NOT NULL,
            #         userBio TEXT,
            #         userProfilePic TEXT,
            #         userHeaderPic TEXT
            #     );

            #     CREATE TABLE IF NOT EXISTS recipe (
            #         recipeID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         recipeTitle TEXT NOT NULL,
            #         recipeDescription TEXT NOT NULL,
            #         recipeIngredients TEXT NOT NULL,
            #         recipeSteps TEXT NOT NULL,
            #         recipePic TEXT,
            #         recipeTime INTEGER NOT NULL,
            #         recipeCalories INTEGER NOT NULL,
            #         recipeLabel TEXT,
            #         recipeCuisine TEXT,
            #         recipeStatus TEXT NOT NULL,
            #         userID INTEGER NOT NULL,
            #         FOREIGN KEY (userID) REFERENCES user(userID)
            #     );

            #     CREATE TABLE IF NOT EXISTS collection (
            #         collectionID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         collectionName TEXT NOT NULL,
            #         userID INTEGER NOT NULL,
            #         FOREIGN KEY (userID) REFERENCES user(userID)
            #     );

            #     CREATE TABLE IF NOT EXISTS admin (
            #         adminID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         adminName TEXT NOT NULL UNIQUE,
            #         adminPassword TEXT NOT NULL,
            #         adminEmail TEXT NOT NULL,
            #         adminProfilePic TEXT
            #     );

            #     CREATE TABLE IF NOT EXISTS report (
            #         reportID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         reportTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #         reportStatus TEXT NOT NULL DEFAULT 'pending',
            #         reportDetails TEXT NOT NULL,
            #         reportSenderUserID INTEGER NOT NULL,
            #         reportedUserID INTEGER NOT NULL,
            #         reportedRecipeID INTEGER NOT NULL,
            #         FOREIGN KEY (reportedUserID) REFERENCES user(userID),
            #         FOREIGN KEY (reportSenderUserID) REFERENCES user(userID),
            #         FOREIGN KEY (reportedRecipeID) REFERENCES recipe(recipeID)
            #     );

            #     CREATE TABLE IF NOT EXISTS notification (
            #         notiID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         notiTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #         notiTitle TEXT NOT NULL,
            #         notiDetails TEXT NOT NULL,
            #         notiReceiver TEXT NOT NULL,
            #         FOREIGN KEY (notiReceiver) REFERENCES user(userPackage)
            #     );

            #     CREATE TABLE IF NOT EXISTS like (
            #         likeID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         userID INTEGER NOT NULL,
            #         recipeID INTEGER NOT NULL,
            #         likeTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #         FOREIGN KEY (userID) REFERENCES user(userID),
            #         FOREIGN KEY (recipeID) REFERENCES recipe(recipeID)
            #     );

            #     CREATE TABLE IF NOT EXISTS comment (
            #         commentID INTEGER PRIMARY KEY AUTOINCREMENT,
            #         commentTime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            #         commentText TEXT NOT NULL,
            #         userID INTEGER NOT NULL,
            #         recipeID INTEGER NOT NULL,
            #         FOREIGN KEY (userID) REFERENCES user(userID),
            #         FOREIGN KEY (recipeID) REFERENCES recipe(recipeID)
            #     );
            # """)

            # cursor.executemany("""
            # INSERT OR IGNORE INTO user (userName, userPassword, userEmail, userPackage, userStatus, userBio, userProfilePic, userHeaderPic) 
            # VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            # """, [
            #     ('alice', 'password123', 'alice@example.com', 'free', 'active', 'Home cook', 'pic1.jpg', 'header1.jpg'),
            #     ('bob', 'password456', 'bob@example.com', 'premium', 'active', 'Professional Chef', 'pic2.jpg', 'header2.jpg'),
            #     ('charlie', 'password789', 'charlie@example.com', 'free', 'suspended', 'Baking Enthusiast', 'pic3.jpg', 'header3.jpg'),
            #     ('david', 'password321', 'david@example.com', 'premium', 'active', 'Healthy Recipes', 'pic4.jpg', 'header4.jpg'),
            #     ('eve', 'password654', 'eve@example.com', 'free', 'active', 'Quick Meals Lover', 'pic5.jpg', 'header5.jpg'),
            #     ('frank', 'password987', 'frank@example.com', 'premium', 'active', 'Grill Master', 'pic6.jpg', 'header6.jpg'),
            #     ('grace', 'password147', 'grace@example.com', 'free', 'active', 'Dessert Expert', 'pic7.jpg', 'header7.jpg'),
            #     ('hannah', 'password258', 'hannah@example.com', 'premium', 'active', 'Plant-based Recipes', 'pic8.jpg', 'header8.jpg'),
            #     ('ivan', 'password369', 'ivan@example.com', 'free', 'active', 'Seafood Specialist', 'pic9.jpg', 'header9.jpg'),
            #     ('jack', 'password741', 'jack@example.com', 'premium', 'suspended', 'Fusion Cuisine Innovator', 'pic10.jpg', 'header10.jpg')
            # ])

            # cursor.executemany("""
            # INSERT OR IGNORE INTO collection (collectionName, userID) 
            # VALUES (?, ?)
            # """, [
            #     ('Italian Favorites', 1),
            #     ('Quick Meals', 2),
            #     ('Healthy Choices', 3),
            #     ('Family Dinners', 4),
            #     ('Vegan Delights', 5),
            #     ('BBQ Specials', 6),
            #     ('Sweet Treats', 7),
            #     ('Plant-Based Wonders', 8),
            #     ('Seafood Specials', 9),
            #     ('Fusion Hits', 10)
            # ])

            # cursor.executemany("""
            # INSERT OR IGNORE INTO admin (adminName, adminPassword, adminEmail, adminProfilePic) 
            # VALUES (?, ?, ?, ?)
            # """, [
            #     ('admin1', 'securepass1', 'admin1@example.com', 'adminpic1.jpg'),
            #     ('admin2', 'securepass2', 'admin2@example.com', 'adminpic2.jpg'),
            #     ('admin3', 'securepass3', 'admin3@example.com', 'adminpic3.jpg')
            # ])

            # cursor.executemany("""
            # INSERT OR IGNORE INTO recipe (recipeTitle, recipeDescription, recipeIngredients, recipeSteps, recipePic, recipeTime, recipeCalories, recipeLabel, recipeCuisine, recipeStatus, userID) 
            # VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            # """, [
            #     ('Spaghetti Carbonara', 'Classic Italian pasta', 'Pasta, Eggs, Cheese, Bacon', 'Boil pasta, cook bacon...', 'carbonara.jpg', 30, 600, 'Dinner', 'Italian', 'published', 1),
            #     ('Avocado Toast', 'Healthy breakfast option', 'Avocado, Bread, Olive Oil', 'Toast bread, mash avocado...', 'avocado.jpg', 10, 250, 'Breakfast', 'American', 'published', 2),
            #     ('Chocolate Cake', 'Rich chocolate dessert', 'Flour, Cocoa, Eggs', 'Mix ingredients, bake...', 'choc_cake.jpg', 60, 800, 'Dessert', 'French', 'published', 3),
            #     ('Grilled Chicken', 'Tasty grilled dish', 'Chicken, Spices', 'Marinate, grill...', 'grilled_chicken.jpg', 45, 400, 'Lunch', 'American', 'published', 4),
            #     ('Caesar Salad', 'Classic salad', 'Lettuce, Croutons, Dressing', 'Toss ingredients...', 'caesar.jpg', 20, 300, 'Lunch', 'Italian', 'published', 5),
            #     ('Vegan Curry', 'Delicious vegan option', 'Veggies, Coconut Milk, Spices', 'Cook veggies...', 'vegan_curry.jpg', 50, 500, 'Dinner', 'Indian', 'published', 6),
            #     ('Apple Pie', 'Traditional dessert', 'Apples, Dough, Sugar', 'Bake apples...', 'apple_pie.jpg', 90, 700, 'Dessert', 'American', 'published', 7),
            #     ('Smoothie Bowl', 'Healthy breakfast', 'Fruits, Yogurt, Nuts', 'Blend fruits...', 'smoothie.jpg', 15, 350, 'Breakfast', 'American', 'published', 8),
            #     ('Fish Tacos', 'Spicy seafood treat', 'Fish, Tortillas, Sauce', 'Cook fish...', 'fish_tacos.jpg', 30, 400, 'Lunch', 'Mexican', 'published', 9),
            #     ('Fusion Stir-fry', 'Mix of flavors', 'Veggies, Noodles, Sauce', 'Stir-fry...', 'fusion_stir_fry.jpg', 25, 450, 'Dinner', 'Asian', 'published', 10)
            # ])

            # cursor.executemany("""
            # INSERT OR IGNORE INTO like (userID, recipeID, likeTime) 
            # VALUES (?, ?, CURRENT_TIMESTAMP)
            # """, [
            #     (1, 2), (1, 3), (2, 1), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9), (9, 10)
            # ])

            # cursor.executemany("""
            # INSERT OR IGNORE INTO comment (commentText, userID, recipeID) 
            # VALUES (?, ?, ?)
            # """, [
            #     ('Delicious recipe!', 1, 2),
            #     ('Easy to follow steps.', 2, 3),
            #     ('Loved the flavors.', 3, 1),
            #     ('Will make this again.', 4, 4),
            #     ('Perfect for dinner.', 5, 5),
            #     ('Great vegan option.', 6, 6),
            #     ('My family loved it.', 7, 7),
            #     ('Refreshing and healthy.', 8, 8),
            #     ('Best tacos ever!', 9, 9),
            #     ('Simple yet tasty.', 10, 10)
            # ])

            # cursor.executemany("""
            # INSERT OR IGNORE INTO report (reportDetails, reportSenderUserID, reportedUserID, reportedRecipeID) 
            # VALUES (?, ?, ?, ?)
            # """, [
            #     ('Inappropriate content in recipe.', 1, 3, 5),
            #     ('Misleading recipe instructions.', 2, 4, 6),
            #     ('Plagiarism detected.', 3, 5, 7),
            #     ('Harmful health advice.', 4, 6, 8),
            #     ('Incorrect ingredient amounts.', 5, 7, 9),
            #     ('Offensive recipe language.', 6, 8, 10),
            #     ('Duplicate recipe.', 7, 9, 1),
            #     ('Spam content in recipe.', 8, 10, 2),
            #     ('Recipe not suitable for minors.', 9, 1, 3),
            #     ('Missing cooking steps.', 10, 2, 4)
            # ])

            # cursor.executemany("""
            # INSERT OR IGNORE INTO notification (notiTitle, notiDetails, notiReceiver) 
            # VALUES (?, ?, ?)
            # """, [
            #     ('New Recipe Published', 'Check out the latest recipes.', 'free'),
            #     ('Recipe Like Alert', 'Someone liked your recipe.', 'premium'),
            #     ('Account Status Update', 'Your account status has changed.', 'free'),
            #     ('New Recipe Tips', 'Discover our expert cooking tips.', 'premium'),
            #     ('Cooking Contest', 'Participate in our monthly contest.', 'free'),
            #     ('Account Suspension Alert', 'Your account has been suspended.', 'free'),
            #     ('Recipe Feature Alert', 'Your recipe is now featured!', 'premium'),
            #     ('Profile Update Reminder', 'Keep your profile up to date.', 'free'),
            #     ('Exclusive Discounts', 'Enjoy premium discounts on packages.', 'premium'),
            #     ('Recipe Feedback Request', 'We value your feedback!', 'free')
            # ])

            conn.commit()
            print("Database initialized successfully.")
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            if conn:
                conn.close()
