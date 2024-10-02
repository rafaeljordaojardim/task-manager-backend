import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import get_app_with_config
from bson import ObjectId
import mongomock
from app import config 
from flask_pymongo import PyMongo
from flask_limiter.util import get_remote_address
import time

app, mongo, limiter = get_app_with_config(config.TestConfig)

@pytest.fixture
def client():
    """
    This fixture creates a test client for your Flask app and configures
    it to use a `mongomock` database for testing. 
    """
    with app.app_context():
        mongo.db = mongomock.MongoClient().db
        yield app.test_client(), mongo, limiter # Yield the test client

class TestAPI:

    @pytest.fixture(autouse=True)
    def setup(self, client):
        """
        This setup fixture will run before each test function.
        It clears the test database collections.
        """
        self.client, self.mongo, self.limiter = client  # Unpack the client and mongo
        self.db = self.mongo.db           # Access the database from mongo
        self.db.users.delete_many({})  
        self.db.tasks.delete_many({})

    def test_signup(self):
        """Test user signup."""
        data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post('/api/auth/signup', json=data)
        assert response.status_code == 201
        assert 'User created successfully' in response.json['message']

    def test_signup_existing_user(self):
        """Test signup with an existing username."""
        data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/auth/signup', json=data)  # Create the user first
        response = self.client.post('/api/auth/signup', json=data)  # Try to create again
        assert response.status_code == 409
        assert 'Username already exists' in response.json['message']

    def test_login_and_get_tasks(self):
        """Test user login and retrieving tasks."""
        # 1. Signup a new user
        signup_data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/auth/signup', json=signup_data)

        # 2. Login the user
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        login_response = self.client.post('/api/auth/login', json=login_data)
        assert login_response.status_code == 200
        access_token = login_response.json['access_token']

        # 3. Create a task (using the access token)
        task_data = {"title":"test","description":"test","status":"pending","user_id":"","dueDate":"2024-09-06"}
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
        assert get_response.json[0]['title'] == 'test'

    def test_rate_limit_signup(self):
        """Test rate limiting on the /api/signup route."""
        # Simulate a request context for rate limiting OUTSIDE the loop
        for i in range(20):
            signup_data = {'username': 'testuser1', 'password': 'testpassword'}
            response = self.client.post('/api/auth/signup', json=signup_data)

        signup_data = {'username': 'testuser1', 'password': 'testpassword'}
        response = self.client.post('/api/auth/signup', json=signup_data)
        assert response.status_code == 429             

        # # Wait for a minute for the rate limit to reset
        time.sleep(61)  # Ensure enough delay

        # Simulate another request context after the delay
        with app.test_request_context('/api/auth/signup', method='POST'):
            # Set a fake remote address for testing
            app.config['RATELIMIT_KEY_FUNC'] = lambda: '127.0.0.1'
            signup_data = {'username': 'testuser4', 'password': 'testpassword'}
            # The next request after the rate limit reset should succeed
            with self.limiter.limit("1/minute"):
                response = self.client.post('/api/auth/signup', json=signup_data)
                assert response.status_code == 201
# ... Add more tests for other endpoints (get_task, update_task, delete_task) ...
