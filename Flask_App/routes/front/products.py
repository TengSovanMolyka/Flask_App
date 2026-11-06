from flask import render_template

from product import (
    products as pro,
    get_product_by_id,
    get_product_by_category,
)

from routes.front import front

# ============================================================
# PRODUCTS LIST
# ============================================================
@front.get("/products")
def products():
    return render_template(
        "front/products.html",
        products=pro,
    )

@front.get("/product/<int:id>")
def product(id):
    product = get_product_by_id(id)

    if not product:
        return "Product not found", 404

    related_product = get_product_by_category(
        product["category"],
        product["_id"],
    )

    return render_template(
        "front/product.html",
        product=product,
        related_product=related_product,
    )
