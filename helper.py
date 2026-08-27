import json, os, requests
from config import Config
from flask import current_app, request
from werkzeug.utils import secure_filename
from product import get_product_by_id


def send_order_to_telegram(order):
    """Send a newly-created SQLAlchemy Order to Telegram."""

    telegram_token = current_app.config.get("TELEGRAM_TOKEN")
    chat_id = current_app.config.get("TELEGRAM_CHAT_ID")

    if not telegram_token or not chat_id:
        print("Telegram notification skipped: Telegram configuration is missing.")
        return False

    exchange_rate = current_app.config.get("EXCHANGE_RATE", 4100)

    message = f"""
🛒 *NEW ORDER RECEIVED*

━━━━━━━━━━━━━━━

📦 *Order ID:* `{order.order_id}`

👤 *Customer Information*
• Name: {order.customer_name}
• Phone: {order.phone}
• Email: {order.email}

📍 *Delivery Address*
{order.address}

💳 *Payment Method:* {order.payment_method.upper()}

━━━━━━━━━━━━━━━

🛍 *ORDER ITEMS*
"""

    for index, item in enumerate(order.items, start=1):
        line_total = item.discounted_price * item.quantity
        size_text = f" ({item.size})" if item.size else ""
        message += (
            f"\n{index}. *{item.title}{size_text} x {item.quantity}*\n"
            f"   Total: ${line_total:.2f}\n"
        )

    shipping_text = "FREE" if order.shipping == 0 else f"${order.shipping:.2f}"

    message += f"""
━━━━━━━━━━━━━━━

💰 *ORDER SUMMARY*

Subtotal: ${order.subtotal:.2f}
Shipping: {shipping_text}
*Grand Total:* ${order.total:.2f} | ៛{order.total * exchange_rate:,.0f}

━━━━━━━━━━━━━━━

🕒 *Status:* {order.status}

🌸 *LA BEAUTÉ STUDIO* 🌸
Thank you for your order.
"""

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

    try:
        response = requests.post(
            url,
            data={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=5,
        )
        print("Telegram Status:", response.status_code)
        return response.ok
    except Exception as e:
        print("Telegram Error:", e)
        return False

# ==========================================================
# FILE UPLOAD
# ==========================================================
def allowed_file(filename: str) -> bool:
    """Check whether an uploaded file has an allowed extension."""
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in current_app.config["ALLOWED_EXTENSIONS"]


def upload_profile(profile) -> str:
    """Save a profile image and return its filename."""
    if not profile or not profile.filename:
        return "default-avatar.png"
    if not allowed_file(profile.filename):
        return "default-avatar.png"

    filename = secure_filename(profile.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(upload_folder, filename)
    profile.save(filepath)

    return filename


# ==========================================================
# CART
# ==========================================================
def get_cart_items() -> list:
    """
    Read cart items from the cart_list cookie.
    Returns an empty list when the cookie does not exist
    or contains invalid JSON.
    """
    cart_cookie = request.cookies.get("cart_list")
    if not cart_cookie:
        return []

    try:
        cart_items = json.loads(cart_cookie)
        return cart_items if isinstance(cart_items, list) else []
    except (json.JSONDecodeError, TypeError):
        return []


def calculate_shipping(subtotal: float) -> int:
    """
    Calculate shipping cost based on subtotal.
    $0       -> $0
    < $100   -> $5
    < $300   -> $3
    >= $300  -> FREE
    """
    if subtotal == 0:
        return 0
    if subtotal < 100:
        return 5
    if subtotal < 300:
        return 3
    return 0


def get_cart_data() -> dict:
    """
    Build complete cart information.
    Returns: cart_products, subtotal, total_items, shipping
    """
    cart_products = get_cart_items()
    subtotal, total_items = 0, 0
    valid_cart_products = []

    for item in cart_products:
        product_id = item.get("_id")
        quantity = item.get("qty", 1)

        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            quantity = 1
        if quantity < 1:
            quantity = 1

        product = get_product_by_id(product_id)
        if not product:
            continue

        # Update product info
        item.update({
            "_id": product["_id"],
            "title": product["title"],
            "category": product["category"],
            "price": product["price"],
            "brand": product["brand"],
            "image": product["image"],
            "qty": quantity,
            "stock": product.get("stock", 0),
            "discountedPrice": product.get("discountedPrice", product["price"]),
        })

        # Prevent exceeding stock
        if item["stock"] <= 0:
            continue
        if item["qty"] > item["stock"]:
            item["qty"] = item["stock"]

        # Totals
        subtotal += item["discountedPrice"] * item["qty"]
        total_items += item["qty"]

        valid_cart_products.append(item)

    shipping = calculate_shipping(subtotal)

    return {
        "cart_products": valid_cart_products,
        "subtotal": subtotal,
        "total_items": total_items,
        "shipping": shipping,
    }

