import os

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)

from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

from extensions import db
from models.user import User
from .auth import admin_required


# ==========================================================
# ADMIN USERS BLUEPRINT
# ==========================================================
admin_users_bp = Blueprint(
    "admin_users",
    __name__,
    url_prefix="/admin",
)


# ==========================================================
# GET USER FORM DATA
# ==========================================================
def get_user_form():
    return {
        "username": request.form.get("username", "").strip(),
        "address": request.form.get("address", "").strip(),
        "email": request.form.get("email", "").strip(),
        "contact": request.form.get("contact", "").strip(),
        "role": request.form.get("role", "User"),
        "status": request.form.get("status", "Active"),
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
# ADMIN USERS
# ==========================================================
@admin_users_bp.get("/users")
@admin_required
def users():
    rows = User.query.all()
    return render_template(
        "admin/users/index.html",
        module="users",
        rows=rows,
    )


# ==========================================================
# ADD USER
# ==========================================================
@admin_users_bp.route("/users/add", methods=["GET", "POST"])
@admin_required
def add_user():
    if request.method == "POST":
        data = get_user_form()

        # Password
        password = request.form.get("password", "")
        if not password:
            flash("Password is required.", "danger")
            return redirect(url_for("admin_users.add_user"))

        data["password"] = generate_password_hash(password)

        # Profile image
        profile = request.files.get("profile")
        filename = upload_profile(profile)

        # Create user
        new_user = User(profile_image=filename, **data)
        db.session.add(new_user)
        db.session.commit()

        flash("User added successfully!", "success")
        return redirect(url_for("admin_users.users"))

    return render_template("admin/users/add.html", module="users")


# ==========================================================
# EDIT USER
# ==========================================================
@admin_users_bp.route("/users/edit/<int:user_id>", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        # Basic information
        user.username = request.form.get("username", "").strip()
        user.address = request.form.get("address", "").strip()
        user.email = request.form.get("email", "").strip()
        user.contact = request.form.get("contact", "").strip()
        user.role = request.form.get("role", "User")
        user.status = request.form.get("status", "Active")

        # Password
        password = request.form.get("password", "")
        if password:
            user.password = generate_password_hash(password)

        # Profile image
        profile = request.files.get("profile")
        if profile and profile.filename:
            user.profile_image = upload_profile(profile)

        db.session.commit()
        flash("User updated successfully!", "success")
        return redirect(url_for("admin_users.users"))

    return render_template(
        "admin/users/edit.html",
        module="users",
        user=user,
    )


# ==========================================================
# DELETE USER
# ==========================================================
@admin_users_bp.route("/users/delete/<int:user_id>", methods=["GET", "POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        # Delete profile image
        if (
            user.profile_image
            and user.profile_image
            not in {"default-avatar.png", "profile-avatar.png"}
        ):
            image = os.path.join(
                current_app.config["UPLOAD_FOLDER"],
                user.profile_image,
            )
            if os.path.exists(image):
                os.remove(image)

        # Delete database user
        db.session.delete(user)
        db.session.commit()

        flash("User deleted successfully!", "success")
        return redirect(url_for("admin_users.users"))

    return render_template(
        "admin/users/delete.html",
        module="users",
        user=user,
    )
