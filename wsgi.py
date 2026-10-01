"""
wsgi.py

Production WSGI entrypoint for Gunicorn, uWSGI, or Azure/AWS/Docker containers.
Usage:
    gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app
"""

from app import app

if __name__ == "__main__":
    app.run()
