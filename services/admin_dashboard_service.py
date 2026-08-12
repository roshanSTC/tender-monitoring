from models.user import User


class AdminDashboardService:

    @staticmethod
    def get_dashboard(db):

        total_users = db.query(User).count()

        active_users = (
            db.query(User)
            .filter(User.status == "ACTIVE")
            .count()
        )

        pending_users = (
            db.query(User)
            .filter(User.status == "INVITED")
            .count()
        )

        disabled_users = (
            db.query(User)
            .filter(User.status == "DISABLED")
            .count()
        )

        recent_users = (
            db.query(User)
            .order_by(User.created_at.desc())
            .limit(5)
            .all()
        )

        recent = []

        for user in recent_users:

            recent.append({

                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "status": user.status,
                "created_at": user.created_at.isoformat(),

            })

        return {

            "summary": {

                "total_users": total_users,
                "active_users": active_users,
                "pending_invitations": pending_users,
                "disabled_users": disabled_users,

            },

            "recent_invitations": recent,

        }