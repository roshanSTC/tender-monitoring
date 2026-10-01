from database.connection import SessionLocal
from models import User
from services.matching_service import (
    get_matching_users_for_tenders
)

from services.notification_service import (
    prepare_batch_notifications,
    create_batch_in_app_notifications,
    send_batch_emails,
)

db = SessionLocal()


test_tenders = [
    {
        "id": 88063,
        "Source": "SPMCIL Corporate",
        "Tender Number": "TEST-006",
        "Tender Title": "Supply of Gold Coins Batch Test",
    },
    {
        "id": 88064,
        "Source": "SPMCIL Corporate",
        "Tender Number": "TEST-007",
        "Tender Title": "Procurement of Gold Bars Batch Test",
    },
]


# Step A
matched_users = get_matching_users_for_tenders(
    test_tenders
)


print("TEST TENDERS:")
for tender in test_tenders:
    print(
        tender["id"],
        tender["Tender Number"],
        tender["Tender Title"]
    )

print("TOTAL TEST TENDERS:", len(test_tenders))


try:
    user = (
        db.query(User)
        .filter(User.id == 1)
        .first()
    )

    matched_users = [user]

finally:
    db.close()


# Step B
batches = prepare_batch_notifications(
    matched_users, test_tenders
)

print("\nBATCH DETAILS")

for batch in batches:

    print(
        f"User {batch['user_id']} "
        f"has {len(batch['tenders'])} tenders"
    )

    for tender in batch["tenders"]:

        print(
            f"  INCLUDED: "
            f"{tender['id']} | "
            f"{tender['Tender Number']} | "
            f"{tender['Tender Title']}"
        )


# Step C
results = create_batch_in_app_notifications(
    batches
)


print("\nBatch In-App Notification Results")
print("=================================")

for result in results:

    print(
        f"User ID          : {result['user_id']}"
    )

    print(
        f"Tender Count     : {result['tender_count']}"
    )

    print(
        f"Notification Made: "
        f"{result['notification_created']}"
    )
    
    
# Step D
email_results = send_batch_emails(
    batches
)

print("\nBatch Email Results")
print("===================")

for result in email_results:

    print(
        f"User ID     : {result['user_id']}"
    )

    print(
        f"Email       : {result['email']}"
    )

    print(
        f"Tender Count: {result['tender_count']}"
    )

    print(
        f"Email Sent  : {result['email_sent']}"
    )