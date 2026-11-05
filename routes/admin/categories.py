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
from models.category import Category


admin_categories_bp = Blueprint(
    "admin_categories",
    __name__,
    url_prefix="/admin/categories"
)


# ==========================================================
# ALLOWED IMAGE EXTENSIONS
# ==========================================================

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp"
}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==========================================================
# UPLOAD FOLDER
# ==========================================================

def get_upload_folder():

    folder = os.path.join(
        current_app.static_folder,
        "uploads",
        "categories"
    )

    os.makedirs(
        folder,
        exist_ok=True
    )

    return folder


# ==========================================================
# GENERATE UNIQUE FILENAME
# ==========================================================

def get_unique_filename(
    upload_folder,
    filename
):

    filename = secure_filename(
        filename
    )

    base, extension = os.path.splitext(
        filename
    )

    final_filename = filename
    counter = 1

    while os.path.exists(
        os.path.join(
            upload_folder,
            final_filename
        )
    ):

        final_filename = (
            f"{base}_{counter}{extension}"
        )

        counter += 1

    return final_filename


# ==========================================================
# DELETE IMAGE FILE
# ==========================================================

def delete_image_file(filename):

    if not filename:
        return

    upload_folder = get_upload_folder()

    image_path = os.path.join(
        upload_folder,
        filename
    )

    if os.path.isfile(image_path):

        try:
            os.remove(image_path)

        except OSError:
            pass


# ==========================================================
# CATEGORY LIST
# ==========================================================

@admin_categories_bp.get("/")
def categories():

    rows = (
        Category.query
        .order_by(Category.id.desc())
        .all()
    )

    return render_template(
        "admin/categories/index.html",
        rows=rows,
        module="categories"
    )


# ==========================================================
# ADD CATEGORY
# ==========================================================

@admin_categories_bp.route(
    "/add",
    methods=["GET", "POST"]
)
def add_category():

    if request.method == "POST":

        # ==================================================
        # BASIC INFORMATION
        # ==================================================

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # ==================================================
        # VALIDATE NAME
        # ==================================================

        if not name:

            flash(
                "Category name is required.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin_categories.add_category"
                )
            )

        # ==================================================
        # CHECK DUPLICATE NAME
        # ==================================================

        existing_category = (
            Category.query
            .filter(
                db.func.lower(Category.name)
                == name.lower()
            )
            .first()
        )

        if existing_category:

            flash(
                "A category with this name already exists.",
                "danger"
            )

            return redirect(
                url_for(
                    "admin_categories.add_category"
                )
            )

        # ==================================================
        # IMAGE UPLOAD
        # ==================================================

        image = request.files.get(
            "image"
        )

        image_filename = None

        if image and image.filename:

            if not allowed_file(
                image.filename
            ):

                flash(
                    f"Invalid image format: {image.filename}",
                    "danger"
                )

                return redirect(
                    url_for(
                        "admin_categories.add_category"
                    )
                )

            upload_folder = get_upload_folder()

            image_filename = get_unique_filename(
                upload_folder,
                image.filename
            )

            image.save(
                os.path.join(
                    upload_folder,
                    image_filename
                )
            )

        # ==================================================
        # CREATE CATEGORY
        # ==================================================

        category = Category(
            name=name,
            image=image_filename,
            description=description
        )

        db.session.add(
            category
        )

        # ==================================================
        # SAVE
        # ==================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            if image_filename:
                delete_image_file(
                    image_filename
                )

            flash(
                f"Failed to add category: {str(e)}",
                "danger"
            )

            return redirect(
                url_for(
                    "admin_categories.add_category"
                )
            )

        flash(
            "Category added successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_categories.categories"
            )
        )

    # ======================================================
    # GET
    # ======================================================

    return render_template(
        "admin/categories/add.html",
        module="categories"
    )


# ==========================================================
# EDIT CATEGORY
# ==========================================================

@admin_categories_bp.route(
    "/edit/<int:category_id>",
    methods=["GET", "POST"]
)
def edit_category(category_id):

    category = db.session.get(
        Category,
        category_id
    )

    if not category:

        flash(
            "Category not found.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_categories.categories"
            )
        )

    # ======================================================
    # POST
    # ======================================================

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        # ==================================================
        # VALIDATE NAME
        # ==================================================

        if not name:

            flash(
                "Category name is required.",
                "danger"
            )

            return render_template(
                "admin/categories/edit.html",
                category=category,
                module="categories"
            )

        # ==================================================
        # CHECK DUPLICATE NAME
        # ==================================================

        existing_category = (
            Category.query
            .filter(
                db.func.lower(Category.name)
                == name.lower(),
                Category.id != category.id
            )
            .first()
        )

        if existing_category:

            flash(
                "A category with this name already exists.",
                "danger"
            )

            return render_template(
                "admin/categories/edit.html",
                category=category,
                module="categories"
            )

        # ==================================================
        # UPDATE BASIC INFORMATION
        # ==================================================

        category.name = name
        category.description = description

        # ==================================================
        # NEW IMAGE
        # ==================================================

        image = request.files.get(
            "image"
        )

        new_image_filename = None

        if image and image.filename:

            if not allowed_file(
                image.filename
            ):

                flash(
                    f"Invalid image format: {image.filename}",
                    "danger"
                )

                return render_template(
                    "admin/categories/edit.html",
                    category=category,
                    module="categories"
                )

            upload_folder = get_upload_folder()

            new_image_filename = get_unique_filename(
                upload_folder,
                image.filename
            )

            image.save(
                os.path.join(
                    upload_folder,
                    new_image_filename
                )
            )

            old_image = category.image

            category.image = new_image_filename

        else:

            old_image = None

        # ==================================================
        # SAVE
        # ==================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            if new_image_filename:
                delete_image_file(
                    new_image_filename
                )

            flash(
                f"Failed to update category: {str(e)}",
                "danger"
            )

            return render_template(
                "admin/categories/edit.html",
                category=category,
                module="categories"
            )

        # ==================================================
        # DELETE OLD IMAGE
        # ==================================================

        if (
            new_image_filename
            and old_image
            and old_image != new_image_filename
        ):

            delete_image_file(
                old_image
            )

        flash(
            "Category updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_categories.categories"
            )
        )

    # ======================================================
    # GET
    # ======================================================

    return render_template(
        "admin/categories/edit.html",
        category=category,
        module="categories"
    )


# ==========================================================
# DELETE CATEGORY
# ==========================================================

@admin_categories_bp.route(
    "/delete/<int:category_id>",
    methods=["POST"]
)
def delete_category(category_id):

    category = db.session.get(
        Category,
        category_id
    )

    if not category:

        flash(
            "Category not found.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_categories.categories"
            )
        )

    # ======================================================
    # CHECK PRODUCTS
    # ======================================================

    if category.products:

        flash(
            "Cannot delete this category because it contains products.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_categories.categories"
            )
        )

    # ======================================================
    # SAVE IMAGE NAME
    # ======================================================

    image_filename = category.image

    # ======================================================
    # DELETE CATEGORY
    # ======================================================

    try:

        db.session.delete(
            category
        )

        db.session.commit()

    except Exception as e:

        db.session.rollback()

        flash(
            f"Failed to delete category: {str(e)}",
            "danger"
        )

        return redirect(
            url_for(
                "admin_categories.categories"
            )
        )

    # ======================================================
    # DELETE IMAGE FILE
    # ======================================================

    if image_filename:

        delete_image_file(
            image_filename
        )

    flash(
        "Category deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "admin_categories.categories"
        )
    )