import os
import gspread

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets"
]

TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

SPREADSHEET_ID = "1VnXjcGSgIZM9FxN6w-vSsR-8glxhrdtOq5GGptbnNLM"


class GoogleSheet:

    def __init__(self):

        self.client = self.authenticate()

        self.sheet = self.client.open_by_key(
        SPREADSHEET_ID
        ).worksheet("Tenders")

    # --------------------------------------------------

    def authenticate(self):

        creds = None

        if os.path.exists(TOKEN_FILE):

            creds = Credentials.from_authorized_user_file(
                TOKEN_FILE,
                SCOPES
            )

        if not creds or not creds.valid:

            if creds and creds.expired and creds.refresh_token:

                creds.refresh(Request())

            else:

                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE,
                    SCOPES
                )

                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, "w") as token:

                token.write(
                    creds.to_json()
                )

        return gspread.authorize(creds)
    
    def create_sheet(self):

        headers = [
            "Source",
            "Unit Name",
            "Tender Number",
            "Tender Title",
            "Publishing Date",
            "Closing Date",
            "Tender Document URL",
            "Corrigendum URL",
            "Scraped At"
        ]

        values = self.sheet.get_all_values()

        # Completely empty sheet
        if not values:
            self.sheet.append_row(headers)
            print("Header created.")
            return

        # First row exists but is empty
        if not values[0]:
            self.sheet.update("A1:K1", [headers])
            print("Header created.")
            return

        # Header already exists
        if values[0][0] == "Source":
            print("Header already exists.")
            return

        # First row contains data instead of headers
        self.sheet.insert_row(headers, 1)
        print("Header inserted.")    
    
    def get_existing_tenders(self):

        values = self.sheet.get_all_values()

        existing = set()

        # Skip header
        for row in values[1:]:

            if len(row) < 3:
                continue

            source = row[0].strip()
            tender_no = row[2].strip()

            if source and tender_no:

                existing.add(f"{source}|{tender_no}")

        return existing
    
    
    def save_to_sheet(self, tenders):

        existing = self.get_existing_tenders()

        rows = []

        inserted = 0

        for tender in tenders:

            key = f"{tender['Source']}|{tender['Tender Number']}"

            if key in existing:
                continue

            rows.append([

                tender["Source"],
                tender["Unit Name"],
                tender["Tender Number"],
                tender["Tender Title"],
                tender["Publishing Date"],
                tender["Closing Date"],
                tender["Tender Document URL"],
                tender["Corrigendum URL"],
                tender["Scraped At"]

            ])

            inserted += 1

        if rows:

            self.sheet.append_rows(rows)

        print(f"Inserted {inserted} new tenders.")  