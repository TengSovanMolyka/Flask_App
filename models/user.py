from extensions import db


class User(db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    profile = db.Column(db.String(128), nullable=True, default="default-avatar.png")
    full_name = db.Column(db.String(128), nullable=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    contact = db.Column(db.String(128), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="User")
    status = db.Column(db.String(50), nullable=False, default="Active")

    # Orders relationship
    orders = db.relationship("Order", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"
