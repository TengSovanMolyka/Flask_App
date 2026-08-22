import os
import json
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash, current_app
)
from werkzeug.utils import secure_filename
from extensions import db
from models.user import User
from helper import allowed_file

account_bp = Blueprint("account", __name__)


# ==========================================================
# GET CURRENT USER
# ==========================================================
def get_current_user():
    """Get the currently logged-in user from the database."""
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


# ==========================================================
# ACCOUNT
# ==========================================================
@account_bp.route("/account")
def account():
    # Require login
    if "user_id" not in session:
        flash("Please login to access your account.", "danger")
        return redirect(url_for("auth.login"))

    user = get_current_user()
    if not user:
        session.clear()
        flash("User not found. Please login again.", "danger")
        return redirect(url_for("auth.login"))

    # Orders (still stored in orders.json for now)
    orders, active_orders = [], []
    orders_file = "orders.json"

    if os.path.exists(orders_file):
        try:
            with open(orders_file, "r", encoding="utf-8") as file:
                orders = json.load(file)

            active_orders = [
                order for order in orders
                if order.get("status") and order["status"] != "Delivered"
                and order.get("email") == user.email
            ]
            orders = [order for order in orders if order.get("email") == user.email]
        except Exception as e:
            print("Account orders error:", e)

    saved_items = []

    return render_template(
        "front/account.html",
        user=user,
        orders=orders,
        active_orders=active_orders,
        saved_items=saved_items,
    )


# ==========================================================
# EDIT PROFILE
# ==========================================================
@account_bp.route("/edit-profile", methods=["POST"])
def edit_profile():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("auth.login"))

    user = get_current_user()
    if not user:
        session.clear()
        flash("User not found. Please login again.", "danger")
        return redirect(url_for("auth.login"))

    # Form data
    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    # Basic validation
    if not full_name:
        flash("Full name is required.", "danger")
        return redirect(url_for("account.account"))
    if not username:
        flash("Username is required.", "danger")
        return redirect(url_for("account.account"))
    if not email:
        flash("Email is required.", "danger")
        return redirect(url_for("account.account"))

    # Check duplicates
    if User.query.filter(User.username == username, User.id != user.id).first():
        flash("Username already taken.", "danger")
        return redirect(url_for("account.account"))
    if User.query.filter(User.email == email, User.id != user.id).first():
        flash("Email already registered.", "danger")
        return redirect(url_for("account.account"))

    # Update user
    user.full_name = full_name
    user.username = username
    user.email = email
    user.contact = phone
    user.address = address
    db.session.commit()

    flash("Profile updated successfully!", "success")
    return redirect(url_for("account.account"))


# ==========================================================
# UPLOAD PROFILE
# ==========================================================
@account_bp.route("/upload-profile", methods=["POST"])
def upload_profile():
    if "user_id" not in session:
        flash("Please login first.", "danger")
        return redirect(url_for("auth.login"))

    user = get_current_user()
    if not user:
        session.clear()
        flash("User not found. Please login again.", "danger")
        return redirect(url_for("auth.login"))

    # Check uploaded file
    if "profile_image" not in request.files:
        flash("No file selected.", "danger")
        return redirect(url_for("account.account"))

    file = request.files["profile_image"]
    if not file or not file.filename:
        flash("No file selected.", "danger")
        return redirect(url_for("account.account"))

    # Validate extension
    if not allowed_file(file.filename):
        flash("Invalid file type. Please upload JPG, JPEG, PNG, or GIF.", "danger")
        return redirect(url_for("account.account"))

    filename = secure_filename(file.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)

    # Delete old profile image
    old_profile = user.profile
    if old_profile and old_profile != "default-avatar.png" and old_profile != filename:
        old_path = os.path.join(upload_folder, old_profile)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError as e:
                print("Could not delete old profile:", e)

    # Save new profile image
    file.save(filepath)

    # Update user profile
    user.profile = filename
    db.session.commit()

    flash("Profile image updated successfully!", "success")
    return redirect(url_for("account.account"))
