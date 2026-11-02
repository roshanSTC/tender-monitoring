"""
gepnic.py

Scraper parser for NIC GePNIC e-Procurement portals:
- https://etenders.gov.in/eprocure/app (Central eTenders)
- https://eprocure.gov.in/eprocure/app (Central Public Procurement Portal - CPPP)

Fetches active tenders directly via FrontEndTendersByOrganisation without CAPTCHA.
Uses parallel HTTP workers for high-speed extraction across all organizations.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin
import urllib3

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from utils.status import get_status, format_display_date

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _create_session() -> requests.Session:
    """Create a configured requests session with retries and browser headers."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


def _parse_org_tenders(
    session: requests.Session,
    org_name: str,
    target_url: str,
    site_name: str,
    base_url: str,
) -> List[Dict]:
    """Fetch and parse all active tenders for a single organization."""
    tenders = []
    try:
        resp = session.get(target_url, verify=False, timeout=25)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", {"id": "table"})
        if not table:
            return tenders

        rows = table.find_all("tr")
        for row in rows:
            cols = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]

            # Skip header, footer, or malformed rows
            if len(cols) < 5 or cols[0].lower() in ("s.no", "sl.no") or row.find("td", {"colspan": True}):
                continue

            raw_title_cell = cols[4]
            # GePNIC titles are structured: [Title] [Ref No][Tender ID]
            bracket_parts = re.findall(r"\[(.*?)\]", raw_title_cell)

            if bracket_parts:
                title = bracket_parts[0].strip()
                ref_no = bracket_parts[1].strip() if len(bracket_parts) > 1 else ""
                tender_id = bracket_parts[2].strip() if len(bracket_parts) > 2 else (bracket_parts[1].strip() if len(bracket_parts) > 1 else "")
            else:
                title = raw_title_cell.strip()
                ref_no = ""
                tender_id = ""

            # Best unique tender identifier
            tender_number = tender_id if tender_id else (ref_no if ref_no else f"GEPNIC_{cols[0]}")

            # Organisation Chain (Unit Name / Issuer)
            org_chain = cols[5].replace("||", " - ").strip() if len(cols) > 5 else org_name
            issued_by = org_chain if org_chain else org_name

            # Dates & Status
            raw_pub_date = cols[1] if len(cols) > 1 else ""
            raw_closing_date = cols[2] if len(cols) > 2 else ""

            status, days_left = get_status(raw_closing_date)
            pub_date = format_display_date(raw_pub_date)
            closing_date = format_display_date(raw_closing_date)

            # Document Link from <a> tag on title
            a_tag = row.find("a")
            doc_url = urljoin(base_url, a_tag.get("href", "")) if a_tag and a_tag.get("href") else ""

            tender = {
                "Source": site_name,
                "Source URL": base_url,
                "Unit Name": issued_by,
                "Issued By": issued_by,
                "Department Name And Address": issued_by,
                "Tender Number": tender_number,
                "Tender Title": title,
                "Matched Keyword": "-",
                "Publishing Date": pub_date,
                "Closing Date": closing_date,
                "Status": status,
                "Days Left": days_left,
                "Tender Document": "Download" if doc_url else "",
                "Tender Document URL": doc_url,
                "Corrigendum": "",
                "Corrigendum URL": "",
                "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            tenders.append(tender)

    except Exception as e:
        logger.warning(f"Failed to fetch tenders for '{org_name}' on {site_name}: {e}")

    return tenders


def parse_gepnic(site: Dict) -> List[Dict]:
    """
    Scrape all active tenders from a GePNIC portal across all organizations.
    Discovers active organizations and fetches their tenders concurrently.
    """
    site_name = site.get("name", "GePNIC Portal")
    base_url = site.get("url", "https://etenders.gov.in/eprocure/app")
    org_list_url = f"{base_url.rstrip('/')}?page=FrontEndTendersByOrganisation&service=page"

    print(f"\n[GePNIC Scraper] Starting fetch for: {site_name} (All Organizations)...")
    logger.info(f"Scraping GePNIC site: {site_name} at {org_list_url}")

    session = _create_session()
    all_tenders: List[Dict] = []
    seen_tenders = set()

    try:
        # Step 1: Fetch organization directory
        resp = session.get(org_list_url, verify=False, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        org_table = soup.find("table", {"id": "table"})
        if not org_table:
            logger.error(f"Could not find organizations table on {org_list_url}")
            print(f"[ERROR] Could not find organizations table on {site_name}")
            return []

        # Step 2: Collect all organizations with active tenders (> 0)
        org_tasks = []
        rows = org_table.find_all("tr")
        for row in rows[1:]:
            cols = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
            if len(cols) >= 3 and cols[2].isdigit():
                tender_count = int(cols[2])
                if tender_count > 0:
                    a_tag = row.find("a")
                    if a_tag and a_tag.get("href"):
                        target_url = urljoin(base_url, a_tag["href"])
                        org_tasks.append((cols[1], tender_count, target_url))

        total_expected = sum(t[1] for t in org_tasks)
        print(f"  -> Found {len(org_tasks)} active organizations ({total_expected} tenders expected). Fetching in parallel...")

        # Step 3: Fetch active tenders across organizations concurrently
        max_workers = min(10, max(4, len(org_tasks)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_org = {
                executor.submit(
                    _parse_org_tenders,
                    session,
                    org_name,
                    target_url,
                    site_name,
                    base_url,
                ): org_name
                for org_name, count, target_url in org_tasks
            }

            for future in as_completed(future_to_org):
                org_name = future_to_org[future]
                try:
                    org_tenders = future.result()
                    for t in org_tenders:
                        t_num = t["Tender Number"]
                        if t_num not in seen_tenders:
                            seen_tenders.add(t_num)
                            all_tenders.append(t)
                except Exception as exc:
                    logger.warning(f"Error processing {org_name}: {exc}")

    except Exception as e:
        logger.exception(f"GePNIC scraping failed for {site_name}: {e}")
        print(f"[ERROR] GePNIC scraper failed for {site_name}: {e}")

    print(f"[GePNIC Scraper] {site_name} completed. Total unique tenders extracted: {len(all_tenders)}")
    logger.info(f"{site_name} completed: {len(all_tenders)} tenders extracted")
    return all_tenders


if __name__ == "__main__":
    test_site = {
        "name": "eTenders Portal",
        "url": "https://etenders.gov.in/eprocure/app",
        "type": "gepnic"
    }
    tenders = parse_gepnic(test_site)
    print(f"\nTotal Tenders Scraped: {len(tenders)}")
    if tenders:
        print("Sample Tender:")
        for k, v in list(tenders[0].items())[:8]:
            print(f"  {k}: {v}")

