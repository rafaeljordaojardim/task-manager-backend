from flask import jsonify, request, session
from app.models import User, JWT, Task
from functools import wraps
from datetime import datetime



# JWT Configuration
ACCESS_TOKEN_EXPIRY_SECONDS = 3600  # 1 hour
REFRESH_TOKEN_EXPIRY_SECONDS = 604800  # 7 days

def create_routes(app, mongo, limiter):
    JWT_SECRET_KEY = app.secret_key

    """Define your Flask routes here."""
    @app.route('/api/auth/signup', methods=['POST'])
    @limiter.limit("20/minute")
    def signup():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400

        if User.find_by_username(mongo.db, username):
            return jsonify({'message': 'Username already exists'}), 409

        User.create_user(mongo.db, username, password)
        return jsonify({'message': 'User created successfully' }), 201

    @app.route('/api/auth/login', methods=['POST'])
    @limiter.limit("20/minute")
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        user = User.find_by_username(mongo.db, username)

        if user and user.check_password(password):
            access_token = JWT.generate_jwt(user._id, JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRY_SECONDS)
            refresh_token = JWT.generate_jwt(user._id, JWT_SECRET_KEY, REFRESH_TOKEN_EXPIRY_SECONDS)

            user.add_refresh_token(mongo.db, refresh_token)

            return jsonify({
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user.username
            }), 200
        else:
            return jsonify({'message': 'Invalid username or password'}), 401

    @app.route('/api/auth/refresh', methods=['POST'])
    def refresh():
        """
        Endpoint to refresh the access token using the refresh token.
        """
        refresh_token = request.headers.get('Authorization').split(" ")[1]
        if not refresh_token:
            return jsonify({'message': 'Refresh token is missing'}), 401

        data = JWT.decode_jwt(refresh_token, JWT_SECRET_KEY)

        if data is None:
            return jsonify({'message': 'Invalid refresh token'}), 401

        current_user = User.find_one(mongo.db, data['sub'])
        if not current_user or not current_user.has_refresh_token(mongo.db, refresh_token):
            return jsonify({'message': 'Invalid refresh token'}), 401

        access_token = JWT.generate_jwt(current_user._id, JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRY_SECONDS)
        return jsonify({'access_token': access_token}), 200

    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        """
        Endpoint to logout the access token using the refresh token.
        """
        refresh_token = request.headers.get('Authorization').split(" ")[1]
        if not refresh_token:
            return jsonify({'message': 'Refresh token is missing'}), 401

        data = JWT.decode_jwt(refresh_token, JWT_SECRET_KEY)

        if data is None:
            return jsonify({'message': 'Invalid refresh token'}), 401

        current_user = User.find_one(mongo.db, data['sub'])
        if not current_user:
            return jsonify({'message': 'User not found'}), 404

        current_user.remove_refresh_token(mongo.db, refresh_token)
        return jsonify({}), 200


    # Decorator to protect routes with JWT
    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            if 'Authorization' in request.headers:
                token = request.headers['Authorization'].split(" ")[1]
            if not token:
                return jsonify({'message': 'Token is missing'}), 401
            
            data = JWT.decode_jwt(token, JWT_SECRET_KEY)
        
            if data is None:
                return jsonify({'message': 'Token is expired'}), 401

            current_user = User.find_one(mongo.db, data['sub'])
            return f(current_user, *args, **kwargs)
        return decorated

    @app.route('/api/auth/revoke_all', methods=['POST'])
    @token_required  # Assuming you have the token_required decorator
    def revoke_all_tokens(current_user):
        """
        Endpoint to revoke all refresh tokens for a user.
        This is typically used when a user changes their password.
        """
        current_user.remove_refresh_tokens(mongo.db)
        return jsonify({'message': 'All refresh tokens revoked'}), 200

    # Example protected route
    @app.route('/api/protected')
    @token_required
    @limiter.limit("20/minute")
    def protected(current_user):
        return jsonify({'message': str(current_user._id)}), 200

    @app.route('/api/tasks', methods=['POST'])
    @token_required
    @limiter.limit("20/minute")
    def create_task(current_user):
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        due_date_str = data.get('dueDate')  # Add due date
        if not title:
            return jsonify({'message': 'Task title is required'}), 400

        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d')
            except ValueError:
                return jsonify({'message': 'Invalid due date format. Use YYYY-MM-DD.'}), 400
        else:
            return jsonify({'message': 'Due date required.'}), 400
        task = Task.create_task(mongo.db, title, description, due_date, current_user._id)
        return jsonify({'message': 'Task created', 'task_id': str(task._id)}), 201

    @app.route('/api/tasks', methods=['GET'])
    @token_required
    @limiter.limit("20/minute")
    def get_tasks(current_user):
        tasks = Task.find_by_user_id(mongo.db, current_user._id)
        task_list = []
        for task in tasks:
            task_data = {
                'id': str(task._id),
                'title': task.title,
                'description': task.description,
                'status': task.status
            }
            if task.due_date:
                task_data['dueDate'] = task.due_date.strftime('%Y-%m-%d')
            task_list.append(task_data)
        return jsonify(task_list), 200

    @app.route('/api/tasks/<task_id>', methods=['GET'])
    @token_required
    @limiter.limit("20/minute")
    def get_task(current_user, task_id):
        task = Task.find_one(mongo.db, task_id)
        if task and task.user_id == current_user._id:
            task_data = {'id': str(task._id), 'title': task.title, 'description': task.description, 'status': task.status}
            if task.due_date:
                task_data['dueDate'] = task.due_date.strftime('%Y-%m-%d')
            return jsonify(task_data), 200
        else:
            return jsonify({'message': 'Task not found'}), 404

    @app.route('/api/tasks/<task_id>', methods=['PUT'])
    @token_required
    @limiter.limit("20/minute")
    def update_task(current_user, task_id):
        task = Task.find_one(mongo.db, task_id)
        if task and task.user_id == current_user._id:
            data = request.get_json()
            due_date_str = data.get('dueDate')

            # Validate and update due date
            if due_date_str:
                try:
                    data['due_date'] = datetime.strptime(due_date_str, '%Y-%m-%d')
                except ValueError:
                    return jsonify({'message': 'Invalid due date format. Use YYYY-MM-DD.'}), 400
            else:
                data['due_date'] = None  # Clear due date if not provided

            task.update(mongo.db, **data)
            return jsonify({'message': 'Task updated'}), 200
        else:
            return jsonify({'message': 'Task not found'}), 404

    @app.route('/api/tasks/<task_id>', methods=['DELETE'])
    @token_required
    @limiter.limit("20/minute")
    def delete_task(current_user, task_id):
        task = Task.find_one(mongo.db, task_id)
        if task and task.user_id == current_user._id:
            task.delete(mongo.db)
            return jsonify({'message': 'Task deleted'}), 200
        else:
            return jsonify({'message': 'Task not found'}), 404
