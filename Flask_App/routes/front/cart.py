import json
from flask import Blueprint, request, redirect, url_for, flash, make_response, render_template
from product import get_product_by_id
from helper import get_cart_items, get_cart_data

cart_bp = Blueprint("cart", __name__)


# ==========================================================
# CART PAGE
# ==========================================================
@cart_bp.route("/cart")
def cart():
    data = get_cart_data()
    return __render_cart(data)


# ==========================================================
# ADD TO CART
# ==========================================================
@cart_bp.route("/cart/add", methods=["POST"])
def add_to_cart():
    # Product ID
    product_id = request.form.get("product_id")
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        flash("Invalid product.", "danger")
        return redirect(request.referrer or url_for("front.products"))

    # Quantity
    quantity = request.form.get("quantity", 1)
    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        quantity = 1
    if quantity < 1:
        quantity = 1

    # Size
    size = request.form.get("size")
    if not size:
        flash("Please select a size.", "danger")
        return redirect(request.referrer or url_for("front.products"))
    size = size.strip()

    # Find product
    product = get_product_by_id(product_id)
    if not product:
        return "Product not found", 404

    # Check stock
    stock = product.get("stock", 0)
    if stock <= 0:
        flash(f"{product['title']} is out of stock.", "danger")
        return redirect(request.referrer or url_for("front.products"))
    if quantity > stock:
        flash(f"Only {stock} items available.", "danger")
        return redirect(request.referrer or url_for("front.products"))

    # Read existing cart
    cart_products = get_cart_items()
    found = False

    # Find existing product + same size
    for item in cart_products:
        if item.get("_id") == product["_id"] and item.get("size") == size:
            new_quantity = item.get("qty", 1) + quantity
            if new_quantity > stock:
                flash(f"Only {stock} items available.", "danger")
                return redirect(request.referrer or url_for("front.products"))
            item["qty"] = new_quantity
            found = True
            break

    # Add new cart item
    if not found:
        cart_products.append({
            "_id": product["_id"],
            "title": product["title"],
            "category": product["category"],
            "price": product["price"],
            "discountedPrice": product.get("discountedPrice", product["price"]),
            "qty": quantity,
            "size": size,
            "brand": product["brand"],
            "image": product["image"],
        })

    return __save_cart_and_redirect(cart_products)


# ==========================================================
# CART COUNT
# ==========================================================
@cart_bp.app_context_processor
def inject_cart_count():
    cart_products = get_cart_items()
    count = sum(item.get("qty", 1) for item in cart_products)
    return {"cart_count": count}


# ==========================================================
# INCREASE QUANTITY
# ==========================================================
@cart_bp.route("/cart/increase/<int:product_id>")
def increase_cart(product_id):
    cart_products = get_cart_items()
    product = get_product_by_id(product_id)

    if not product:
        flash("Product not found.", "danger")
        return redirect(url_for("cart.cart"))

    stock = product.get("stock", 0)
    for item in cart_products:
        if item.get("_id") == product_id:
            current_quantity = item.get("qty", 1)
            if current_quantity < stock:
                item["qty"] = current_quantity + 1
            else:
                flash(f"Only {stock} items available.", "warning")
            break

    return __save_cart_and_redirect(cart_products)


# ==========================================================
# DECREASE QUANTITY
# ==========================================================
@cart_bp.route("/cart/decrease/<int:product_id>")
def decrease_cart(product_id):
    cart_products = get_cart_items()
    for item in cart_products:
        if item.get("_id") == product_id:
            current_quantity = item.get("qty", 1)
            if current_quantity > 1:
                item["qty"] = current_quantity - 1
            break
    return __save_cart_and_redirect(cart_products)


# ==========================================================
# REMOVE FROM CART
# ==========================================================
@cart_bp.route("/cart/remove/<int:product_id>")
def remove_cart(product_id):
    cart_products = [item for item in get_cart_items() if item.get("_id") != product_id]
    return __save_cart_and_redirect(cart_products)


# ==========================================================
# OLD REMOVE URL (legacy support)
# ==========================================================
@cart_bp.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    return remove_cart(product_id)


# ==========================================================
# SAVE CART
# ==========================================================
def __save_cart_and_redirect(cart_products):
    response = make_response(redirect(url_for("cart.cart")))
    response.set_cookie("cart_list", json.dumps(cart_products), httponly=True, samesite="Lax")
    return response


# ==========================================================
# RENDER CART
# ==========================================================
def __render_cart(data):
    return render_template("front/cart.html", **data)
