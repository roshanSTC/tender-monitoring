"""
scraper.py

Scrapes SPMCIL tenders and stores them in an Excel file.
"""

from datetime import datetime


import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import TENDER_SITES, logger


from datetime import datetime

from scraper.parsers.bnpm import parse_bnpm
from scraper.parsers.brbnmpl import parse_brbnmpl
from scraper.parsers.spmcil.corporate import parse_corporate_table
from scraper.parsers.spmcil.noida import parse_noida_page
from scraper.parsers.unit_sites import parse_unit_table



    
    

class TenderScraper:

    def __init__(self):

        self.session = requests.Session()

        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
        )

        adapter = HTTPAdapter(max_retries=retries)

        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/137.0 Safari/537.36"
            )
        }

    # --------------------------------------------------------

    def fetch_page(self, url, site_name ):

        logger.info(f"Fetching {url}")

        response = self.session.get(
            url,
            headers=self.headers,
            timeout=30
        )

        response.raise_for_status()
        
       

        return response.text

# --------------------------------------------------------
    
    def get_existing_tenders(self):

        wb = load_workbook(EXCEL_FILE)

        ws = wb.active

        existing = set()

        for row in ws.iter_rows(min_row=2, values_only=True):

            source = str(row[0]).strip() if row[0] else ""

            tender_no = str(row[2]).strip() if row[2] else ""

            if source and tender_no:

                existing.add(f"{source}|{tender_no}")

        wb.close()

        return existing

    # --------------------------------------------------------
    # --------------------------------------------------------

    def scrape(self, site):

        html = self.fetch_page(site["url"], site["name"])

        if site["type"] == "corporate":
            tenders = parse_corporate_table(html)

        elif site["name"] == "IGM Noida":
            tenders = parse_noida_page(html, site)
        
        elif site["type"] == "brbnmpl":
            return parse_brbnmpl(site)

        elif site["type"] == "bnpm":
            return parse_bnpm(site)

        else:
            tenders = parse_unit_table(html, site)

        # Add source information to every tender
        for tender in tenders:
            tender["Source"] = site["name"]
            tender["Source URL"] = site["url"]

        return tenders


# --------------------------------------------------------

def get_tenders():

    scraper = TenderScraper()

    return scraper.scrape()


# --------------------------------------------------------

if __name__ == "__main__":

    tenders = get_tenders()

    print(f"\nTotal Scraped : {len(tenders)}")

    for tender in tenders:
        print(tender)