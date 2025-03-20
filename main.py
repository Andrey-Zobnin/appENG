#!/usr/bin/env python3
# This file serves as the entry point for the Flask application
# It imports and runs the application from run.py

from run import app

# The application will be started automatically by Gunicorn
# No need to call app.run() here

if __name__ == "__main__":
    # This block will only be executed when the file is run directly
    # It won't be executed when imported by Gunicorn
    app.run(host='0.0.0.0', port=5000, debug=True)