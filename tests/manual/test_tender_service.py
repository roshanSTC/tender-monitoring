from services.tender_service import save_new_tenders


test_tenders = [

    {
        "Source": "SPMCIL Corporate",
        "Tender Number": "TEST-001",
        "Tender Title": "Test Gold Tender",
        "Unit Name": "Corporate",
        "Publishing Date": "01-08-2026",
        "Closing Date": "10-08-2026",
        "Tender": "https://example.com/Tender.pdf",
        "Tender URL": "https://example.com/tender/TEST-001",
    },

]


new_tenders = save_new_tenders(
    test_tenders
)


print("\nTender Storage Test")
print("===================")

for tender in new_tenders:

    print(
        f"ID             : {tender.id}"
    )

    print(
        f"Source         : {tender.source}"
    )

    print(
        f"Tender Number  : {tender.tender_number}"
    )

    print(
        f"Title          : {tender.title}"
    )

    print(
        f"Created At     : {tender.created_at}"
    )