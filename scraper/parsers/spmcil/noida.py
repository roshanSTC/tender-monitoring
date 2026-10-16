"""
noida.py

Parser for IGM Noida tenders page (WordPress layout).
"""

from datetime import datetime
from urllib.parse import urljoin
from config import logger
from bs4 import BeautifulSoup
from utils.status import get_status


def parse_noida_page(html, site):
    """
    Parse tender articles from IGM Noida latest-tenders page.
    """
    soup = BeautifulSoup(html, "lxml")
    articles = soup.find_all("article")
    tenders = []

    for article in articles:
        # Title extraction from headline
        title = ""
        title_link = article.find("h2")
        if title_link:
            a = title_link.find("a")
            if a:
                title = a.get_text(" ", strip=True)
            else:
                title = title_link.get_text(" ", strip=True)

        # Content container: WordPress theme uses ast-excerpt-container
        content = (
            article.find("div", class_="ast-excerpt-container")
            or article.find("div", class_="entry-content")
            or article
        )

        values = {}
        for p in content.find_all("p"):
            text = p.get_text(" ", strip=True)
            if ":" not in text:
                continue
            key, value = text.split(":", 1)
            values[key.strip()] = value.strip()

        # Extract Tender Document and Corrigendum URLs from links
        tender_doc = ""
        tender_doc_url = ""
        corr_text = ""
        corr_url = ""

        for a in content.find_all("a"):
            href = a.get("href", "")
            if not href:
                continue

            link_text = a.get_text(" ", strip=True)
            full_url = urljoin(site["url"], href)
            lower_text = link_text.lower()
            lower_href = href.lower()

            # Identify Corrigendum vs Tender Document
            if "corrigendum" in lower_text or "corrigendum" in lower_href or "extension" in lower_text:
                if not corr_url:
                    corr_text = link_text or "Corrigendum"
                    corr_url = full_url
            else:
                if not tender_doc_url:
                    tender_doc = link_text or "Download"
                    tender_doc_url = full_url

        tender_no = values.get("Tender Number", "").strip()
        tender_title = values.get("Tender Ttile", values.get("Tender Title", title)).strip()
        pub_date = values.get("Publishing Date", "").strip()
        closing_date = values.get("Closing Date", "").strip()
        unit_name = values.get("Unit", site.get("name", "IGM Noida")).strip()

        status, days_left = get_status(closing_date)

        tender = {
            "Source": site.get("name", "IGM Noida"),
            "Source URL": site.get("url", ""),
            "Unit Name": unit_name,
            "Tender Number": tender_no,
            "Tender Title": tender_title,
            "Publishing Date": pub_date,
            "Closing Date": closing_date,
            "Status": status,
            "Days Left": days_left,
            "Tender Document": tender_doc,
            "Tender Document URL": tender_doc_url,
            "Corrigendum": corr_text,
            "Corrigendum URL": corr_url,
            "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if tender_no:
            tenders.append(tender)

    logger.info(f"{site['name']} -> Parsed {len(tenders)} tenders")
    return tenders