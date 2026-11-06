import json, os, requests

from config import Config
from flask import current_app, request
from werkzeug.utils import secure_filename

# from product import get_product_by_id
from models.product import Product
from product import products as old_products
from extensions import db

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


# ==========================================================
# PRODUCT HELPERS: DATABASE + product.py SAMPLE PRODUCTS
# ==========================================================

# Reserve a separate ID range for the sample products in product.py.
# Database product IDs remain unchanged.
LEGACY_PRODUCT_ID_BASE = 1_000_000_000

def _to_float(value, default=0.0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def normalize_legacy_product(product, index):
    """Convert one product.py dictionary into the common storefront shape."""
    raw_id = product.get("_id", index)
    try:
        raw_id = int(raw_id)
    except (TypeError, ValueError):
        raw_id = index

    price = _to_float(product.get("price"), 0.0)
    image = product.get("image") or product.get("thumbnail") or ""
    return {
        "_id": LEGACY_PRODUCT_ID_BASE + raw_id,
        "id": LEGACY_PRODUCT_ID_BASE + raw_id,
        "source": "legacy",
        "source_id": raw_id,
        "title": product.get("title") or product.get("name") or "Untitled product",
        "name": product.get("title") or product.get("name") or "Untitled product",
        "isNew": bool(product.get("isNew", product.get("is_new", False))),
        "is_new": bool(product.get("isNew", product.get("is_new", False))),
        "oldPrice": _to_float(product.get("oldPrice", product.get("old_price")), None),
        "old_price": _to_float(product.get("oldPrice", product.get("old_price")), None),
        "price": price,
        "discountedPrice": _to_float(product.get("discountedPrice", product.get("discounted_price")), price),
        "discounted_price": _to_float(product.get("discountedPrice", product.get("discounted_price")), price),
        "description": product.get("description") or "",
        "category": product.get("category") or "Uncategorized",
        "category_id": None,
        "type": product.get("type") or "",
        "stock": int(product.get("stock") or 0),
        "brand": product.get("brand") or "",
        "size": product.get("size") or [],
        "image": image,
        "thumbnail": image,
        "images": [image] if image else [],
        "rating": _to_float(product.get("rating"), 0.0),
    }

def product_to_dict(product):
    """Convert a SQLAlchemy Product into the same shape as product.py data."""
    image_names = [image.name for image in (product.images or []) if image.name]
    main_image = product.thumbnail or (image_names[0] if image_names else "")
    category_name = product.category.name if product.category else "Uncategorized"
    price = _to_float(product.price, 0.0)
    old_price = _to_float(product.old_price, None)
    discounted_price = _to_float(product.discounted_price, price)
    return {
        "_id": product.id,
        "id": product.id,
        "source": "database",
        "source_id": product.id,
        "title": product.name or "Untitled product",
        "name": product.name or "Untitled product",
        "isNew": bool(product.is_new),
        "is_new": bool(product.is_new),
        "oldPrice": old_price,
        "old_price": old_price,
        "price": price,
        "discountedPrice": discounted_price,
        "discounted_price": discounted_price,
        "cost": _to_float(product.cost, None),
        "description": product.description or "",
        "category": category_name,
        "category_id": product.category_id,
        "type": product.type or "",
        "stock": int(product.stock or 0),
        "brand": product.brand or "",
        "size": product.size or [],
        "image": main_image,
        "thumbnail": main_image,
        "images": image_names or ([main_image] if main_image else []),
        "rating": _to_float(product.rating, 0.0),
    }

def get_all_store_products():
    """Return products from both product.py and the SQLAlchemy database."""
    legacy = [
        normalize_legacy_product(item, index)
        for index, item in enumerate(old_products, start=1)
    ]
    database = [
        product_to_dict(item)
        for item in Product.query.order_by(Product.id.desc()).all()
    ]
    # Keep database products first, followed by the original sample products.
    return database + legacy

def get_all_products():
    """Backward-compatible alias for the combined storefront product list."""
    return get_all_store_products()

def get_product_by_id(product_id):
    """Find a product from either source using its storefront ID."""
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return None

    if product_id >= LEGACY_PRODUCT_ID_BASE:
        legacy_id = product_id - LEGACY_PRODUCT_ID_BASE
        for index, item in enumerate(old_products, start=1):
            try:
                item_id = int(item.get("_id", index))
            except (TypeError, ValueError):
                item_id = index
            if item_id == legacy_id:
                return normalize_legacy_product(item, index)
        return None

    product = db.session.get(Product, product_id)
    return product_to_dict(product) if product else None

def get_products_by_category(category, current_id=None, limit=8):
    """Find related products across both sources."""
    category_text = (category or "").strip().lower()
    results = [
        item for item in get_all_store_products()
        if (item.get("category") or "").strip().lower() == category_text
        and item.get("_id") != current_id
    ]
    return results[:limit]

def decrease_product_stock(product_id, quantity):
    """Decrease stock for either a database product or a product.py sample."""
    product = get_product_by_id(product_id)
    if not product:
        return False

    quantity = max(int(quantity or 0), 0)
    if product["stock"] < quantity:
        return False

    if product["source"] == "database":
        record = db.session.get(Product, product["source_id"])
        if not record:
            return False
        record.stock = max(0, int(record.stock or 0) - quantity)
    else:
        legacy_id = product["source_id"]
        for index, item in enumerate(old_products, start=1):
            try:
                item_id = int(item.get("_id", index))
            except (TypeError, ValueError):
                item_id = index
            if item_id == legacy_id:
                item["stock"] = max(0, int(item.get("stock", 0)) - quantity)
                break
    return True
