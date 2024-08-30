from flask import Flask
from flask_pymongo import PyMongo
import os
from flask_cors import CORS
import secrets

app = Flask(__name__)
app.config["MONGO_URI"] = os.environ.get('MONGO_URI', "mongodb://mongo:27017/mydatabase")
CORS(app, origins=['http://localhost:4200'], methods=['GET', 'POST', 'PUT', 'DELETE'], supports_credentials=True)

mongo = PyMongo(app)
app.secret_key = secrets.token_urlsafe(32)  # Important for session security

from app import main


# Call the function to create routes AFTER app is initialized
main.create_routes(app, mongo) 
