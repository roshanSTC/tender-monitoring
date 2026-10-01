from database.connection import SessionLocal

from models.user import User
from models.notification import Notification

from utils.password import hash_password


db = SessionLocal()

try:

    user = (
        db.query(User)
        .filter(
            User.email == "test@example.com"
        )
        .first()
    )

    if not user:

        print("User not found.")

    else:

        user.password_hash = hash_password(
            "Test@123"
        )

        db.commit()

        print("Password updated successfully.")

finally:

    db.close()