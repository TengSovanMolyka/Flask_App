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

from extensions import db
from models.product import Product
from models.category import Category
from models.product_image import ProductImage


admin_products_bp = Blueprint(
    "admin_products",
    __name__,
    url_prefix="/admin/products"
)


# ==========================================================
# ALLOWED IMAGE EXTENSIONS
# ==========================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "avif",
}


# ==========================================================
# IMAGE HELPERS
# ==========================================================

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def get_upload_folder():
    folder = os.path.join(
        current_app.static_folder,
        "uploads",
        "products"
    )

    os.makedirs(folder, exist_ok=True)

    return folder


def get_unique_filename(filename):
    filename = secure_filename(filename)

    name, extension = os.path.splitext(filename)

    upload_folder = get_upload_folder()

    new_filename = filename
    counter = 1

    while os.path.exists(
        os.path.join(upload_folder, new_filename)
    ):
        new_filename = f"{name}_{counter}{extension}"
        counter += 1

    return new_filename


def delete_image_file(filename):
    if not filename:
        return

    file_path = os.path.join(
        get_upload_folder(),
        filename
    )

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass


# ==========================================================
# PRODUCT LIST
# ==========================================================

@admin_products_bp.get("/")
def products():

    rows = (
        Product.query
        .order_by(Product.id.desc())
        .all()
    )

    return render_template(
        "admin/products/index.html",
        rows=rows,
        module="products"
    )


# ==========================================================
# ADD PRODUCT
# ==========================================================

