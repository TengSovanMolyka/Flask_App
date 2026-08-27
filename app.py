import os
from flask import Flask, session
from config import Config
from extensions import db, migrate

from models import (
    User,
    Order,
    OrderItem,
)
from routes.front import (
    front_bp,
    auth_bp,
    account_bp,
    cart_bp,
    orders_bp,
)

from routes.admin import (
    admin_users_bp,
    admin_orders_bp,
    admin_auth_bp,
    admin_dashboard_bp,
)

def create_app():
    app = Flask(__name__)

    # ==========================================
    # Configuration
    # ==========================================
    app.config.from_object(Config)

    # ==================================================
    # WISHLIST COUNT
    # ==================================================

    @app.context_processor
    def inject_wishlist_count():
        wishlist = session.get("wishlist", [])

        return {
            "wishlist_count": len(wishlist)
        }

    # ==========================================
    # Extensions
    # ==========================================
    db.init_app(app)
    migrate.init_app(app, db)

    # ==========================================
    # Ensure upload folder exists
    # ==========================================
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register Blueprints
    # ==========================================
    # Front Routes
    # ==========================================
    app.register_blueprint(front_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)



    # ==========================================
    # Admin Routes
    # ==========================================
    app.register_blueprint(admin_auth_bp)
    app.register_blueprint(admin_dashboard_bp)
    app.register_blueprint(admin_users_bp)
    app.register_blueprint(admin_orders_bp)


    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
