from app import app
from extensions import db
from models.user import User
from werkzeug.security import generate_password_hash


with app.app_context():

    user = User.query.filter_by(
        username="luka"
    ).first()

    if not user:
        print("❌ User 'luka' not found.")

    else:
        new_password = "Admin123!"

        user.password = generate_password_hash(
            new_password
        )

        user.role = "Admin"
        user.status = "Active"

        db.session.commit()

        print("================================")
        print("✅ ADMIN PASSWORD RESET")
        print("Username :", user.username)
        print("Password :", new_password)
        print("Role     :", user.role)
        print("Status   :", user.status)
        print("================================")