from datetime import datetime
from extensions import db


class Order(db.Model):
    __tablename__ = "orders"

    # Primary Key
    id = db.Column(db.Integer, primary_key=True)

    # Order Number
    order_id = db.Column(db.String(20), unique=True, nullable=False, index=True)

    # Customer
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)

    # Billing Information
    customer_name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(500), nullable=False)

    # Payment
    payment_method = db.Column(db.String(50), nullable=False)

    # Money
    subtotal = db.Column(db.Float, nullable=False, default=0)
    shipping = db.Column(db.Float, nullable=False, default=0)
    total = db.Column(db.Float, nullable=False, default=0)

    # Status
    status = db.Column(db.String(50), nullable=False, default="Processing")

    # Created Date
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order {self.order_id}>"