@admin_products_bp.route("/add", methods=["GET", "POST"])
def add_product():

    categories = (
        Category.query
        .order_by(Category.name.asc())
        .all()
    )

    if request.method == "POST":

        # --------------------------------------------------
        # BASIC FIELDS
        # --------------------------------------------------

        name = request.form.get("name", "").strip()
        product_type = request.form.get("type", "").strip()
        brand = request.form.get("brand", "").strip()

        is_new = request.form.get("is_new") == "1"

        category_id_text = request.form.get(
            "category_id",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # --------------------------------------------------
        # PRICE / STOCK / RATING
        # --------------------------------------------------

        old_price_text = request.form.get(
            "old_price",
            ""
        ).strip()

        price_text = request.form.get(
            "price",
            ""
        ).strip()

        discounted_price_text = request.form.get(
            "discounted_price",
            ""
        ).strip()

        stock_text = request.form.get(
            "stock",
            "0"
        ).strip()

        rating_text = request.form.get(
            "rating",
            "0"
        ).strip()

        # --------------------------------------------------
        # SIZE
        # --------------------------------------------------

        allowed_sizes = {
            "XS",
            "S",
            "M",
            "L",
            "XL",
            "XXL",
        }

        sizes = [
            size
            for size in request.form.getlist("size")
            if size in allowed_sizes
        ]

        # --------------------------------------------------
        # VALIDATION
        # --------------------------------------------------

        if not name:
            flash("Product name is required.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        if not product_type:
            flash("Product type is required.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        if not category_id_text:
            flash("Please select a category.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        try:
            category_id = int(category_id_text)
        except ValueError:
            flash("Invalid category.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        category = db.session.get(
            Category,
            category_id
        )

        if not category:
            flash("Selected category does not exist.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # CONVERT NUMBERS
        # --------------------------------------------------

        try:
            if not price_text:
                raise ValueError

            price = float(price_text)

            if price < 0:
                raise ValueError

        except ValueError:
            flash("Please enter a valid price.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        try:
            old_price = (
                float(old_price_text)
                if old_price_text
                else None
            )

            if old_price is not None and old_price < 0:
                raise ValueError

        except ValueError:
            flash("Please enter a valid old price.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        try:
            discounted_price = (
                float(discounted_price_text)
                if discounted_price_text
                else None
            )

            if (
                discounted_price is not None
                and discounted_price < 0
            ):
                raise ValueError

        except ValueError:
            flash(
                "Please enter a valid discounted price.",
                "danger"
            )
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        try:
            stock = int(stock_text)

            if stock < 0:
                raise ValueError

        except ValueError:
            flash("Please enter a valid stock quantity.", "danger")
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        try:
            rating = float(rating_text or 0)

            if rating < 0 or rating > 5:
                raise ValueError

        except ValueError:
            flash(
                "Rating must be between 0 and 5.",
                "danger"
            )
            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # UPLOAD IMAGES
        # --------------------------------------------------

        uploaded_files = request.files.getlist("images")

        uploaded_images = []

        for file in uploaded_files:

            if not file or not file.filename:
                continue

            if not allowed_file(file.filename):
                flash(
                    f"Invalid image type: {file.filename}",
                    "danger"
                )
                return render_template(
                    "admin/products/add.html",
                    categories=categories,
                    module="products"
                )

            filename = get_unique_filename(
                file.filename
            )

            file.save(
                os.path.join(
                    get_upload_folder(),
                    filename
                )
            )

            uploaded_images.append(filename)

        # --------------------------------------------------
        # MAIN IMAGE
        # --------------------------------------------------

        main_image_index_text = request.form.get(
            "main_image_index",
            "0"
        )

        try:
            main_image_index = int(
                main_image_index_text
            )
        except ValueError:
            main_image_index = 0

        thumbnail = None

        if uploaded_images:

            if (
                0 <= main_image_index
                < len(uploaded_images)
            ):
                thumbnail = uploaded_images[
                    main_image_index
                ]
            else:
                thumbnail = uploaded_images[0]

        # --------------------------------------------------
        # CREATE PRODUCT
        # --------------------------------------------------

        product = Product(
            name=name,
            type=product_type,
            brand=brand or None,
            is_new=is_new,

            thumbnail=thumbnail,

            # Current add form has no cost field.
            cost=None,

            old_price=old_price,
            price=price,
            discounted_price=discounted_price,

            stock=stock,
            rating=rating,

            size=sizes if sizes else None,

            category_id=category.id,

            description=description or None,
        )

        db.session.add(product)
        db.session.flush()

        # --------------------------------------------------
        # SAVE PRODUCT IMAGES
        # --------------------------------------------------

        for filename in uploaded_images:

            product_image = ProductImage(
                product_id=product.id,
                name=filename
            )

            db.session.add(product_image)

        # --------------------------------------------------
        # COMMIT
        # --------------------------------------------------

        try:

            db.session.commit()

            flash(
                "Product added successfully.",
                "success"
            )

            return redirect(
                url_for("admin_products.products")
            )

        except Exception as e:

            db.session.rollback()

            # Remove uploaded files if database failed
            for filename in uploaded_images:
                delete_image_file(filename)

            current_app.logger.exception(
                "Error adding product: %s",
                e
            )

            flash(
                "Failed to add product.",
                "danger"
            )

            return render_template(
                "admin/products/add.html",
                categories=categories,
                module="products"
            )

    return render_template(
        "admin/products/add.html",
        categories=categories,
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

    product = db.session.get(
        Product,
        product_id
    )

    if not product:

        flash(
            "Product not found.",
            "danger"
        )

        return redirect(
            url_for("admin_products.products")
        )

    categories = (
        Category.query
        .order_by(Category.name.asc())
        .all()
    )

    if request.method == "POST":

        # --------------------------------------------------
        # BASIC FIELDS
        # --------------------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        product_type = request.form.get(
            "type",
            ""
        ).strip()

        brand = request.form.get(
            "brand",
            ""
        ).strip()

        is_new = request.form.get(
            "is_new"
        ) == "1"

        category_id_text = request.form.get(
            "category_id",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # --------------------------------------------------
        # NUMERIC FIELDS
        # --------------------------------------------------

        # If the form does not contain cost,
        # preserve the current database value.
        cost_text = request.form.get("cost")

        old_price_text = request.form.get(
            "old_price",
            ""
        ).strip()

        price_text = request.form.get(
            "price",
            ""
        ).strip()

        discounted_price_text = request.form.get(
            "discounted_price",
            ""
        ).strip()

        stock_text = request.form.get(
            "stock",
            "0"
        ).strip()

        rating_text = request.form.get(
            "rating",
            "0"
        ).strip()

        # --------------------------------------------------
        # VALIDATE BASIC FIELDS
        # --------------------------------------------------

        if not name:
            flash(
                "Product name is required.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        if not product_type:
            flash(
                "Product type is required.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        try:
            category_id = int(category_id_text)

        except ValueError:

            flash(
                "Invalid category.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        category = db.session.get(
            Category,
            category_id
        )

        if not category:

            flash(
                "Selected category does not exist.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # COST
        # --------------------------------------------------

        if cost_text is None:

            cost = product.cost

        else:

            cost_text = cost_text.strip()

            try:

                cost = (
                    float(cost_text)
                    if cost_text
                    else None
                )

                if cost is not None and cost < 0:
                    raise ValueError

            except ValueError:

                flash(
                    "Please enter a valid cost.",
                    "danger"
                )

                return render_template(
                    "admin/products/edit.html",
                    product=product,
                    categories=categories,
                    module="products"
                )

        # --------------------------------------------------
        # OLD PRICE
        # --------------------------------------------------

        try:

            old_price = (
                float(old_price_text)
                if old_price_text
                else None
            )

            if old_price is not None and old_price < 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid old price.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # PRICE
        # --------------------------------------------------

        try:

            if not price_text:
                raise ValueError

            price = float(price_text)

            if price < 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid price.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # DISCOUNTED PRICE
        # --------------------------------------------------

        try:

            discounted_price = (
                float(discounted_price_text)
                if discounted_price_text
                else None
            )

            if (
                discounted_price is not None
                and discounted_price < 0
            ):
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid discounted price.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # STOCK
        # --------------------------------------------------

        try:

            stock = int(stock_text)

            if stock < 0:
                raise ValueError

        except ValueError:

            flash(
                "Please enter a valid stock quantity.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # RATING
        # --------------------------------------------------

        try:

            rating = float(rating_text or 0)

            if rating < 0 or rating > 5:
                raise ValueError

        except ValueError:

            flash(
                "Rating must be between 0 and 5.",
                "danger"
            )

            return render_template(
                "admin/products/edit.html",
                product=product,
                categories=categories,
                module="products"
            )

        # --------------------------------------------------
        # SIZE
        # --------------------------------------------------

        allowed_sizes = {
            "XS",
            "S",
            "M",
            "L",
            "XL",
            "XXL",
        }

        sizes = [
            size
            for size in request.form.getlist("size")
            if size in allowed_sizes
        ]

        # --------------------------------------------------
        # UPDATE PRODUCT
        # --------------------------------------------------

        product.name = name
        product.type = product_type
        product.brand = brand or None
        product.is_new = is_new

        product.category_id = category.id

        product.description = (
            description or None
        )

        product.cost = cost
        product.old_price = old_price
        product.price = price
        product.discounted_price = discounted_price

        product.stock = stock
        product.rating = rating

        product.size = (
            sizes if sizes else None
        )

        # --------------------------------------------------
        # UPLOAD NEW IMAGES
        # --------------------------------------------------

        uploaded_files = request.files.getlist(
            "images"
        )

        new_images = []

        for file in uploaded_files:

            if not file or not file.filename:
                continue

            if not allowed_file(file.filename):

                flash(
                    f"Invalid image type: {file.filename}",
                    "danger"
                )

                return render_template(
                    "admin/products/edit.html",
                    product=product,
                    categories=categories,
                    module="products"
                )

            filename = get_unique_filename(
                file.filename
            )

            file.save(
                os.path.join(
                    get_upload_folder(),
                    filename
                )
            )

            new_images.append(filename)

            db.session.add(
                ProductImage(
                    product_id=product.id,
                    name=filename
                )
            )

        # --------------------------------------------------
        # MAIN IMAGE
        # --------------------------------------------------

        main_image = request.form.get(
            "main_image",
            ""
        ).strip()

        existing_images = [
            image.name
            for image in product.images
        ]

        valid_image_names = (
            existing_images + new_images
        )

        # New image selected from edit page
        if main_image.startswith("__NEW__"):

            try:

                new_index = int(
                    main_image.replace(
                        "__NEW__",
                        "",
                        1
                    )
                )

            except ValueError:

                new_index = -1

            if (
                0 <= new_index
                < len(new_images)
            ):
                product.thumbnail = new_images[
                    new_index
                ]

        # Existing image selected
        elif (
            main_image
            and main_image in existing_images
        ):

            product.thumbnail = main_image

        # If product has no thumbnail
        elif (
            not product.thumbnail
            and valid_image_names
        ):

            product.thumbnail = (
                valid_image_names[0]
            )

        # --------------------------------------------------
        # COMMIT
        # --------------------------------------------------

        try:

            db.session.commit()

            flash(
                "Product updated successfully.",
                "success"
            )

            return redirect(
                url_for("admin_products.products")
            )

        except Exception as e:

            db.session.rollback()

            # Remove newly uploaded files
            for filename in new_images:
                delete_image_file(filename)

            current_app.logger.exception(
                "Error updating product: %s",
                e
            )

            flash(
                "Failed to update product.",
                "danger"
            )

    return render_template(
        "admin/products/edit.html",
        product=product,
        categories=categories,
        module="products"
    )


# ==========================================================
# DELETE CONFIRMATION PAGE
# ==========================================================

@admin_products_bp.get("/delete/<int:product_id>")
def confirm_delete(product_id):

    product = db.session.get(
        Product,
        product_id
    )

    if not product:

        flash(
            "Product not found.",
            "danger"
        )

        return redirect(
            url_for("admin_products.products")
        )

    return render_template(
        "admin/products/delete.html",
        product=product,
        module="products"
    )


# ==========================================================
# DELETE PRODUCT
# ==========================================================

@admin_products_bp.post("/delete/<int:product_id>")
def delete_product(product_id):

    product = db.session.get(
        Product,
        product_id
    )

    if not product:

        flash(
            "Product not found.",
            "danger"
        )

        return redirect(
            url_for("admin_products.products")
        )

    # Keep image names before deleting product
    image_names = [
        image.name
        for image in product.images
        if image.name
    ]

    # Also include thumbnail
    if (
        product.thumbnail
        and product.thumbnail not in image_names
    ):
        image_names.append(
            product.thumbnail
        )

    try:

        db.session.delete(product)

        db.session.commit()

        # Delete physical image files
        for filename in image_names:
            delete_image_file(filename)

        flash(
            "Product deleted successfully.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        current_app.logger.exception(
            "Error deleting product: %s",
            e
        )

        flash(
            "Failed to delete product.",
            "danger"
        )

    return redirect(
        url_for("admin_products.products")
    )