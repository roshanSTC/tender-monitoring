from datetime import datetime
from urllib.parse import urljoin
from config import logger

from bs4 import BeautifulSoup

from utils.status import get_status
from utils.date_utils import normalize_tender_date




def  parse_corporate_table( html):

        soup = BeautifulSoup(html, "lxml")

        table = soup.find("table")

        if table is None:
            raise Exception("Tender table not found.")

        rows = table.find_all("tr")

        tenders = []

        base_url = "https://www.spmcil.com"

        for row in rows[1:]:

            cols = row.find_all("td")

            if len(cols) < 8:
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
            # Tender
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

                "Tender Number": cols[2].get_text(strip=True),

                "Tender Title": cols[3].get_text(
                    " ",
                    strip=True
                ),

                "Publishing Date": normalize_tender_date(cols[4].get_text(
                    " ",
                    strip=True
                )),

                "Closing Date": normalize_tender_date(cols[5].get_text(
                    " ",
                    strip=True
                )),
                
                "Status": status,
                
                "Days Left": days_left,
                
                "Corrigendum": corrigendum_text,

                "Corrigendum URL": corrigendum_url,

                "Tender": tender_doc_text,

                "Tender URL": tender_doc_url
            }

            tenders.append(tender)

        logger.info(f"Fetched {len(tenders)} tenders")

        return tenders


        # --------------------------------------------------------
    
  