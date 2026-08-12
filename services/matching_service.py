from database.connection import SessionLocal

from models import (
    User,
    UserTenderPreference,
)


def get_matching_users(tender):
    """
    Find active users whose tender preferences
    match the supplied tender.
    """

    db = SessionLocal()

    try:

        users = (
            db.query(User)
            # .filter(User.is_active == True)
            .all()
        )

        matched_users = []

        tender_title = (
            tender.get("Tender Title", "") or ""
        ).lower()

        tender_source = (
            tender.get("Source", "") or ""
        ).lower()

        for user in users:

            preferences = (
                db.query(UserTenderPreference)
                .filter(
                    UserTenderPreference.user_id == user.id,
                    UserTenderPreference.is_active.is_(True)
                )
                .all()
            )
            
            print("\nUSER PREFERENCES")

            for preference in preferences:

                print(
                    preference.preference_type,
                    "=>",
                    preference.preference_value
                )

            keyword_preferences = [
                p.preference_value.lower()
                for p in preferences
                if p.preference_type == "keyword"
            ]

            website_preferences = [
                p.preference_value.lower()
                for p in preferences
                if p.preference_type == "website"
            ]

            keyword_match = False
            website_match = False

            # Keyword matching
            for keyword in keyword_preferences:

                if keyword in tender_title:

                    keyword_match = True
                    break

            # Website/source matching
            for website in website_preferences:

                if website in tender_source:

                    website_match = True
                    break

            # User matches if either preference matches
            if keyword_match or website_match:

                matched_users.append(user)

        return matched_users

    finally:

        db.close()
        

def get_matching_users_for_tenders(tenders):
    """
    Match multiple new tenders against all active users.

    Returns:
        {
            user_id: {
                "user": User object,
                "tenders": [tender_dict, ...]
            }
        }
    """

    db = SessionLocal()

    try:

        if not tenders:
            return {}

        users = (
            db.query(User)
            # .filter(User.is_active == True)
            .all()
        )

        matches = {}

        for user in users:

            preferences = (
                db.query(UserTenderPreference)
                .filter(
                    UserTenderPreference.user_id == user.id,
                    UserTenderPreference.is_active.is_(True)
                )
                .all()
            )

            keyword_preferences = [
                p.preference_value.lower().strip()
                for p in preferences
                if p.preference_type == "keyword"
                and p.preference_value
            ]

            website_preferences = [
                p.preference_value.lower().strip()
                for p in preferences
                if p.preference_type == "website"
                and p.preference_value
            ]

            matched_tenders = []

            for tender in tenders:

                tender_title = (
                    tender.get("Tender Title", "") or ""
                ).lower()

                tender_source = (
                    tender.get("Source", "") or ""
                ).lower()

                keyword_match = any(
                    keyword in tender_title
                    for keyword in keyword_preferences
                )

                website_match = any(
                    website in tender_source
                    for website in website_preferences
                )

                if keyword_match or website_match:

                    matched_tenders.append(tender)

            if matched_tenders:

                matches[user.id] = {
                    "user": user,
                    "tenders": matched_tenders,
                }

        return matches

    finally:

        db.close()