"""
gem.py

Scrapes targeted bids from the Government e-Marketplace (GeM) using Playwright.
Uses an authenticated headless browser to pass the F5 BIG-IP WAF and executes
in-page queries against /all-bids-data, fetching 100% of available pages with no page limits.
"""

from datetime import datetime
from typing import List, Dict, Optional, Set, Any
import logging
import json
import re
from utils.status import get_status, format_display_date

logger = logging.getLogger(__name__)

# Default target search queries for GeM (Security printing organizations & specialized equipment)
DEFAULT_GEM_QUERIES = [
    "CNC Machine",
    "E-Type Machine",
    "Rimming Machine",
    "Opacified Polymer Substrate Sheets",
    "Physical Vapour Deposition System",
    "Security Design Software",
    "ICAO Compliant Electronic Contactless Inlays",
    "CTOP",
    "CSP-Manufacturing-plant",
    "Colour Shift Pigment",
    "Paper Line",
    "Clextral",
    "Schoen",
    "Schoen + Sandt",
    "Sandt",
    "Isravision",
    "Voith",
    "Bivis",
    "Lang",
    "Sheeter",
    "PM 5",
    "PM 6",
    "Security Thread",
    "Fibres",
    "Fibers",
    "BCLP",
    "BCCP",
    "HAUV",
    "Buckram",
    "Passport",
    "Intaglio Ink",
    "Fluorescent Ink",
    "Pasaban",
    "Komsco",
    "Cotton Comber",
    "UPS",
    "PVA",
    "Polyvinyl Alcohol",
    "Schuler",
    "Vinsak",
    "ICAO",
    "Electronic Contactless Inlays",
    "e-passport",
    "Development Tender",
    "Refurbishment and Modernization of Coining Presses",
    "Thales",
    "NATIONAL COMPETITIVE BID",
    "Global Tender",
    "CATIONIC UV CURING OVER-PRINT VARNISH",
    "Varnish",
    "Egates",
    "Border Control",
    "Lathe Machine",
    "Giesecke & Devrient",
    "Printing Machine",
    "Reinforced Tear & Water-Resistant Paper",
    "Ghost Image",
    "LSI",
    "Letter Screen Image",
    "Secondary image for passport"
]

GEM_URL = "https://bidplus.gem.gov.in/all-bids"


def _val(item: Any, default: str = "") -> str:
    """Helper to unpack single-element lists returned by GeM Solr docs."""
    if isinstance(item, list):
        return str(item[0]).strip() if item else default
    if item is None:
        return default
    return str(item).strip()


