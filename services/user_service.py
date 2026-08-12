from models.user import User


class UserService:

    @staticmethod
    def get_all_users(db):

        users = (
            db.query(User)
            .order_by(User.created_at.desc())
            .all()
        )

        return users
    
    @staticmethod
    def update_status(
        db,
        user_id,
        status,
    ):
        print(f"Status received: '{status}'")
        print(type(status))
        
        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise ValueError("User not found.")

        allowed = [
            "ACTIVE",
            "DISABLED",
        ]

        if status not in allowed:
            raise ValueError(
                f"Invalid status: {status}"
            )

        user.status = status

        db.commit()
        db.refresh(user)

        return user
    

    @staticmethod
    def delete_user(db, user_id):

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            raise ValueError("User not found.")

        db.delete(user)

        db.commit()