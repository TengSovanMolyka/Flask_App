from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models.order import Order

admin_orders_bp = Blueprint("admin_orders", __name__, url_prefix="/admin/orders")


# ==========================================================
# ORDER LIST
# ==========================================================
@admin_orders_bp.route("/")
def index():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders/index.html", module="orders", orders=orders)


# ==========================================================
# ORDER DETAIL
# ==========================================================
@admin_orders_bp.route("/<string:order_id>")
def detail(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    return render_template("admin/orders/detail.html", module="orders", order=order)


# ==========================================================
# UPDATE ORDER STATUS
# ==========================================================
@admin_orders_bp.route("/<string:order_id>/status", methods=["POST"])
def update_status(order_id):
    order = Order.query.filter_by(order_id=order_id).first_or_404()
    status = request.form.get("status")

    allowed_statuses = {"Processing", "Shipped", "Delivered", "Cancelled"}
    if status not in allowed_statuses:
        flash("Invalid order status.", "danger")
        return redirect(url_for("admin_orders.detail", order_id=order.order_id))

    order.status = status
    db.session.commit()

    flash("Order status updated successfully.", "success")
    return redirect(url_for("admin_orders.detail", order_id=order.order_id))
