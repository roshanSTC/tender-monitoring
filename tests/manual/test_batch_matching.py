from services.matching_service import (
    get_matching_users_for_tenders
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


results = get_matching_users_for_tenders(
    test_tenders
)


print("\nBatch Matching Results")
print("======================")

print(
    f"Matched Users: {len(results)}"
)

for user_id, data in results.items():

    user = data["user"]
    tenders = data["tenders"]

    print(
        f"\nUser: {user.email}"
    )

    print(
        f"Matching Tenders: {len(tenders)}"
    )

    for tender in tenders:

        print(
            f"  - {tender['Tender Number']} | "
            f"{tender['Tender Title']}"
        )