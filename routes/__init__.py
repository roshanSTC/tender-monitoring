"""
Routes package initialization.
Exports all API route blueprints.
"""

from routes.admin_dashboard import admin_dashboard_bp
from routes.admin_users import admin_users_bp
from routes.auth import auth_bp
from routes.corrigendums import corrigendum_bp
from routes.dashboard import dashboard_bp
from routes.notifications import notifications_bp
from routes.preferences import preferences_bp
from routes.tenders import tenders_bp

__all__ = [
    "admin_dashboard_bp",
    "admin_users_bp",
    "auth_bp",
    "corrigendum_bp",
    "dashboard_bp",
    "notifications_bp",
    "preferences_bp",
    "tenders_bp",
]
