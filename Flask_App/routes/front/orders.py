import uuid
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash, make_response
)
from extensions import db
from models.user import User
from models.order import Order
from models.order_item import OrderItem
from product import get_product_by_id, update_stock
from helper import get_cart_data

orders_bp = Blueprint("orders", __name__)


# ==========================================================
# CURRENT USER
# ==========================================================
def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


# ==========================================================
# CHECKOUT PAGE
# ==========================================================
@orders_bp.route("/checkout")
def checkout():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("auth.login"))

    user = get_current_user()
    if not user:
        session.clear()
        flash("User not found. Please login again.", "danger")
        return redirect(url_for("auth.login"))

    data = get_cart_data()
    if not data["cart_products"]:
        flash("Your cart is empty.", "danger")
        return redirect(url_for("cart.cart"))

    return render_template("front/orders/checkout.html", user=user, **data)


# ==========================================================
# CONFIRM CHECKOUT
# ==========================================================
@orders_bp.route("/checkout/confirm", methods=["POST"])
def checkout_confirm():
    if "user_id" not in session:
        flash("You must login or register before placing an order.", "danger")
        return redirect(url_for("auth.login"))

    user = get_current_user()
    if not user:
        session.clear()
        flash("User not found. Please login again.", "danger")
        return redirect(url_for("auth.login"))

    # Billing information
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip().lower()
    address = request.form.get("address", "").strip()
    payment_method = request.form.get("payment_method", "").strip()

    # Required fields
    if not all([name, phone, email, address, payment_method]):
        flash("All billing fields are required.", "danger")
        return redirect(url_for("orders.checkout"))

    if email != user.email.lower():
        flash("Incorrect email in Billing Details. Please use your account email.", "danger")
        return redirect(url_for("orders.checkout"))

    # Cart
    data = get_cart_data()
    cart_products = data["cart_products"]
    if not cart_products:
        flash("Your cart is empty.", "danger")
        return redirect(url_for("cart.cart"))

    # Check stock
    for item in cart_products:
        product = get_product_by_id(item["_id"])
        if not product:
            flash("One of the products in your cart is no longer available.", "danger")
            return redirect(url_for("cart.cart"))

        current_stock = product.get("stock", 0)
        if item["qty"] > current_stock:
            flash(f"{product['title']} only has {current_stock} left in stock.", "danger")
            return redirect(url_for("cart.cart"))

    # Totals
    subtotal, shipping = data["subtotal"], data["shipping"]
    total = subtotal + shipping

    # Generate order number
    order_id = "ORD-" + uuid.uuid4().hex[:10].upper()

    # Create order
    order = Order(
        order_id=order_id,
        user_id=user.id,
        customer_name=name,
        phone=phone,
        email=email,
        address=address,
        payment_method=payment_method,
        subtotal=subtotal,
        shipping=shipping,
        total=total,
        status="Processing",
    )
    db.session.add(order)

    # Create order items
    for item in cart_products:
        order_item = OrderItem(
            order=order,
            product_id=item["_id"],
            title=item["title"],
            category=item.get("category"),
            brand=item.get("brand"),
            image=item.get("image"),
            price=item["price"],
            discounted_price=item["discountedPrice"],
            quantity=item["qty"],
            size=item.get("size"),
        )
        db.session.add(order_item)

    # Commit order
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("Order database error:", e)
        flash("Unable to place your order. Please try again.", "danger")
        return redirect(url_for("orders.checkout"))

    # Reduce stock
    for item in cart_products:
        update_stock(item["_id"], item["qty"])

    # Clear cart
    response = make_response(
        render_template(
            "front/orders/order_success.html",
            customer_name=name,
            order_id=order_id,
            **data,
            total=total,
        )
    )
    response.set_cookie("cart_list", "[]", httponly=True, samesite="Lax")

    # Telegram notification
    try:
        from helper import send_order_to_telegram
        send_order_to_telegram(order)
    except Exception as e:
        print("Telegram notification error:", e)

    return response


# ==========================================================
# ORDER SUCCESS
# ==========================================================
@orders_bp.route("/order_success/<string:order_id>")
def order_success(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    if "user_id" not in session or order.user_id != session["user_id"]:
        flash("You are not allowed to view this order.", "danger")
        return redirect(url_for("orders.order_history"))

    return render_template(
        "front/orders/order_success.html",
        order_id=order.order_id,
        customer_name=order.customer_name,
        subtotal=order.subtotal,
        shipping=order.shipping,
        total=order.total,
    )


# ==========================================================
# ORDER RECEIPT
# ==========================================================
@orders_bp.route("/orders/<string:order_id>")
def order_receipt(order_id):
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("auth.login"))

    order = Order.query.filter_by(order_id=order_id).first_or_404()
    if order.user_id != session["user_id"]:
        flash("You are not allowed to view this order.", "danger")
        return redirect(url_for("orders.order_history"))

    return render_template("front/orders/order_receipt.html", order=order)


# ==========================================================
# ORDER HISTORY
# ==========================================================
@orders_bp.route("/orders")
def order_history():
    if "user_id" not in session:
        flash("Please login to view your orders.", "danger")
        return redirect(url_for("auth.login"))

    orders = (
        Order.query.filter_by(user_id=session["user_id"])
        .order_by(Order.created_at.desc())
        .all()
    )
    return render_template("front/orders/orders_history.html", orders=orders)
