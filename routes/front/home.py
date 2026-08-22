from flask import Blueprint, render_template
from product import (
    products as pro,
    get_product_by_category,
    get_product_by_id,
)

front_bp = Blueprint("front", __name__)


# ==========================================
# HOME
# ==========================================
@front_bp.get("/")
def home():
    return render_template("front/index.html", products=pro)


# ==========================================
# PRODUCTS
# ==========================================
@front_bp.get("/products")
def products():
    return render_template("front/products.html", products=pro)


# ==========================================
# PRODUCT DETAIL
# ==========================================
@front_bp.get("/product/<int:id>")
def product(id):
    product_item = get_product_by_id(id)

    if not product_item:
        return "Product not found", 404

    related_product = get_product_by_category(
        product_item["category"],
        product_item["_id"]
    )

    return render_template(
        "front/product.html",
        product=product_item,
        related_product=related_product,
    )
