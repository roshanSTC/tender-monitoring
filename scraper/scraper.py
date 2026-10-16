"""
scraper.py

Orchestrates scraping of SPMCIL, BRBNMPL, and BNPM tender sites.
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import TENDER_SITES, logger
from scraper.parsers.bnpm import parse_bnpm
from scraper.parsers.brbnmpl import parse_brbnmpl
from scraper.parsers.spmcil.corporate import parse_corporate_table
from scraper.parsers.spmcil.noida import parse_noida_page
from scraper.parsers.unit_sites import parse_unit_table
from utils.status import get_status


class TenderScraper:
    """HTTP client and scraper orchestrator for tender portals."""

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

    def fetch_page(self, url: str, site_name: str = "") -> str:
        """Fetch HTML content from a URL using configured retries and timeouts."""
        label = f"{site_name} ({url})" if site_name else url
        logger.info(f"Fetching {label}")

        response = self.session.get(
            url,
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.text

    def scrape(self, site: dict) -> list:
        """Scrape tenders for a single site definition."""
        site_type = site.get("type")
        site_name = site.get("name", "")

        # Sites with dedicated self-fetching parsers
        if site_type == "brbnmpl":
            tenders = parse_brbnmpl(site)
        elif site_type == "bnpm":
            tenders = parse_bnpm(site)
        else:
            html = self.fetch_page(site["url"], site_name)
            if site_type == "corporate":
                tenders = parse_corporate_table(html)
            elif site_name == "IGM Noida":
                tenders = parse_noida_page(html, site)
            else:
                tenders = parse_unit_table(html, site)

        # Standardize source metadata and status for all tenders
        for tender in tenders:
            tender.setdefault("Source", site_name)
            tender.setdefault("Source URL", site.get("url", ""))

            if "Status" not in tender or "Days Left" not in tender:
                status, days_left = get_status(tender.get("Closing Date", ""))
                tender.setdefault("Status", status)
                tender.setdefault("Days Left", days_left)

        return tenders

    def scrape_all(self, sites: list = None) -> list:
        """Scrape tenders across all configured sites."""
        target_sites = sites if sites is not None else TENDER_SITES
        all_tenders = []

        for site in target_sites:
            try:
                logger.info(f"Scraping: {site.get('name')}")
                tenders = self.scrape(site)
                all_tenders.extend(tenders)
                logger.info(f"{site.get('name')} -> {len(tenders)} tenders scraped")
            except Exception as e:
                logger.exception(f"Failed to scrape {site.get('name')}: {e}")

        return all_tenders


def get_tenders(sites: list = None) -> list:
    """Convenience function to scrape all tenders."""
    scraper = TenderScraper()
    return scraper.scrape_all(sites)


if __name__ == "__main__":
    tenders = get_tenders()
    print(f"\nTotal Scraped : {len(tenders)}")
    for tender in tenders[:5]:
        print(tender)