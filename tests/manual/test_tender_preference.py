from database.connection import SessionLocal

from models.user import User
from models.notification import Notification
from models.user_preference import UserPreference
from models.user_tender_preference import UserTenderPreference


db = SessionLocal()

try:

    user = db.query(User).first()

    if not user:

        print("No users found.")

    else:

        keyword = UserTenderPreference(
            user_id=user.id,
            preference_type="keyword",
            preference_value="Gold",
        )

        website = UserTenderPreference(
            user_id=user.id,
            preference_type="website",
            preference_value="SPMCIL Corporate",
        )

        db.add(keyword)
        db.add(website)

        db.commit()

        print("Tender preferences created successfully.")

        preferences = (
            db.query(UserTenderPreference)
            .filter(
                UserTenderPreference.user_id == user.id
            )
            .all()
        )

        for preference in preferences:

            print(
                preference.preference_type,
                "=>",
                preference.preference_value
            )

finally:

    db.close()