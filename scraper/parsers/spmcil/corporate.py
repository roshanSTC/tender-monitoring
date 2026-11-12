from datetime import datetime
from urllib.parse import urljoin
from config import logger

from bs4 import BeautifulSoup

from utils.status import get_status, parse_date


def parse_corporate_table(html):

        soup = BeautifulSoup(html, "lxml")

        table = soup.find("table")

        if table is None:
            raise Exception("Tender table not found.")

        rows = table.find_all("tr")

        seen_tenders = {}

        base_url = "https://www.spmcil.com"

        for row in rows[1:]:

            cols = row.find_all("td")

            if len(cols) < 8:
                continue

            tender_no = cols[2].get_text(strip=True)
            if not tender_no:
                continue

            # -----------------------------
            # Corrigendum
            # -----------------------------

            corrigendum_text = ""
            corrigendum_url = ""

            corrigendum_link = cols[6].find("a")

            if corrigendum_link:

                corrigendum_text = corrigendum_link.get_text(
                    " ",
                    strip=True
                )

                corrigendum_url = urljoin(
                    base_url,
                    corrigendum_link.get("href", "")
                )

            # -----------------------------
            # Tender Document
            # -----------------------------

            tender_doc_text = ""
            tender_doc_url = ""

            tender_doc_link = cols[7].find("a")

            if tender_doc_link:

                tender_doc_text = tender_doc_link.get_text(
                    " ",
                    strip=True
                )

                tender_doc_url = urljoin(
                    base_url,
                    tender_doc_link.get("href", "")
                )
                
            closing_date = cols[5].get_text(" ", strip=True)

            status, days_left = get_status(closing_date)

            tender = {

                "Unit Name": cols[1].get_text(" ", strip=True),

                "Tender Number": tender_no,

                "Tender Title": cols[3].get_text(
                    " ",
                    strip=True
                ),

                "Publishing Date": cols[4].get_text(
                    " ",
                    strip=True
                ),

                "Closing Date": cols[5].get_text(
                    " ",
                    strip=True
                ),
                
                "Status": status,
                
                "Days Left": days_left,
                
                "Corrigendum": corrigendum_text,

                "Corrigendum URL": corrigendum_url,

                "Tender Document": tender_doc_text,

                "Tender Document URL": tender_doc_url,

                "Scraped At": datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

            if tender_no in seen_tenders:
                existing_entry = seen_tenders[tender_no]
                dt_new = parse_date(tender["Closing Date"])
                dt_old = parse_date(existing_entry["Closing Date"])
                if (dt_new and dt_old and dt_new > dt_old) or (corrigendum_url and not existing_entry.get("Corrigendum URL")):
                    seen_tenders[tender_no] = tender
                continue

            seen_tenders[tender_no] = tender

        tenders = list(seen_tenders.values())
        logger.info(f"Fetched {len(tenders)} tenders")

        return tenders


        # --------------------------------------------------------
    
  