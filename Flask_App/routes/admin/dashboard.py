from flask import (
    Blueprint,
    render_template
)

from .auth import login_required


# ==========================================================
# ADMIN DASHBOARD BLUEPRINT
# ==========================================================

admin_dashboard_bp = Blueprint(
    "admin_dashboard",
    __name__,
    url_prefix="/admin/dashboard"
)


# ==========================================================
# DASHBOARD
# ==========================================================

@admin_dashboard_bp.get("/")
@login_required
def dashboard():

    return render_template(
        "admin/dashboard/index.html",
        module="dashboard"
    )