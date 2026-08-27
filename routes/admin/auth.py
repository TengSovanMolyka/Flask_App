from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
)

from functools import wraps
from werkzeug.security import check_password_hash

from models.user import User


# ==========================================================
# ADMIN / DASHBOARD AUTH BLUEPRINT
# ==========================================================
admin_auth_bp = Blueprint(
    "admin_auth",
    __name__,
    url_prefix="/admin/auth",
)


# ==========================================================
# LOGIN REQUIRED
# ==========================================================
# Admin AND User can access routes protected by this decorator.
# ==========================================================
def login_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        if not session.get("user_id"):
            return redirect(
                url_for(
                    "admin_auth.login",
                    next=request.path,
                )
            )

        return view(*args, **kwargs)

    return wrapped


# ==========================================================
# ADMIN REQUIRED
# ==========================================================
# ONLY Admin can access routes protected by this decorator.
# ==========================================================
def admin_required(view):

    @wraps(view)
    def wrapped(*args, **kwargs):

        # Not logged in
        if not session.get("user_id"):
            return redirect(
                url_for(
                    "admin_auth.login",
                    next=request.path,
                )
            )

        # Logged in but not Admin
        if session.get("user_role") != "Admin":
            flash(
                "You do not have permission to access this page.",
                "danger",
            )

            return redirect(
                url_for("admin_dashboard.dashboard")
            )

        return view(*args, **kwargs)

    return wrapped


# ==========================================================
# LOGIN
# ==========================================================
@admin_auth_bp.route("/login", methods=["GET", "POST"])
def login():

    # Already logged in
    if session.get("user_id"):
        return redirect(
            url_for("admin_dashboard.dashboard")
        )

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # --------------------------------------------------
        # FIND USER
        # --------------------------------------------------
        user = User.query.filter_by(
            username=username
        ).first()

        if not user:
            flash(
                "Invalid username or password.",
                "danger",
            )

            return redirect(
                url_for("admin_auth.login")
            )

        # --------------------------------------------------
        # CHECK ACCOUNT STATUS
        # --------------------------------------------------
        if user.status != "Active":
            flash(
                "Your account is not active.",
                "danger",
            )

            return redirect(
                url_for("admin_auth.login")
            )

        # --------------------------------------------------
        # CHECK PASSWORD
        # --------------------------------------------------
        if not check_password_hash(
            user.password,
            password,
        ):
            flash(
                "Invalid username or password.",
                "danger",
            )

            return redirect(
                url_for("admin_auth.login")
            )

        # ==================================================
        # LOGIN SUCCESS
        # ==================================================
        session.clear()

        # General user information
        session["user_id"] = user.id
        session["user_username"] = user.username
        session["user_role"] = user.role
        session["user_profile"] = user.profile_image

        # --------------------------------------------------
        # Keep admin session names for your existing navbar
        # --------------------------------------------------
        session["admin_id"] = user.id
        session["admin_username"] = user.username
        session["admin_role"] = user.role
        session["admin_profile"] = user.profile_image

        # --------------------------------------------------
        # Redirect to dashboard
        # --------------------------------------------------
        next_page = request.args.get("next")

        if next_page:
            return redirect(next_page)

        return redirect(
            url_for("admin_dashboard.dashboard")
        )

    return render_template(
        "admin/auth/login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================
@admin_auth_bp.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("admin_auth.login")
    )