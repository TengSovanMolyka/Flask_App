from extensions import db


class OrderItem(db.Model):
    __tablename__ = "order_items"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Order
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)

    # Product Information
    product_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    image = db.Column(db.String(500), nullable=True)

    # Product Price Snapshot
    price = db.Column(db.Float, nullable=False)
    discounted_price = db.Column(db.Float, nullable=False)

    # Cart Information
    quantity = db.Column(db.Integer, nullable=False)
    size = db.Column(db.String(50), nullable=True)

    # Relationship
    order = db.relationship("Order", back_populates="items")

    @property
    def line_total(self) -> float:
        return self.discounted_price * self.quantity

    def __repr__(self):
        return f"<OrderItem {self.title}>"
