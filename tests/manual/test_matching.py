from services.matching_service import get_matching_users


class TestTender:

    def __init__(
        self,
        title,
        source,
    ):
        self.title = title
        self.source = source


tender = TestTender(
    title="Supply of Gold Coins",
    source="SPMCIL Corporate",
)


matched_users = get_matching_users(tender)


print("\nMatched Users:")
print("-------------------------")

for user in matched_users:

    print(
        user.id,
        user.email
    )

print("-------------------------")
print(
    "Total matches:",
    len(matched_users)
)