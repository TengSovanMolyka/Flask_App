import os
import json

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

from extensions import db
from models.product import Product


admin_products_bp = Blueprint(
    "admin_products",
    __name__,
    url_prefix="/admin/products"
)


# ==========================================================
# FILE UPLOAD
# ==========================================================

def allowed_image(filename):
    if not filename or "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in current_app.config.get(
        "ALLOWED_EXTENSIONS",
        {"png", "jpg", "jpeg", "gif"}
    )


def upload_product_image(image):
    """
    Upload product image and return filename.
    """

    if not image or not image.filename:
        return None

    if not allowed_image(image.filename):
        return None

    filename = secure_filename(image.filename)

    upload_folder = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "products"
    )

    os.makedirs(upload_folder, exist_ok=True)

    filepath = os.path.join(
        upload_folder,
        filename
    )

    image.save(filepath)

    return filename


def delete_product_image(filename):
    """
    Delete product image from storage.
    """

    if not filename:
        return

    filepath = os.path.join(
        current_app.root_path,
        "static",
        "uploads",
        "products",
        filename
    )

    if os.path.exists(filepath):
        os.remove(filepath)


# ==========================================================
# FORM DATA
# ==========================================================

def get_product_form():
    """
    Read product information from the submitted form.
    """

    title = request.form.get("title", "").strip()

    is_new = request.form.get("is_new") == "1"

    old_price = request.form.get("old_price", "").strip()

    price = request.form.get("price", "").strip()

    discounted_price = request.form.get(
        "discounted_price",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    category = request.form.get(
        "category",
        ""
    ).strip()

    product_type = request.form.get(
        "type",
        ""
    ).strip()

    stock = request.form.get(
        "stock",
        "0"
    ).strip()

    brand = request.form.get(
        "brand",
        ""
    ).strip()

    rating = request.form.get(
        "rating",
        "0"
    ).strip()

    size_text = request.form.get(
        "size",
        ""
    ).strip()

    # Convert sizes into JSON list
    if size_text:
        size = [
            item.strip()
            for item in size_text.split(",")
            if item.strip()
        ]
    else:
        size = []

    return {
        "title": title,
        "is_new": is_new,
        "old_price": float(old_price) if old_price else None,
        "price": float(price) if price else 0,
        "discounted_price": (
            float(discounted_price)
            if discounted_price
            else None
        ),
        "description": description,
        "category": category,
        "type": product_type,
        "stock": int(stock) if stock else 0,
        "brand": brand,
        "size": size,
        "rating": float(rating) if rating else 0,
    }


# ==========================================================
# PRODUCT LIST
# ==========================================================

@admin_products_bp.get("/")
def products():

    rows = Product.query.order_by(
        Product.id.desc()
    ).all()

    return render_template(
        "admin/products/index.html",
        module="products",
        rows=rows
    )


# ==========================================================
# ADD PRODUCT
# ==========================================================

@admin_products_bp.route("/add", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        try:
            data = get_product_form()

            # Basic validation
            if not data["title"]:
                flash(
                    "Product title is required.",
                    "danger"
                )
                return render_template(
                    "admin/products/add.html",
                    module="products"
                )

            if not data["category"]:
                flash(
                    "Category is required.",
                    "danger"
                )
                return render_template(
                    "admin/products/add.html",
                    module="products"
                )

            if not data["type"]:
                flash(
                    "Product type is required.",
                    "danger"
                )
                return render_template(
                    "admin/products/add.html",
                    module="products"
                )

            if data["price"] < 0:
                flash(
                    "Price cannot be negative.",
                    "danger"
                )
                return render_template(
                    "admin/products/add.html",
                    module="products"
                )

            if data["stock"] < 0:
                flash(
                    "Stock cannot be negative.",
                    "danger"
                )
                return render_template(
                    "admin/products/add.html",
                    module="products"
                )

            # Upload image
            image = request.files.get("image")

            filename = upload_product_image(image)

            data["image"] = filename

            # Create product
            product = Product(**data)

            db.session.add(product)
            db.session.commit()

            flash(
                "Product added successfully!",
                "success"
            )

            return redirect(
                url_for("admin_products.products")
            )

        except ValueError:
            db.session.rollback()

            flash(
                "Please enter valid numbers for price, stock, and rating.",
                "danger"
            )

        except Exception as e:
            db.session.rollback()

            print("Add Product Error:", e)

            flash(
                "Unable to add product.",
                "danger"
            )

    return render_template(
        "admin/products/add.html",
        module="products"
    )


# ==========================================================
# EDIT PRODUCT
# ==========================================================

@admin_products_bp.route(
    "/edit/<int:product_id>",
    methods=["GET", "POST"]
)
def edit_product(product_id):

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":

        try:
            data = get_product_form()

            if not data["title"]:
                flash(
                    "Product title is required.",
                    "danger"
                )

                return render_template(
                    "admin/products/edit.html",
                    module="products",
                    product=product
                )

            if not data["category"]:
                flash(
                    "Category is required.",
                    "danger"
                )

                return render_template(
                    "admin/products/edit.html",
                    module="products",
                    product=product
                )

            if not data["type"]:
                flash(
                    "Product type is required.",
                    "danger"
                )

                return render_template(
                    "admin/products/edit.html",
                    module="products",
                    product=product
                )

            if data["price"] < 0:
                flash(
                    "Price cannot be negative.",
                    "danger"
                )

                return render_template(
                    "admin/products/edit.html",
                    module="products",
                    product=product
                )

            if data["stock"] < 0:
                flash(
                    "Stock cannot be negative.",
                    "danger"
                )

                return render_template(
                    "admin/products/edit.html",
                    module="products",
                    product=product
                )

            # Update product fields
            product.title = data["title"]
            product.is_new = data["is_new"]
            product.old_price = data["old_price"]
            product.price = data["price"]
            product.discounted_price = data[
                "discounted_price"
            ]
            product.description = data["description"]
            product.category = data["category"]
            product.type = data["type"]
            product.stock = data["stock"]
            product.brand = data["brand"]
            product.size = data["size"]
            product.rating = data["rating"]

            # New image
            image = request.files.get("image")

            if image and image.filename:

                new_filename = upload_product_image(image)

                if new_filename:

                    old_filename = product.image

                    product.image = new_filename

                    if old_filename:
                        delete_product_image(
                            old_filename
                        )

            db.session.commit()

            flash(
                "Product updated successfully!",
                "success"
            )

            return redirect(
                url_for("admin_products.products")
            )

        except ValueError:
            db.session.rollback()

            flash(
                "Please enter valid numbers.",
                "danger"
            )

        except Exception as e:
            db.session.rollback()

            print("Edit Product Error:", e)

            flash(
                "Unable to update product.",
                "danger"
            )

    return render_template(
        "admin/products/edit.html",
        module="products",
        product=product
    )


# ==========================================================
# DELETE PRODUCT
# ==========================================================

@admin_products_bp.route(
    "/delete/<int:product_id>",
    methods=["GET", "POST"]
)
def delete_product(product_id):

    product = Product.query.get_or_404(product_id)

    if request.method == "POST":

        try:

            # Delete product image
            if product.image:
                delete_product_image(
                    product.image
                )

            db.session.delete(product)
            db.session.commit()

            flash(
                "Product deleted successfully!",
                "success"
            )

            return redirect(
                url_for("admin_products.products")
            )

        except Exception as e:

            db.session.rollback()

            print("Delete Product Error:", e)

            flash(
                "Unable to delete product.",
                "danger"
            )

            return redirect(
                url_for("admin_products.products")
            )

    return render_template(
        "admin/products/delete.html",
        module="products",
        product=product
    )