from flask import Blueprint, render_template

from models.category import Category
from helper import get_all_store_products, get_product_by_id, get_products_by_category

front_bp = Blueprint("front", __name__)


@front_bp.get("/")
def home():
    products = get_all_store_products()[:6]
    return render_template("front/index.html", products=products)


@front_bp.get("/products")
def products():
    all_products = get_all_store_products()
    category_names = {
        category.name for category in Category.query.order_by(Category.name.asc()).all()
        if category.name
    }
    category_names.update(
        (item.get("category") or "").strip()
        for item in all_products
        if (item.get("category") or "").strip()
    )
    return render_template(
        "front/products.html",
        products=all_products,
        categories=sorted(category_names, key=str.lower),
    )


@front_bp.get("/product/<int:id>")
def product(id):
    current_product = get_product_by_id(id)
    if not current_product:
        return "Product not found", 404

    related_products = get_products_by_category(
        current_product.get("category"),
        current_id=current_product.get("_id"),
        limit=8,
    )
    return render_template(
        "front/product.html",
        product=current_product,
        related_product=related_products,
    )
