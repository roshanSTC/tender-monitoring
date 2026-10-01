from database.connection import SessionLocal

# Important: load both models
from models.user import User
from models.notification import Notification


db = SessionLocal()

try:

    existing = db.query(User).filter(User.email == "roshan.tambe@stcpl.com").first()
    if existing:
        print("User already exists:")
        print(f"ID    : {existing.id}")
        print(f"Name  : {existing.name}")
        print(f"Email : {existing.email}")
        print(f"Status: {existing.status}")
        print(f"Role  : {existing.role}")
    else:
        from utils.password import hash_password
        user = User(
            name="Roshan Tambe",
            email="roshan.tambe@stcpl.com",
            role="ADMIN",
            status="ACTIVE",
            password_hash=hash_password("Admin@123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print("User created successfully.")
        print(f"ID    : {user.id}")
        print(f"Name  : {user.name}")
        print(f"Email : {user.email}")

except Exception as e:

    db.rollback()

    print(f"Error: {e}")

finally:

    db.close()