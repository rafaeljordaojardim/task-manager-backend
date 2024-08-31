from flask import Flask
from flask_pymongo import PyMongo
import os
from flask_cors import CORS
import secrets
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

def get_app_with_config(config):
    app.config.from_object(config)
    mongo = PyMongo(app)
    app.secret_key = secrets.token_urlsafe(32)  # Important for session security
    # Initialize limiter AFTER loading config
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=app.config.get('RATELIMIT_DEFAULT', ["200 per day", "50 per hour"]),  # Get default from config
        storage_uri="memory://",
    )

    from app import main
    # Call the function to create routes AFTER app is initialized
    main.create_routes(app, mongo, limiter) 
    return app, mongo, limiter

