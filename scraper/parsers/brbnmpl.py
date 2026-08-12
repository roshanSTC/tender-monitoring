from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from utils.date_utils import normalize_tender_date
import requests


def parse_brbnmpl(site):

        tenders = []
        seen = set()

        response = requests.get(site["url"], timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")


        for table in tables:

            rows = table.find_all("tr")

            if len(rows) < 2:
                continue

            header_text = rows[0].get_text(" ", strip=True).lower()

            if "tender no" not in header_text:
                continue


            for row in rows[1:]:

                cols = row.find_all(["td", "th"])

                if len(cols) < 5:
                    continue

                tender_no = cols[1].get_text(strip=True)

                if not tender_no:
                    continue

                key = f"BRBNMPL|{tender_no}"

                if key in seen:
                    continue

                seen.add(key)

                open_date = cols[2].get_text(strip=True)

                title_col = cols[3]

                closing_date = cols[4].get_text(strip=True)

                title = title_col.get_text(" ", strip=True)

                tender_url = ""

                link = title_col.find("a")

                if link and link.get("href"):
                    tender_url = urljoin(site["url"], link["href"])

                tenders.append({

                    "Source": "BRBNMPL",
                    "Source URL": site["url"],
                    "Unit Name": "BRBNMPL",
                    "Tender Number": tender_no,
                    "Tender Title": title,
                    "Publishing Date": normalize_tender_date(open_date),
                    "Closing Date": normalize_tender_date(closing_date),
                    "Tender": "Download" if tender_url else "",
                    "Tender URL": tender_url,
                    "Corrigendum": "",
                    "Corrigendum URL": ""

                })

            # Stop after parsing the first valid tender table
            break


        return tenders

