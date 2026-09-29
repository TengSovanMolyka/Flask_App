from extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(255), nullable=False)

    is_new = db.Column(db.Boolean, nullable=False, default=False)

    old_price = db.Column(db.Numeric(10, 2), nullable=True)

    price = db.Column(db.Numeric(10, 2), nullable=False)

    discounted_price = db.Column(db.Numeric(10, 2), nullable=True)

    description = db.Column(db.Text, nullable=True)

    category = db.Column(db.String(100), nullable=False)

    type = db.Column(db.String(100), nullable=False)

    stock = db.Column(db.Integer, nullable=False, default=0)

    brand = db.Column(db.String(150), nullable=True)

    size = db.Column(db.JSON, nullable=True)

    image = db.Column(db.String(500), nullable=True)

    rating = db.Column(db.Float, nullable=False, default=0)

    def __repr__(self):
        return f"<Product {self.id}: {self.title}>"