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
# PRODUCT DATABASE HELPERS
# ==========================================================
def product_to_dict(product):
    """
    Convert the new Product SQLAlchemy model
    into the dictionary format used by the existing frontend.
    """

    # Product images
    image_names = []

    if product.images:
        image_names = [
            image.name
            for image in product.images
            if image.name
        ]

    # Fallback to thumbnail
    if not image_names and product.thumbnail:
        image_names = [product.thumbnail]

    # Main image
    main_image = product.thumbnail

    if not main_image and image_names:
        main_image = image_names[0]

    # Category name
    category_name = ""

    if product.category:
        category_name = product.category.name

    # Price
    price = float(product.price) if product.price is not None else 0.0

    # Cost
    cost = float(product.cost) if product.cost is not None else None

    return {
        # Frontend-compatible ID
        "_id": product.id,

        # New product fields mapped to old frontend names
        "title": product.name or "",
        "name": product.name or "",

        "isNew": getattr(product, "is_new", False),

        "oldPrice": (
            float(product.old_price)
            if getattr(product, "old_price", None) is not None
            else None
        ),

        "price": price,

        "discountedPrice": (
            float(product.discounted_price)
            if getattr(product, "discounted_price", None) is not None
            else price
        ),

        "cost": cost,

        "description": product.description or "",

        # Category
        "category": category_name,
        "category_id": product.category_id,

        # New product structure
        "stock": product.stock or 0,

        # Temporary compatibility fields
        "type": getattr(product, "type", "") or "",
        "brand": getattr(product, "brand", "") or "",
        "size": getattr(product, "size", None) or [],

        # Image compatibility
        "image": main_image,
        "thumbnail": product.thumbnail,
        "images": image_names,

        "rating": (
            float(product.rating)
            if getattr(product, "rating", None) is not None
            else 0
        ),
    }

def get_product_by_id(product_id):
    """
    Get one product from the database.
    """

    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return None

    product = db.session.get(Product, product_id)

    if not product:
        return None

    return product_to_dict(product)


def get_all_products():
    # Products from database
    db_products = Product.query.order_by(Product.id.desc()).all()
    db_product_list = [product_to_dict(product) for product in db_products]

    # Products from old product.py
    old_product_list = old_products.copy()

    # Combine old + new
    return old_product_list + db_product_list

def get_products_by_category(category, current_id=None):
    """
    Get products from the same category.
    """

    query = Product.query.filter(
        Product.category == category
    )

    if current_id is not None:
        try:
            current_id = int(current_id)
            query = query.filter(Product.id != current_id)
        except (ValueError, TypeError):
            pass

    products = (
        query
        .order_by(Product.id.desc())
        .all()
    )

    return [
        product_to_dict(product)
        for product in products
    ]

def normalize_product(product):
    """
    Normalize old product.py data and database products
    into the same frontend format.
    """

    if not product:
        return None

    def to_float(value, default=None):
        if value is None or value == "":
            return default

        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    return {
        "_id": product.get("_id"),
        "title": product.get("title", ""),
        "isNew": product.get("isNew", False),

        "oldPrice": to_float(
            product.get("oldPrice")
        ),

        "price": to_float(
            product.get("price"),
            0
        ),

        "discountedPrice": to_float(
            product.get("discountedPrice"),
            to_float(product.get("price"), 0)
        ),

        "description": product.get("description", ""),

        "category": product.get("category", ""),
        "type": product.get("type", ""),

        "stock": int(product.get("stock", 0) or 0),

        "brand": product.get("brand", ""),

        "size": product.get("size", []) or [],

        "image": product.get("image"),

        "rating": to_float(
            product.get("rating"),
            0
        ),
    }


def get_all_store_products():
    """
    Return both old product.py products and database products.

    Old products use IDs starting from 1001 to avoid
    conflicts with database product IDs.
    """

    combined_products = []

    # ==========================================
    # OLD PRODUCTS
    # ==========================================

    for index, product in enumerate(old_products, start=1001):

        old_product = normalize_product(product)

        old_product["_id"] = index

        combined_products.append(old_product)

    # ==========================================
    # DATABASE PRODUCTS
    # ==========================================

    database_products = get_all_products()

    combined_products.extend(database_products)

    return combined_products