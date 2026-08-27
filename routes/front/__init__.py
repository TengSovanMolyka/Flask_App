from routes.front.home import front_bp
from routes.front.user_auth import auth_bp
from routes.front.account import account_bp
from routes.front.cart import cart_bp
from routes.front.orders import orders_bp
from routes.front.wishlist import wishlist


__all__ = [
    "front_bp",
    "auth_bp",
    "account_bp",
    "cart_bp",
    "orders_bp",
    "wishlist",
]