from datetime import datetime
from urllib.parse import urljoin
from config import logger

from bs4 import BeautifulSoup

from utils.status import get_status


def parse_unit_table(html, site):

        soup = BeautifulSoup(html, "lxml")

        table = soup.find("table")

        if table is None:
            raise Exception("Tender table not found.")

        rows = table.find_all("tr")

        tenders = []

        for row in rows[1:]:

            cols = row.find_all("td")

            # Skip invalid rows
            if len(cols) < 7:
                continue

            # ---------------------------------
            # Tender Document
            # ---------------------------------

            tender_doc = ""
            tender_doc_url = ""

            link = cols[0].find("a")

            if link:
                tender_doc = link.get_text(" ", strip=True)
                tender_doc_url = urljoin(
                    site["url"],
                    link.get("href", "")
                )

            # ---------------------------------
            # Corrigendum
            # ---------------------------------

            corr_text = ""
            corr_url = ""

            link = cols[6].find("a")

            if link:
                corr_text = link.get_text(" ", strip=True)
                corr_url = urljoin(
                    site["url"],
                    link.get("href", "")
                )
                
            status, days_left = get_status(
                cols[5].get_text(" ", strip=True)
            )

            tender = {

                "Unit Name": cols[1].get_text(" ", strip=True),

                "Tender Number": cols[2].get_text(" ", strip=True),

                "Tender Title": cols[3].get_text(" ", strip=True),

                "Publishing Date": cols[4].get_text(" ", strip=True),

                "Closing Date": cols[5].get_text(" ", strip=True),
                
                "Status": status,

                "Days Left": days_left,

                "Tender Document": tender_doc,

                "Tender Document URL": tender_doc_url,

                "Corrigendum": corr_text,

                "Corrigendum URL": corr_url,

                "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            }

            tenders.append(tender)

        logger.info(
            f"{site['name']} -> Parsed {len(tenders)} tenders"
        )

        return tenders

