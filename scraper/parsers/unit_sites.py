from datetime import datetime
from urllib.parse import urljoin
from config import logger

from bs4 import BeautifulSoup

from utils.status import get_status, parse_date


def parse_unit_table(html, site):

        soup = BeautifulSoup(html, "lxml")

        table = soup.find("table")

        if table is None:
            raise Exception("Tender table not found.")

        rows = table.find_all("tr")

        seen_tenders = {}

        for row in rows[1:]:

            cols = row.find_all("td")

            # Skip invalid rows
            if len(cols) < 7:
                continue

            tender_no = cols[2].get_text(" ", strip=True)
            if not tender_no:
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

                "Tender Number": tender_no,

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

            if tender_no in seen_tenders:
                existing_entry = seen_tenders[tender_no]
                dt_new = parse_date(tender["Closing Date"])
                dt_old = parse_date(existing_entry["Closing Date"])
                if (dt_new and dt_old and dt_new > dt_old) or (corr_url and not existing_entry.get("Corrigendum URL")):
                    seen_tenders[tender_no] = tender
                continue

            seen_tenders[tender_no] = tender

        tenders = list(seen_tenders.values())

        logger.info(
            f"{site['name']} -> Parsed {len(tenders)} tenders"
        )

        return tenders

