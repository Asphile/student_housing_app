# PythonAnywhere WSGI configuration for Student Housing App

import sys
import os

# Add the project directory to the sys.path
project_home = '/home/asiphile/student_housing_app'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure key
os.environ['FLASK_ENV'] = 'production'

# Import the Flask application
from app import create_app
application = create_app()

# Optional: Log that the app loaded
print("Flask app loaded successfully")