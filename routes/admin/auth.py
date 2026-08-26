from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from functools import wraps
from werkzeug.security import check_password_hash

from models.user import User


# ==========================================================
# ADMIN AUTH BLUEPRINT
# ==========================================================

admin_auth_bp = Blueprint(
    "admin_auth",
    __name__,
    url_prefix="/admin/auth"
)


# ==========================================================
# ADMIN LOGIN REQUIRED
# ==========================================================
def login_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("admin_id"):
            return redirect(
                url_for(
                    "admin_auth.login",
                    next=request.path
                )
            )

        return view(*args, **kwargs)

    return wrapped

# ==========================================================
# ADMIN LOGIN
# ==========================================================
@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if session.get("admin_id"):
        return redirect(
            url_for("admin_dashboard.dashboard")
        )

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(
            username=username
        ).first()

        if not user:
            flash(
                "Invalid username or password.",
                "danger"
            )
            return redirect(
                url_for("admin_auth.login")
            )

        if user.role != "Admin":
            flash(
                "You do not have administrator access.",
                "danger"
            )
            return redirect(
                url_for("admin_auth.login")
            )

        if user.status != "Active":
            flash(
                "Your admin account is not active.",
                "danger"
            )
            return redirect(
                url_for("admin_auth.login")
            )

        if not check_password_hash(
            user.password,
            password
        ):
            flash(
                "Invalid username or password.",
                "danger"
            )
            return redirect(
                url_for("admin_auth.login")
            )

        # ==============================================
        # LOGIN SUCCESS
        # ==============================================

        session.clear()

        session["admin_id"] = user.id
        session["admin_username"] = user.username
        session["admin_role"] = user.role
        session["admin_profile"] = user.profile_image

        return redirect(
            url_for("admin_dashboard.dashboard")
        )

    return render_template(
        "admin/auth/login.html"
    )

# ==========================================================
# ADMIN LOGOUT
# ==========================================================

@admin_auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("admin_auth.login")
    )