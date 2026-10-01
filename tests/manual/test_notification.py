from database.connection import SessionLocal
from models.user import User
from models.notification import Notification


db = SessionLocal()

try:

    # --------------------------------------------------
    # Find an existing user
    # --------------------------------------------------

    user = db.query(User).first()

    if not user:
        print("No users found in the database.")
        print("Create a user first.")
        exit()

    print(f"Using User:")
    print(f"ID    : {user.id}")
    print(f"Name  : {user.name}")
    print(f"Email : {user.email}")

    # --------------------------------------------------
    # Create test notification
    # --------------------------------------------------

    notification = Notification(
        user_id=user.id,
        type="test",
        title="Test Notification",
        message="This is a test notification from the backend.",
        reference_type=None,
        reference_id=None,
        is_read=False
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    print("\nNotification created successfully.")

    print(f"Notification ID : {notification.id}")
    print(f"User ID         : {notification.user_id}")
    print(f"Title           : {notification.title}")
    print(f"Read            : {notification.is_read}")

    # --------------------------------------------------
    # Test relationship
    # --------------------------------------------------

    print("\nTesting User → Notifications relationship...")

    user_notification = user.notifications[-1]

    print(f"Notification ID : {user_notification.id}")
    print(f"Title           : {user_notification.title}")
    print(f"User            : {user_notification.user.name}")

    print("\nRelationship working successfully.")

except Exception as e:

    db.rollback()

    print(f"Error: {e}")

finally:

    db.close()