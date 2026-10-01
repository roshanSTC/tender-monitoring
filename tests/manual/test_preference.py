from database.connection import SessionLocal

from models.user import User
from models.notification import Notification
from models.user_preference import UserPreference


db = SessionLocal()

try:

    user = db.query(User).first()

    if not user:

        print("No users found.")

    else:

        preference = UserPreference(
            user_id=user.id,
            in_app_enabled=True,
            email_enabled=True,
        )

        db.add(preference)
        db.commit()
        db.refresh(preference)

        print("Preference created successfully.")

        print(
            "User:",
            user.email
        )

        print(
            "In-app:",
            preference.in_app_enabled
        )

        print(
            "Email:",
            preference.email_enabled
        )

finally:

    db.close()