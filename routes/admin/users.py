import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from extensions import db
from models.user import User

# ==========================================================
# ADMIN BLUEPRINT
# ==========================================================
admin_users_bp = Blueprint("admin_users", __name__, url_prefix="/admin")


# ==========================================================
# GET USER FORM DATA
# ==========================================================
def get_user_form():
    return {
        "username": request.form.get("username"),
        "address": request.form.get("address"),
        "email": request.form.get("email"),
        "contact": request.form.get("contact"),
        "password": request.form.get("password"),
        "role": request.form.get("role"),
        "status": request.form.get("status"),
    }


# ==========================================================
# UPLOAD PROFILE IMAGE
# ==========================================================
def upload_profile(profile):
    filename = "profile-avatar.png"
    if profile and profile.filename:
        filename = secure_filename(profile.filename)
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        os.makedirs(upload_folder, exist_ok=True)
        profile.save(os.path.join(upload_folder, filename))
    return filename


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================
@admin_users_bp.get("/dashboard")
def dashboard():
    return render_template("admin/dashboard/index.html", module="dashboard")


# ==========================================================
# ADMIN USERS
# ==========================================================
@admin_users_bp.get("/users")
def users():
    rows = User.query.all()
    return render_template("admin/users/index.html", module="users", rows=rows)


# ==========================================================
# ADD USER
# ==========================================================
@admin_users_bp.route("/users/add", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        data = get_user_form()

        # Password
        password = request.form.get("password")
        if not password:
            flash("Password is required.", "danger")
            return redirect(url_for("admin_users.add_user"))
        data["password"] = generate_password_hash(password)

        # Profile image
        profile = request.files.get("profile")
        filename = upload_profile(profile)

        # Create user
        new_user = User(profile=filename, **data)
        db.session.add(new_user)
        db.session.commit()

        flash("User added successfully!", "success")
        return redirect(url_for("admin_users.users"))

    return render_template("admin/users/add.html", module="users")


# ==========================================================
# EDIT USER
# ==========================================================
@admin_users_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        # Basic user information
        user.username = request.form.get("username")
        user.address = request.form.get("address")
        user.email = request.form.get("email")
        user.contact = request.form.get("contact")
        user.role = request.form.get("role")
        user.status = request.form.get("status")

        # Password
        password = request.form.get("password")
        if password:
            user.password = generate_password_hash(password)

        # Profile
        profile = request.files.get("profile")
        if profile and profile.filename:
            user.profile = upload_profile(profile)

        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("admin_users.users"))

    return render_template("admin/users/edit.html", module="users", user=user)


# ==========================================================
# DELETE USER
# ==========================================================
@admin_users_bp.route("/users/delete/<int:user_id>", methods=["GET", "POST"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        # Delete profile image
        if user.profile and user.profile not in {"default-avatar.png", "profile-avatar.png"}:
            image = os.path.join(current_app.config["UPLOAD_FOLDER"], user.profile)
            if os.path.exists(image):
                os.remove(image)

        # Delete database user
        db.session.delete(user)
        db.session.commit()

        flash("User deleted successfully!", "success")
        return redirect(url_for("admin_users.users"))

    return render_template("admin/users/delete.html", module="users", user=user)
