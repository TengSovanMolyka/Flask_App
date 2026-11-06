from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User

auth_bp = Blueprint("auth", __name__)


# ==========================================================
# REGISTER
# ==========================================================
@auth_bp.route("/create_user", methods=["GET", "POST"])
def create_user():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Basic validation
        if not full_name:
            flash("Full name is required.", "danger")
            return redirect(url_for("auth.create_user"))
        if not username:
            flash("Username is required.", "danger")
            return redirect(url_for("auth.create_user"))
        if not email:
            flash("Email is required.", "danger")
            return redirect(url_for("auth.create_user"))
        if not password:
            flash("Password is required.", "danger")
            return redirect(url_for("auth.create_user"))

        # Password confirmation
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("auth.create_user"))

        # Check duplicates
        if User.query.filter_by(username=username).first():
            flash("Username already taken!", "danger")
            return redirect(url_for("auth.create_user"))
        if User.query.filter_by(email=email).first():
            flash("Email already registered!", "danger")
            return redirect(url_for("auth.create_user"))

        # Hash password and create user
        hashed_password = generate_password_hash(password)
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            contact=phone,
            password=hashed_password,
            role="User",
            status="Active",
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("front/user/register.html")


# ==========================================================
# LOGIN
# ==========================================================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()
        if not user or user.status != "Active" or not check_password_hash(user.password, password):
            flash("Invalid username or password.", "danger")
            return redirect(url_for("auth.login"))

        session.clear()
        session["user_id"] = user.id
        flash(f"Welcome back, {user.full_name or user.username}!", "success")
        return redirect(url_for("front.home"))

    return render_template("front/user/login.html")


# ==========================================================
# LOGOUT
# ==========================================================
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))


# ==========================================================
# FORGOT PASSWORD
# ==========================================================
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("No account found with that email.", "danger")
            return redirect(url_for("auth.forgot_password"))

        # Temporary flow: redirect to reset page
        return redirect(url_for("auth.reset_password", user_id=user.id))

    return render_template("front/user/forgot_password.html")


# ==========================================================
# RESET PASSWORD
# ==========================================================
@auth_bp.route("/reset-password/<int:user_id>", methods=["GET", "POST"])
def reset_password(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not new_password:
            flash("Password cannot be empty.", "danger")
            return redirect(url_for("auth.reset_password", user_id=user.id))
        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for("auth.reset_password", user_id=user.id))

        user.password = generate_password_hash(new_password)
        db.session.commit()

        flash("Password reset successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("front/user/reset_password.html", user_id=user.id)
