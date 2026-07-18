from flask import Flask, render_template, redirect, url_for, request, flash, session, jsonify, redirect
from .models import DatabaseManager
from .admin import Admin, Report, Notification
from .user import RegisteredUser
from .recipe import Recipe
from .comment import Comment
from .collection import Collection
import os
from werkzeug.utils import secure_filename

def create_app():
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'saranadianisafiza'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database2.db'

    DatabaseManager.init_db()

    # ----------------- UPLOAD FOLDER -----------------
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'website/static/uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # ----------------- MAIN ROUTES -----------------
    @app.route('/')
    def main():
        recipes = Recipe.get_published_recipes()
        # Handle logged-in vs. guest access
        if 'user' in session:
            user_package = session.get('userPackage')
            notifications = Notification.get_all_notifications(user_package)
        else:
            notifications = []  # No notifications for guests
        return render_template('userhome.html', recipes=recipes,  notifications=notifications)
    
    # ----------------- AUTHENTICATION ROUTES -----------------
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            email = request.form.get('email')

            if RegisteredUser.get_user_by_username(username):
                flash('Username already exists', 'error')
                return render_template('login.html')
            
            success = RegisteredUser.add_user(username, password, email)
            if success:
                flash('Signup successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Signup failed. Try again.', 'error')

        return render_template('login.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            # Check if the user exists in the user table
            user = RegisteredUser.get_user_by_username(username)

            if user:
                if user['userStatus'] == 'suspended':
                    return redirect(url_for('suspended_user_page'))
                
                if user and user['userPassword'] == password:
                    session['user'] = user['userName']
                    session['role'] = 'user'
                    session['userPackage'] = user['userPackage'] 
                    return redirect(url_for('main'))

            # If not a user, check if it's an admin
            admin = Admin.get_admin_by_username(username)
            if admin and admin['adminPassword'] == password:
                session['user'] = admin['adminName']
                session['role'] = 'admin'
                return redirect(url_for('adminhome'))

            # Invalid login
            # error = 'Invalid username or password'
            # return render_template('login.html', error=error)
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.pop('user', None)
        session.pop('role', None)
        session.pop('userPackage', None)
        return redirect(url_for('main'))

    # ----------------- USER ROUTES -----------------
    @app.route('/user/<int:id>')
    def get_user(id):
        user = RegisteredUser.get_user_by_id(id)
        if user:
            return {
                'userID': user['userID'],  
                'userName': user['userName'],
                'userEmail': user['userEmail'],
                'userBio': user['userBio'],
                'userPackage': user['userPackage'],
                'userHeaderPic': user['userHeaderPic'], 
                'userProfilePic': user['userProfilePic'], 
                'userStatus': user['userStatus']  
            }
        return {'error': 'User  not found'}, 404
    
    @app.route('/user/username/<string:username>')
    def get_user_by_username(username):
        user = RegisteredUser.get_user_by_username(username)
        if user:
            return {
                'userID': user['userID'],
                'userName': user['userName'],
                'userEmail': user['userEmail'],
                'userBio': user['userBio'],
                'userPackage': user['userPackage'],
                'userHeaderPic': user['userHeaderPic'],
                'userProfilePic': user['userProfilePic'],
                'userStatus': user['userStatus']
            }
        return {'error': 'User not found'}, 404
    
    @app.route('/profile', methods=['GET', 'POST'])
    def profile():
        if 'user' not in session:
            flash('Please log in to access your profile.', 'warning')
            return redirect(url_for('login'))
        
        username = session['user']
        user = RegisteredUser.get_user_by_username(username)
        recipes = RegisteredUser.get_recipes_by_user_id(user['userID']) if user else []
        
        if request.method == 'POST':
            updated_user = {
                'userName': request.form.get('userName'),
                'userEmail': request.form.get('userEmail'),
                'userBio': request.form.get('userBio'),
            }

            if 'userProfilePic' in request.files:
                file = request.files['userProfilePic']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    updated_user['userProfilePic'] = url_for('static', filename='uploads/' + filename)
                else:
                    updated_user['userProfilePic'] = user['userProfilePic']
                
            if 'userHeaderPic' in request.files:
                file = request.files['userHeaderPic']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    updated_user['userHeaderPic'] = url_for('static', filename='uploads/' + filename)
                else:
                    updated_user['userHeaderPic'] = user['userHeaderPic']
            
            if RegisteredUser.update_user(user['userID'], updated_user):
                session['user'] = updated_user['userName']  # Update session with new username
                # add confirm / error message
        if user:
            user_package = user['userPackage'] if 'userPackage' in user else 'free'
            notifications = Notification.get_notifications_by_package(user_package)
            return render_template('profile.html', user=user, recipes=recipes, notifications=notifications)
        else:
            flash('User not found', 'error')
            return redirect(url_for('userhome'))

    @app.route('/profile/edit_profile', methods=['POST'])
    def edit_profile():
        if 'user' not in session:
            return redirect(url_for('login'))
        
        username = session['user']
        user = RegisteredUser.get_user_by_username(username)
        if request.method == 'POST':
            updated_user = {
                'userName': request.form.get('userName'),
                'userEmail': request.form.get('userEmail'),
                'userBio': request.form.get('userBio'),
                'userProfilePic': user['userProfilePic'],  # Default to current profile pic
                'userHeaderPic': user['userHeaderPic']   # Default to current header pic
            }

            if 'userProfilePic' in request.files:
                file = request.files['userProfilePic']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    updated_user['userProfilePic'] = url_for('static', filename='uploads/' + filename)
                
            if 'userHeaderPic' in request.files:
                file = request.files['userHeaderPic']
                if file.filename:
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    updated_user['userHeaderPic'] = url_for('static', filename='uploads/' + filename)

            success = RegisteredUser.update_user(user['userID'], updated_user)
            if success:
                return "<script>alert('Profile updated successfully!'); window.location.href = '/profile';</script>"
        return render_template('edit_profile.html', user=user)
        
    @app.route('/suspended_user_page')
    def suspended_user_page():
        return render_template('suspended.html')
    
    # ----------------- RECIPE ROUTES -----------------
    def like_recipe(recipe_id, user_id):
        recipe = Recipe.get_recipe_by_id(recipe_id)
        if not recipe:
            flash("Recipe not found.", "error")
            return None, False

        if int(recipe['userID']) != user_id:
            flash("You do not have permission to like this recipe.", "error")
            return recipe, False

        return recipe, True

    @app.route('/edit_recipe/<int:recipe_id>', methods=['GET', 'POST'])
    def edit_recipe(recipe_id):
        username = session.get('user')
        if not username:
            flash("Please log in to edit recipes.", "warning")
            return redirect(url_for('login'))

        user = RegisteredUser.get_user_by_username(username)
        user_id = user['userID']

        recipe = Recipe.get_recipe_by_id(recipe_id)
        if not recipe:
            # flash("Recipe not found.", "error")
            return redirect(url_for('main'))

        if int(recipe['userID']) != user_id:
            # flash("You do not have permission to edit this recipe.", "error")
            return redirect(url_for('main'))

        if request.method == 'POST':
            new_title = request.form.get('title', '').strip()
            new_description = request.form.get('description', '').strip()
            new_ingredients = request.form.get('ingredients', '').strip()
            new_steps = request.form.get('steps', '').strip()
            new_time = request.form.get('time', '').strip()
            new_calories = request.form.get('calories', '').strip()
            new_cuisines = request.form.get('cuisines', '').strip()
            new_labels = request.form.get('labels', '').strip()
            image_url = None

            if 'recipe_image' in request.files:
                file = request.files['recipe_image']
                if file.filename != '':
                    image_filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                    image_url = url_for('static', filename='uploads/' + image_filename)

            if not new_title or not new_description or not new_ingredients or not new_steps:
                flash("All fields are required!", "error")
                return render_template('editrecipe.html', recipe=recipe)
            
            success = Recipe.update_recipe(recipe_id, new_title, new_description, new_ingredients, new_steps, new_time, new_calories, new_cuisines, new_labels, image_url)

            # if success:
            #     flash("Recipe updated successfully!", "success")
            # else:
            #     flash("Failed to update recipe.", "error")
            return redirect(url_for('edit_recipe', recipe_id=recipe_id))
        return render_template('editrecipe.html', recipe=recipe)

    @app.route('/recipe/<int:id>')
    def get_recipe(id):
        recipe = Recipe.get_recipe_by_id(id)
        if recipe:
            like_count = Recipe.get_recipe_like_count(id)
            comments = Comment.get_comments_by_recipe_id(id)
            user_liked = False
            if 'user' in session:
                user = RegisteredUser.get_user_by_username(session['user'])
                if user:
                    user_liked = Recipe.has_user_liked(id, user['userID'])
            return render_template('recipe.html', recipe=recipe, like_count=like_count, comments=comments, user_liked=user_liked)
        return {'error': 'Recipe not found'}, 404

    @app.route('/api/recipe/<int:id>', methods=['GET'])
    def get_recipe_data(id):
        recipe = Recipe.get_recipe_by_id(id)
        if recipe:
            recipe_data = {
                'recipeID': recipe['recipeID'],
                'userID': recipe['userID']
            }
            if 'user' in session:
                user = RegisteredUser.get_user_by_username(session['user'])
                recipe_data['reportSenderUserID'] = user['userID'] if user else None
            return recipe_data, 200
        return {'error': 'Recipe not found'}, 404

    @app.route('/user/<int:id>/recipes')
    def get_user_recipes(id):
        # Fetch user recipes
        recipes = Recipe.get_recipe_by_user_id(id)
        if recipes:
            return {'recipes': [dict(recipe) for recipe in recipes]}  # Return a list of recipes in a JSON-friendly format
        return {'recipes': []}  # If no recipes are found, return an empty list
    

    @app.route('/createrecipe', methods=['GET', 'POST'])
    def createrecipe():
        username = session.get('user')
        if not username:
            flash('Please log in to access this feature.', 'warning')
            return redirect(url_for('login'))
        user = RegisteredUser.get_user_by_username(username)
        if request.method == 'POST':
            user_id = user['userID']
            title = request.form.get('title')
            description = request.form.get('description')
            ingredients = request.form.get('ingredients')
            time = request.form.get('time')
            calories = request.form.get('calories')
            cuisines = request.form.get('cuisines')
            labels = request.form.get('labels')
            steps = request.form.get('steps')
            status = 'published'
            
            # Handle Image Upload
            if 'recipe_image' in request.files:
                file = request.files['recipe_image']
                if file.filename != '':
                    image_filename = secure_filename(file.filename)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                    image_url = url_for('static', filename='uploads/' + image_filename)
                            
            # Store in DB
            success = Recipe.create_recipe(title, description, ingredients, steps, image_url, time, calories, labels, cuisines, status, user_id)
            if success:
                flash("Recipe created successfully!", "success")
            else:
                flash("Failed to create recipe.", "error")
        return render_template('createrecipe.html')
    
    # ----------------- LIKE & COMMENT ROUTES -----------------
    @app.route('/recipe/<int:id>/likes')
    def get_recipe_like_count(id):
        # Fetch the total like count for the specified recipe
        like_count = Recipe.get_recipe_like_count(id)
        return {'recipeID': id, 'likeCount': like_count}

    @app.route('/recipe/<int:id>/comments')
    def get_recipe_comments(id):
        comments = Comment.get_comments_by_recipe_id(id)
        return {
            'comments': [dict(comment) for comment in comments]
        }

    @app.route('/recipe/<int:id>/like', methods=['POST'])
    def like_recipe(id):
        if 'user' not in session:
            return jsonify({'error': 'User not logged in'}), 401

        user = RegisteredUser.get_user_by_username(session['user'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if Recipe.has_user_liked(id, user['userID']):
            success = Recipe.unlike_recipe(id, user['userID'])
        else:
            success = Recipe.like_recipe(id, user['userID'])

        if success:
            like_count = Recipe.get_recipe_like_count(id)
            return jsonify({'success': True, 'likeCount': like_count})
        return jsonify({'error': 'Failed to like/unlike recipe'}), 500

    @app.route('/recipe/<int:id>/comment', methods=['POST'])
    def add_comment(id):
        if 'user' not in session:
            return jsonify({'error': 'User not logged in'}), 401

        user = RegisteredUser.get_user_by_username(session['user'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        comment_text = request.form.get('comment')
        if not comment_text:
            return jsonify({'error': 'Comment text is required'}), 400

        success = Comment.add_comment(id, user['userID'], comment_text)
        if success:
            comments = Comment.get_comments_by_recipe_id(id)
            return jsonify({'success': True, 'comments': [dict(comment) for comment in comments]})
        return jsonify({'error': 'Failed to add comment'}), 500

    @app.route('/recipe/<int:recipe_id>/comment/<int:comment_id>', methods=['DELETE'])
    def delete_comment(recipe_id, comment_id):
        if 'user' not in session:
            return jsonify({'error': 'User not logged in'}), 401

        user = RegisteredUser.get_user_by_username(session['user'])
        if not user:
            return jsonify({'error': 'User not found'}), 404

        comment = Comment.get_comment_by_id(comment_id)
        if not comment or comment['userID'] != user['userID']:
            return jsonify({'error': 'Comment not found or unauthorized'}), 404

        success = Comment.delete_comment(comment_id)
        if success:
            return jsonify({'success': True})
        return jsonify({'error': 'Failed to delete comment'}), 500

    # ----------------- ADMIN MANAGE ROUTES -----------------#
    @app.route('/adminhome')
    def adminhome():
        if session.get('role') != 'admin':
            return redirect(url_for('login'))
        
        username = session.get('user')  # Assuming the admin username is stored in the session
        admin = Admin.get_admin_by_username(username)
        
        if not admin:
            flash("Admin not found", "error")
            return redirect(url_for('login'))
        reports = Report.get_all_reports()
        notifications = Notification.get_all_notifications()

        return render_template(
            'adminhome.html',
            admin_info={
                'adminID': admin['adminID'],
                'adminName': admin['adminName'],
                'adminEmail': admin['adminEmail'],
                'adminProfilePic': admin['adminProfilePic']
            },
            reports=reports,
            notifications=notifications
        )

    @app.route('/admin/<username>')
    def get_admin(username):
        admin = Admin.get_admin_by_username(username)
        if admin:
            return {
                'adminID': admin['adminID'],
                'adminName': admin['adminName'],
                'adminEmail': admin['adminEmail'],
                'adminProfilePic': admin['adminProfilePic']
            }
        return {"error": "Admin not found"}, 404

    @app.route('/manage')
    def manage():
        users = RegisteredUser.get_all_users()
        recipes = Recipe.get_all_recipes()    
        return render_template('adminmanage.html', users=users, recipes=recipes)

    @app.route('/user/update_status/<int:user_id>', methods=['POST'])
    def update_user_status(user_id):
        new_status = request.form.get('status')
        if not new_status:
            return "Invalid status", 400

        RegisteredUser.update_user_status(user_id, new_status)
        return jsonify({"message": "User status updated successfully"}), 200
    
    @app.route('/recipe/update_status/<int:recipe_id>', methods=['POST'])
    def update_recipe_status(recipe_id):
        new_status = request.form.get('status')
        if not new_status:
            return "Invalid status", 400

        Recipe.update_recipe_status(recipe_id, new_status)
        return jsonify({"message": "Recipe status updated successfully"}), 200

    @app.route('/user/delete/<int:user_id>', methods=['POST'])
    def delete_user(user_id):
        try:
            RegisteredUser.delete_user(user_id)
            return jsonify({"message": "User deleted successfully"}), 200
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": f"Failed to delete user: {e}"}), 500
        
    @app.route('/admin/recipe/<int:id>')
    def get_recipe_admin(id):
        recipe = Recipe.get_recipe_by_id(id)
        if recipe:
            like_count = Recipe.get_recipe_like_count(id)  # Fetch the like count
            return {
                'recipeID': recipe['recipeID'],
                'recipeTitle': recipe['recipeTitle'],
                'recipeDescription': recipe['recipeDescription'],
                'recipeIngredients': recipe['recipeIngredients'],
                'recipeSteps': recipe['recipeSteps'],
                'recipePic': recipe['recipePic'],
                'recipeTime': recipe['recipeTime'],
                'recipeCalories': recipe['recipeCalories'],
                'recipeLabel': recipe['recipeLabel'],
                'recipeCuisine': recipe['recipeCuisine'],
                'recipeStatus': recipe['recipeStatus'],
                'userID': recipe['userID'],
                'likeCount': like_count,  # Include the like count in the response
            }
        return {'error': 'Recipe not found'}, 404

    @app.route('/recipe/delete/<int:recipe_id>', methods=['POST'])
    def delete_recipe(recipe_id):
        try:
            Recipe.delete_recipe(recipe_id)
            return jsonify({"message": "Recipe deleted successfully"}), 200
        except Exception as e:
            print(f"Error: {e}")
            return jsonify({"error": f"Failed to delete recipe: {e}"}), 500
        

    # ----------------- REPORT ROUTES -----------------
    @app.route('/reports')
    def reports():
        reports = Report.get_all_reports()
        return render_template('adminreport.html', reports=reports)
    
    @app.route('/report/update_status/<int:id>', methods=['POST'])
    def update_report_status(id):
        new_status = request.form.get('status')
        if not new_status:
            return "Invalid status", 400
        
        Report.update_report_status(id, new_status)
        return redirect(url_for('reports'))

    @app.route('/report/<int:report_id>')
    def get_report_details(report_id):
        report = Report.get_report_details(report_id)
        if report:
            return {
                'reportID': report['reportID'],
                'reportTitle': report['reportTitle'],
                'reportDetails': report['reportDetails'],
                'reportTime': report['reportTime'],
                'reportStatus': report['reportStatus'],
                'reportedUser': report['reportedUser'],
                'reportSenderUser': report['reportSenderUser'],
                'relatedRecipe': report['relatedRecipe']
            }
        return {'error': 'Report not found'}, 404
    
    @app.route('/report/create/<int:recipe_id>/<int:sender_id>/<int:reported_user_id>', methods=['POST'])
    def create_report(recipe_id, sender_id, reported_user_id):
        if request.method == 'POST':
            title = request.form.get('title')
            details = request.form.get('details')

            success = Report.create_report(title, details, sender_id, reported_user_id, recipe_id)
            if success:
                flash("Report created successfully", "success")
            else:
                flash("Failed to create report", "error")

        # Redirect to the appropriate recipe or report overview page
        return redirect(url_for('get_recipe', id=recipe_id))

    # ----------------- NOTIFICATION ROUTES -----------------
    @app.route('/notifications')
    def notifications():
        notifications = Notification.get_all_notifications()
        return render_template('adminnoti.html', notifications=notifications)
    
    @app.route('/notification/delete/<int:id>', methods=['POST'])
    def delete_notification(id):
        Notification.delete_notification(id)
        return redirect(url_for('notifications'))
    
    @app.route('/notification/edit/<int:id>', methods=['GET', 'POST'])
    def edit_notification(id):
        if request.method == 'POST':
            title = request.form.get('title')
            details = request.form.get('details')
            receiver = request.form.get('receiver')
            Notification.update_notification(id, title, details, receiver)
            return redirect(url_for('notifications'))
        notification = Notification.get_notification_by_id(id)
        return render_template('edit_notification.html', notification=notification)
    
    @app.route('/notification/<int:id>')
    def get_notification(id):
        notification = Notification.get_notification_by_id(id)
        if notification:
            return {
                'title': notification['notiTitle'],
                'details': notification['notiDetails'],
                'receiver': notification['notiReceiver']
            }
        return {'error': 'Notification not found'}, 404
    
    @app.route('/notification/create', methods=['POST'])
    def create_notification():
        if request.method == 'POST':
            title = request.form.get('title')
            details = request.form.get('details')
            receiver = request.form.get('receiver')
            Notification.add_notification(title, details, receiver)
            return redirect(url_for('notifications'))

    # ----------------- USER ROUTES -----------------

    @app.route('/userhome')
    def userhome():
        recipes = Recipe.get_published_recipes()
        # Handle logged-in vs. guest access
        if 'user' in session:
            user_package = session.get('userPackage')
            notifications = Notification.get_all_notifications(user_package)
        else:
            notifications = []  # No notifications for guests
        return render_template('userhome.html', recipes=recipes,  notifications=notifications)
    
    # ----------------- COLLECTION ROUTES -----------------
    @app.route('/collection')
    def collection():
        username = session.get('user')
        if not username:
            if request.headers.get('Accept') == 'application/json':  
                return jsonify({'error': 'User not logged in'}), 401  
            flash('Please log in to access your collections.', 'warning')
            return redirect(url_for('login'))

        user = RegisteredUser.get_user_by_username(username)
        if not user:
            if request.headers.get('Accept') == 'application/json':  
                return jsonify({'error': 'User not found'}), 404  
            flash('User not found. Please log in again.', 'error')
            return redirect(url_for('login'))

        user_id = user['userID']
        collections = Collection.get_collections_by_user_id(user_id)

        formatted_collections = [
            {
                'collectionID': collection['collectionID'],
                'collectionName': collection['collectionName'],
                'collectionPic': collection['collectionPic'],
                'collectionSize': collection['collectionSize']
            }
            for collection in collections
        ]

        # If request is for JSON data, return it
        if request.headers.get('Accept') == 'application/json':  
            return jsonify({'collections': formatted_collections})  

        # Otherwise, render HTML
        return render_template('collection.html', collections=formatted_collections)

    
    @app.route('/collection/<int:collection_id>/recipes')
    def get_collection_recipes(collection_id):
        recipes = Collection.get_recipes_by_collection(collection_id)
        return jsonify({'recipes': recipes})


    @app.route('/collection/create', methods=['POST'])
    def create_collection():
        username = session.get('user')
        if not username:
            return jsonify({'error': 'User not logged in'}), 401

        user = RegisteredUser.get_user_by_username(username)
        if not user:
            return jsonify({'error': 'User not found'}), 404

        user_id = user['userID']
        data = request.get_json()
        collection_name = data.get('collectionName')

        if not collection_name:
            return jsonify({'error': 'Collection name is required'}), 400

        result = Collection.create_collection(user_id, collection_name)
        if result:
            return jsonify({'message': 'Collection created successfully'}), 200
        else:
            return jsonify({'error': 'Failed to create collection'}), 500


    @app.route('/recipe/<int:recipe_id>/collection', methods=['POST'])
    def save_recipe_to_collection(recipe_id):
        data = request.json
        collection_id = data.get('collectionID')

        if not collection_id:
            return jsonify({'error': 'Collection ID is required'}), 400

        print(f"Adding recipe {recipe_id} to collection {collection_id}")  # Debugging

        success = Collection.add_recipe_to_collection(collection_id, recipe_id)

        if success:
            print(f"Successfully added recipe {recipe_id} to collection {collection_id}")  # Debugging
            return jsonify({'success': True})
        else:
            print(f"Failed to add recipe {recipe_id} to collection {collection_id}")  # Debugging
            return jsonify({'error': 'Failed to add recipe to collection'}), 500

        
    
    # ----------------- SEARCH ROUTES -----------------

    @app.route('/search', methods=['GET'])
    def search():
        query = request.args.get('q', '').strip()

        if not query:
            return jsonify([])  # Return an empty list if no query

        recipe = Recipe.search_recipe(query)  # Call a method from Recipe to handle search
        return jsonify(recipe)
    
    # ----------------- FILTER ROUTES -----------------

    @app.route('/filter', methods=['POST'])
    def filter_recipe():
        print("Received a request!")  # Debugging print
        data = request.json
        print("Request data:", data)  # Debugging print
        cuisines = data.get('cuisines', [])
        labels = data.get('labels', [])

        filters = data.get('filters', [])  # Combined filters (e.g., ["Italian", "Breakfast"])


        conn = DatabaseManager.get_db()
        cursor = conn.cursor()

        # Build the query dynamically based on filters
        query = "SELECT * FROM recipe WHERE 1=1"
        params = []

        if cuisines:
            placeholders = ','.join(['?'] * len(cuisines))  
            query += f" AND LOWER(recipeCuisine) IN ({placeholders})"
            params.extend([c.lower() for c in cuisines])

        if labels:
            placeholders = ','.join(['?'] * len(labels))
            query += f" AND LOWER(recipeLabeL) IN ({placeholders})"
            params.extend([l.lower() for l in labels])

        print("Executing query:", query)  # 🔍 Debugging: Print the final SQL query
        print("With parameters:", params)  # 🔍 Debugging: Check parameter values

        cursor.execute(query, params)
        recipes = cursor.fetchall()

        print("Recipes found:", [dict(recipe) for recipe in recipes])

        return jsonify([dict(recipe) for recipe in recipes])
    
    # ----------------- SORT BY ROUTES -----------------
    @app.route('/sort', methods=['POST'])
    def sort_recipes():
        data = request.json
        sort_by = data.get("sort_by")  # Default sort by time
        order = data.get("order", "asc")  # Default to ascending order

        print(f"Received sorting request: sort_by={sort_by}, order={order}")  # Debugging

        # Map valid sorting fields to database columns
        valid_fields = {
            "title": "recipeTitle",
            "time": "recipeTime",
            "calories": "recipeCalories"
        }

        # Validate and get the database column for sorting
        sort_column = valid_fields.get(sort_by)
        if not sort_column:
            print(f"Invalid or missing sort_by value received: {sort_by}")  # Debugging
            return jsonify({"error": "Invalid sorting field."}), 400

        # Ensure the order is either ASC or DESC
        order = "ASC" if order.lower() == "asc" else "DESC"

        # Construct the query dynamically
        query = f"""
            SELECT recipeID, recipeTitle, recipePic, recipeDescription, recipeTime, recipeCalories, recipeCuisine
            FROM recipe
            ORDER BY {sort_column} {order}
        """

        try:
            # Use the existing DatabaseManager to execute the query
            conn = DatabaseManager.get_db()
            cursor = conn.cursor()
            cursor.execute(query)
            recipes = cursor.fetchall()
            conn.close()

        except Exception as e:
            print(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred."}), 500

        # Convert the database rows to a list of dictionaries
        recipes_list = [
            {
                "recipeID": recipe["recipeID"],
                "recipeTitle": recipe["recipeTitle"],
                "recipePic": recipe["recipePic"],
                "recipeDescription": recipe["recipeDescription"],
                "recipeTime": recipe["recipeTime"],
                "recipeCalories": recipe["recipeCalories"],
                "recipeCuisine": recipe["recipeCuisine"]
            }
            for recipe in recipes
        ]

        return jsonify(recipes_list)
    
    @app.route('/profile/change_password', methods=['POST'])
    def change_password():
        if 'user' not in session:
            return "<script>alert('Please log in to change your password.'); window.location.href = '/login';</script>"

        username = session['user']
        user = RegisteredUser.get_user_by_username(username)

        current_password = request.form.get('currentPassword')
        new_password = request.form.get('newPassword')

        if user and user['userPassword'] == current_password:
            success = RegisteredUser.update_password(user['userID'], new_password)
            if success:
                return "<script>alert('Password changed successfully!'); window.location.href = '/profile';</script>"
            else:
                return "<script>alert('Failed to change password. Try again.'); window.location.href = '/profile';</script>"
        else:
            return "<script>alert('Current password is incorrect.'); window.location.href = '/profile';</script>"
    
    return app