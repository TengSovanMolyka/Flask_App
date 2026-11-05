from extensions import db


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "products.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    name = db.Column(
        db.String(255),
        nullable=False
    )

    product = db.relationship(
        "Product",
        back_populates="images"
    )

    def __repr__(self):
        return f"<ProductImage {self.id}: {self.name}>"