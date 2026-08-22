import os

class Config:

    # ==========================================
    # Flask
    # ==========================================
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-this"
    )

    # ==========================================
    # Database
    # ==========================================
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///FlaskApp.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ==========================================
    # Uploads
    # ==========================================
    UPLOAD_FOLDER = os.path.join("static", "uploads", "profile")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # ==========================================
    # Telegram
    # ==========================================
    TELEGRAM_TOKEN = os.environ.get(
        "TELEGRAM_TOKEN",
        ""
    )

    TELEGRAM_CHAT_ID = os.environ.get(
        "TELEGRAM_CHAT_ID",
        ""
    )
