# Task Manager API - Backend
This repository contains the backend code for a simple task manager application. It provides a RESTful API built with Flask that allows users to:

* Sign up and log in to manage their tasks.
* Create, read, update, and delete tasks.
* Assign due dates to tasks.
* Technologies Used
* Flask: Python web framework for building the API.
* PyMongo: Python driver for interacting with MongoDB.
* MongoDB: NoSQL database for storing user data and tasks.
* JWT (JSON Web Tokens): For user authentication and authorization.
* bcrypt: For password hashing.
* Flask-Limiter: For rate limiting API requests.
* Flask-CORS: For enabling Cross-Origin Resource Sharing.

## Project Structure

backend/
├── app/
│   ├── __init__.py        # Flask app initialization
│   ├── config.py         # Configuration settings
│   ├── main.py           # API route definitions
│   └── models.py          # Data models (User, Task)
└── ...

## Installation

1. Clone the repository:
```git clone https://github.com/rafaeljordaojardim/task-manager-backend.git```
```cd task-manager-backend```

2. Create a virtual environment (recommended):
```python3 -m venv venv```
```source venv/bin/activate```

3. Install dependencies:
```pip install -r requirements.txt```

## Configuration

1. Create a config.py file:
Create a config.py file in the backend/app/ directory and add your MongoDB connection details:
class RunConfig:
    MONGO_HOST = 'your_mongo_host'
    MONGO_PORT = 27017
    MONGO_DBNAME = 'your_database_name'
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DBNAME}"

2. Set up environment variables (optional):
You can store sensitive information like your JWT secret key in environment variables.

## Running the Application

1. Start the docker compose development server:

docker compose up

This will start the server at http://127.0.0.1:5000/ by default.


## Running tests

docker compose -f docker-compose.test.yml up --abort-on-container-exit web --build