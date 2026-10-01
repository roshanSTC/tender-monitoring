from services.matching_service import (
    get_matching_users_for_tenders
)

from services.notification_service import (
    prepare_batch_notifications
)


test_tenders = [

    {
        "id": 10001,
        "Source": "SPMCIL Corporate",
        "Tender Number": "TEST-001",
        "Tender Title": "Supply of Gold Coins",
    },

    {
        "id": 10002,
        "Source": "SPMCIL Corporate",
        "Tender Number": "TEST-002",
        "Tender Title": "Procurement of Gold Bars",
    },

    {
        "id": 10003,
        "Source": "IGM Mumbai",
        "Tender Number": "TEST-003",
        "Tender Title": "Office Furniture",
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


print("\nBatch Notification Payload")
print("==========================")

print(
    f"Total Users: {len(batches)}"
)


for batch in batches:

    print(
        f"\nUser       : {batch['email']}"
    )

    print(
        f"Tender Count: {batch['tender_count']}"
    )

    for tender in batch["tenders"]:

        print(
            f"  - {tender['Tender Number']} | "
            f"{tender['Tender Title']}"
        )