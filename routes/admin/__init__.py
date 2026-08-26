from routes.admin.users import admin_users_bp
from routes.admin.orders import admin_orders_bp

from routes.admin.auth import admin_auth_bp
from routes.admin.dashboard import admin_dashboard_bp


__all__ = [
    "admin_users_bp",
    "admin_orders_bp",
    "admin_auth_bp",
    "admin_dashboard_bp",
]
