from bson import ObjectId
import bcrypt
import jwt
import datetime
import sys
class User:
    def __init__(self, username, password, _id=None, refresh_tokens=None):
        self.username = username
        self.password = password
        self._id = _id
        self.refresh_tokens = refresh_tokens if refresh_tokens else []

    @staticmethod
    def create_user(db, username, password):  # Pass db here
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_id = db.users.insert_one({"username": username, "password": hashed_password, "refresh_tokens": [] }).inserted_id
        return user_id

    @staticmethod
    def find_by_username(db, username):  # Pass db here
        user_data = db.users.find_one({"username": username})
        print(user_data, file=sys.stderr)
        if user_data:
            return User(user_data.get("username"), user_data.get("password"), user_data.get('_id'), user_data.get('refresh_tokens'))  # Pass db
        return None

    @staticmethod
    def find_one(db, user_id):  # Pass db here
        objectId= ObjectId(user_id)
        user_data = db.users.find_one({"_id": objectId})
        print(user_data, file=sys.stderr)
        if user_data:
            return User(user_data["username"], user_data["password"], user_data["_id"], user_data.get('refresh_tokens'))  # Pass db
        return None

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)
    
    def add_refresh_token(self, db, token):
        hashed_token = bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt())
        self.refresh_tokens.append(hashed_token)
        db.users.update_one({"_id": self._id}, {"$set": {"refresh_tokens": self.refresh_tokens}})

    def remove_refresh_token(self, db, token):
        if token in self.refresh_tokens:
            self.refresh_tokens.remove(token)
            db.users.update_one({"_id": self._id}, {"$set": {"refresh_tokens": self.refresh_tokens}})
    
    def remove_refresh_tokens(self, db):
        db.users.update_one({"_id": self._id}, {"$set": {"refresh_tokens": []}})

    def has_refresh_token(self, db, token):
        for stored_token in self.refresh_tokens:
            if bcrypt.checkpw(token.encode('utf-8'), stored_token):
                return True
        return False
    

class Task:
    def __init__(self, title, description, user_id, due_date=None, status="pending", _id=None):
        self.title = title
        self.description = description
        self.user_id = user_id  # Store the ID of the user who owns this task
        self.status = status
        self._id = _id
        self.due_date = due_date

    @staticmethod
    def create_task(db, title, description,due_date, user_id):
        task = Task(title, description, user_id, due_date)
        task_id = db.tasks.insert_one({
            "title": title, 
            "description": description,
            "user_id": user_id,
            "status": task.status,
            "due_date": task.due_date
        }).inserted_id
        task._id = task_id
        return task

    @staticmethod
    def find_by_user_id(db, user_id):
        tasks = list(db.tasks.find({"user_id": user_id}))
        return [Task(**task) for task in tasks]

    @staticmethod
    def find_one(db, task_id):
        task_data = db.tasks.find_one({"_id": ObjectId(task_id)})
        if task_data:
            return Task(**task_data)
        return None

    def update(self, db, **kwargs):
        update_data = {k: v for k, v in kwargs.items() if hasattr(self, k)}
        db.tasks.update_one({"_id": self._id}, {"$set": update_data})

    def delete(self, db):
        db.tasks.delete_one({"_id": self._id})

class JWT:

    @staticmethod
    def generate_jwt(user_id, secret_key, expires_in=3600):  # Default expiry: 1 hour
        """Generates a JWT for this user."""
        payload = {
            'sub': str(user_id),  # User ID as the subject
            'iat': datetime.datetime.utcnow(),  # Issued at time
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')

    @staticmethod
    def decode_jwt(token, secret_key):
        try:
            data = jwt.decode(token, secret_key, algorithms='HS256')
            return data
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        return None
