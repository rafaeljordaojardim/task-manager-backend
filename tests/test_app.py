import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import app, mongo
from bson import ObjectId
import pymongo
class TestAPI:

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up for test methods."""
        test_db_uri = "mongodb://mongo-test:27017/test_database"  # URI for your test database
        test_client = pymongo.MongoClient(test_db_uri)
        self.db = test_client.test_database  # Access the test database
        self.client = app.test_client()
        self.db.users.delete_many({})  # Clear users collection before each test
        self.db.tasks.delete_many({})  # Clear tasks collection before each test

    def test_signup(self):
        """Test user signup."""
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post('/api/signup', json=data)
        assert response.status_code == 201
        assert 'User created successfully' in response.json['message']

    def test_signup_existing_user(self):
        """Test signup with an existing username."""
        data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/signup', json=data)  # Create the user first
        response = self.client.post('/api/signup', json=data)  # Try to create again
        assert response.status_code == 409
        assert 'Username already exists' in response.json['message']

    def test_login_and_get_tasks(self):
        """Test user login and retrieving tasks."""
        # 1. Signup a new user
        signup_data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/signup', json=signup_data)

        # 2. Login the user
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        login_response = self.client.post('/api/login', json=login_data)
        assert login_response.status_code == 200
        access_token = login_response.json['access_token']

        # 3. Create a task (using the access token)
        task_data = {'title': 'Test Task', 'description': 'This is a test task'}
        create_response = self.client.post(
            '/api/tasks', 
            json=task_data, 
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert create_response.status_code == 201

        # 4. Get tasks (using the access token)
        get_response = self.client.get(
            '/api/tasks', 
            headers={'Authorization': f'Bearer {access_token}'}
        )
        assert get_response.status_code == 200
        assert len(get_response.json) == 1  # Check if one task is returned
        assert get_response.json[0]['title'] == 'Test Task'

# ... Add more tests for other endpoints (get_task, update_task, delete_task) ...
