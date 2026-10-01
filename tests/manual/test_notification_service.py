from services.notification_service import (
    create_tender_notifications,
)


tender = {
    "id": 1003,
    "Source": "SPMCIL Corporate",
    "Tender Number": "NOTIFICATION-TEST-1002",
    "Tender Title": "Supply of Gold Coins",
    "Unit Name": "Test Unit",
    "Publishing Date": "2026-08-01",
    "Closing Date": "2026-08-10",
    "Tender": "Tender Document",
    "Tender URL": "https://example.com/tender",
    "Corrigendum": "",
    "Corrigendum URL": "",
}


results = create_tender_notifications(tender)


print("\nNotification Service Results")
print("============================")

for result in results:

    print(
        f"User       : {result['email']}"
    )

    print(
        f"In-app     : "
        f"{result['notification_created']}"
    )

    print(
        f"Email sent : "
        f"{result['email_sent']}"
    )

    print("----------------------------")