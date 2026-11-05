from extensions import db


class Product(db.Model):
    __tablename__ = "products"

    # ==========================================================
    # PRIMARY KEY
    # ==========================================================

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ==========================================================
    # BASIC INFORMATION
    # ==========================================================

    name = db.Column(
        db.String(255),
        nullable=False
    )

    type = db.Column(
        db.String(100),
        nullable=True
    )

    brand = db.Column(
        db.String(100),
        nullable=True
    )

    is_new = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    # ==========================================================
    # IMAGE
    # ==========================================================

    thumbnail = db.Column(
        db.String(255),
        nullable=True
    )

    # ==========================================================
    # PRICING
    # ==========================================================

    cost = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    old_price = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    price = db.Column(
        db.Numeric(10, 2),
        nullable=False
    )

    discounted_price = db.Column(
        db.Numeric(10, 2),
        nullable=True
    )

    # ==========================================================
    # INVENTORY
    # ==========================================================

    stock = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    rating = db.Column(
        db.Numeric(2, 1),
        nullable=False,
        default=0
    )

    size = db.Column(
        db.JSON,
        nullable=True
    )

    # ==========================================================
    # CATEGORY
    # ==========================================================

    category_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "categories.id"
        ),
        nullable=False
    )

    # ==========================================================
    # DESCRIPTION
    # ==========================================================

    description = db.Column(
        db.Text,
        nullable=True
    )

    # ==========================================================
    # RELATIONSHIPS
    # ==========================================================

    category = db.relationship(
        "Category",
        back_populates="products"
    )

    images = db.relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    # ==========================================================
    # REPRESENTATION
    # ==========================================================

    def __repr__(self):
        return f"<Product {self.id}: {self.name}>"