from services.matching_service import (
    get_matching_users_for_tenders
)

from services.notification_service import (
    prepare_batch_notifications,
    send_batch_emails,
)


test_tenders = [

    {
        "id": 10001,
        "Source": "SPMCIL Corporate",
        "Tender Number": "TEST-001",
        "Tender Title": "Supply of Gold Coins",
        "Closing Date": "2026-08-10",
    },

    {
        "id": 10002,
        "Source": "SPMCIL Corporate",
        "Tender Number": "TEST-002",
        "Tender Title": "Procurement of Gold Bars",
        "Closing Date": "2026-08-12",
    },

    {
        "id": 10003,
        "Source": "IGM Mumbai",
        "Tender Number": "TEST-003",
        "Tender Title": "Office Furniture",
        "Closing Date": "2026-08-15",
    },

]


# Step A
matched_users = get_matching_users_for_tenders(
    test_tenders
)


# Step B
batches = prepare_batch_notifications(
    matched_users
)


# Step D
results = send_batch_emails(
    batches
)


print("\nBatch Email Results")
print("===================")

for result in results:

    print(
        f"User         : {result['email']}"
    )

    print(
        f"Tender Count : {result['tender_count']}"
    )

    print(
        f"Email Sent   : {result['email_sent']}"
    )

    print("-------------------")