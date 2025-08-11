# This is the main Flask application file for PythonAnywhere deployment
# PythonAnywhere expects a file named flask_app.py in your main directory

import sys
import os

# Add your project directory to the Python path
mysite_path = '/home/yourusername/mysite'  # You'll need to update this path
if mysite_path not in sys.path:
    sys.path.append(mysite_path)

# Import your Flask app
from app import app as application

# Make sure we set the secret key for production
if not application.secret_key:
    application.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this')

if __name__ == "__main__":
    application.run()