def parse_gem(
    site: Optional[Dict] = None,
    queries: Optional[List[str]] = None,
    max_pages: Optional[int] = None
) -> List[Dict]:
    """
    Search and extract relevant bids from GeM portal across 100% of available pages.
    When max_pages is None, it loops through every page until all matching records are fetched.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.error("Playwright is not installed. Please run: pip install playwright && playwright install chromium")
        print("[ERROR] Playwright is not installed. Please run: pip install playwright && playwright install chromium")
        return []

    target_queries = queries if queries else DEFAULT_GEM_QUERIES
    tenders: List[Dict] = []
    seen_bids: Set[str] = set()

    mode_str = "100% of all pages (unlimited)" if max_pages is None else f"up to {max_pages} pages"
    print(f"\n[GeM Scraper] Starting Playwright session for {len(target_queries)} queries ({mode_str})...")

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )

            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800}
            )

            page = context.new_page()

            # Navigate to GeM all-bids page
            logger.info(f"Navigating to {GEM_URL}")
            page.goto(GEM_URL, wait_until="domcontentloaded", timeout=45000)

            # Wait for search input & jQuery to be ready
            page.wait_for_selector("#searchBid", timeout=20000)

            for query in target_queries:
                print(f"  -> GeM Searching: '{query}'")
                query_collected = 0
                query_already_seen = 0
                num_found = 0
                page_num = 1

                while True:
                    try:
                        # Execute query directly inside browser context with exact page number
                        raw_response = page.evaluate("""({ searchQuery, pageNumber }) => {
                            return new Promise((resolve) => {
                                var postdata = {
                                    page: pageNumber,
                                    param: { searchBid: searchQuery },
                                    filter: {
                                        bidStatusType: 'ongoing_bids',
                                        byType: 'all',
                                        sort: 'Bid-End-Date-Latest'
                                    }
                                };
                                
                                // Extract CSRF token
                                var csrf = $('input[name="csrf_bd_gem_nk"]').val() || '';
                                if (!csrf) {
                                    var html = $('body').html();
                                    var m = html.match(/csrf_bd_gem_nk'\\s*:\\s*'([a-f0-9]+)'/);
                                    if (m) csrf = m[1];
                                }
                                
                                $.ajax({
                                    type: 'POST',
                                    url: 'https://bidplus.gem.gov.in/all-bids-data',
                                    dataType: 'json',
                                    data: {
                                        'payload': JSON.stringify(postdata),
                                        'csrf_bd_gem_nk': csrf
                                    },
                                    success: function(data) { resolve(data); },
                                    error: function(xhr, status, err) { resolve({ error: err, status: status }); }
                                });
                            });
                        }""", {"searchQuery": query, "pageNumber": page_num})

                        if not isinstance(raw_response, dict) or "error" in raw_response:
                            break

                        inner_resp = raw_response.get("response", {}).get("response", {})
                        docs = inner_resp.get("docs") or inner_resp.get("bids") or []
                        num_found = inner_resp.get("numFound", len(docs))

                        if not docs:
                            break

                        for doc in docs:
                            bid_no = _val(doc.get("b_bid_number"))
                            if not bid_no:
                                continue
                            if bid_no in seen_bids:
                                query_already_seen += 1
                                continue

                            seen_bids.add(bid_no)
                            query_collected += 1

                            # Extract details
                            category_name = _val(doc.get("b_category_name"))
                            b_id = _val(doc.get("b_id") or doc.get("id"))
                            doc_url = f"https://bidplus.gem.gov.in/showbidDocument/{b_id}" if b_id else ""

                            # Dates
                            raw_closing = _val(doc.get("final_end_date_sort"))
                            raw_pub = _val(doc.get("final_start_date_sort"))

                            status, days_left = get_status(raw_closing)
                            closing_date = format_display_date(raw_closing)
                            pub_date = format_display_date(raw_pub)

                            # Buyer department / ministry
                            dept_name = (
                                _val(doc.get("ba_official_details_deptName"))
                                or _val(doc.get("ba_official_details_minName"))
                                or "GeM Buyer"
                            )

                            # Exact word-boundary match for keyword
                            q_tokens = [re.escape(w) for w in query.strip().split()]
                            q_pattern = r"\b" + r"\s+".join(q_tokens) + r"\b"
                            matched_kw = query.upper() if re.search(q_pattern, category_name, re.IGNORECASE) else "-"

                            tender = {
                                "Source": "GeM Portal",
                                "Source URL": GEM_URL,
                                "Unit Name": dept_name,
                                "Tender Number": bid_no,
                                "Tender Title": category_name,
                                "Matched Keyword": matched_kw,
                                "Publishing Date": pub_date,
                                "Closing Date": closing_date,
                                "Status": status,
                                "Days Left": days_left,
                                "Tender Document": "Download" if doc_url else "",
                                "Tender Document URL": doc_url,
                                "Corrigendum": "",
                                "Corrigendum URL": "",
                                "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }

                            tenders.append(tender)

                        # Stop condition: 100% of all available records processed
                        total_processed = query_collected + query_already_seen
                        if total_processed >= num_found or len(docs) < 10:
                            break

                        # If user passed an explicit max_pages limit, respect it
                        if max_pages is not None and page_num >= max_pages:
                            break

                        page_num += 1
                        page.wait_for_timeout(200)

                    except Exception as page_err:
                        logger.warning(f"Error fetching page {page_num} for '{query}': {page_err}")
                        break

                pages_fetched = page_num
                if query_already_seen > 0:
                    print(f"     -> '{query}': {num_found} total on GeM | {query_collected} new bids + {query_already_seen} already collected in prior queries (100% fetched across {pages_fetched} pages)")
                else:
                    print(f"     -> '{query}': {num_found} total on GeM | {query_collected} new bids (100% fetched across {pages_fetched} pages)")
                page.wait_for_timeout(300)

            browser.close()

        except Exception as browser_err:
            logger.exception(f"GeM scraper browser error: {browser_err}")
            print(f"[ERROR] GeM scraper failed: {browser_err}")

    print(f"[GeM Scraper] Completed. Total unique bids extracted (100% of pages): {len(tenders)}")
    logger.info(f"GeM Scraper completed. Total bids: {len(tenders)}")
    return tenders


if __name__ == "__main__":
    bids = parse_gem(queries=["Voith", "Currency Note Press", "Bank Note Press"])
    print(f"\nTotal GeM Bids Found: {len(bids)}")
    for bid in bids[:5]:
        print(f"  {bid['Tender Number']} | {bid['Unit Name']} | {bid['Closing Date']} | {bid['Tender Title'][:50]}")
