from flask import (
    render_template,
    redirect,
    url_for,
    session,
    flash,
    request,
)

from routes.front.home import front_bp
from product import get_product_by_id


# ==========================================================
# WISHLIST PAGE
# ==========================================================
@front_bp.get("/wishlist")
def wishlist():

    user_id = session.get("user_id")

    if not user_id:
        flash("Please login to view your wishlist.", "warning")
        return redirect(url_for("front.login"))

    wishlist_ids = session.get("wishlist", [])

    wishlist_products = []

    for product_id in wishlist_ids:

        product_item = get_product_by_id(int(product_id))

        if product_item:
            wishlist_products.append(product_item)

    return render_template(
        "front/wishlist.html",
        wishlist=wishlist_products,
    )


# ==========================================================
# TOGGLE WISHLIST
# ==========================================================
@front_bp.post("/wishlist/toggle/<int:product_id>")
def toggle_wishlist(product_id):

    user_id = session.get("user_id")

    if not user_id:
        flash("Please login first.", "warning")
        return redirect(
            request.referrer or url_for("front.products")
        )

    # Check product
    product_item = get_product_by_id(product_id)

    if not product_item:
        flash("Product not found.", "danger")
        return redirect(
            request.referrer or url_for("front.products")
        )

    # Get wishlist
    wishlist = [
        int(item)
        for item in session.get("wishlist", [])
    ]

    # REMOVE
    if product_id in wishlist:

        wishlist.remove(product_id)

        flash(
            f"{product_item['title']} removed from your wishlist.",
            "info"
        )

    # ADD
    else:

        wishlist.append(product_id)

        flash(
            f"{product_item['title']} added to your wishlist.",
            "success"
        )

    # Save
    session["wishlist"] = wishlist
    session.modified = True

    return redirect(
        request.referrer or url_for("front.wishlist")
    )


# ==========================================================
# REMOVE FROM WISHLIST
# ==========================================================
@front_bp.post("/wishlist/remove/<int:product_id>")
def remove_from_wishlist(product_id):

    user_id = session.get("user_id")

    if not user_id:
        flash("Please login first.", "warning")
        return redirect(url_for("front.login"))

    wishlist = [
        int(item)
        for item in session.get("wishlist", [])
    ]

    if product_id in wishlist:

        wishlist.remove(product_id)

        session["wishlist"] = wishlist
        session.modified = True

        flash(
            "Product removed from your wishlist.",
            "success"
        )

    return redirect(url_for("front.wishlist"))


# ==========================================================
# CLEAR WISHLIST
# ==========================================================
@front_bp.post("/wishlist/clear")
def clear_wishlist():

    user_id = session.get("user_id")

    if not user_id:
        return redirect(url_for("front.login"))

    session["wishlist"] = []
    session.modified = True

    flash("Wishlist cleared.", "success")

    return redirect(url_for("front.wishlist"))