from datetime import datetime
from urllib.parse import urljoin
from config import logger

from bs4 import BeautifulSoup
from utils.date_utils import normalize_tender_date


def parse_noida_page(html, site):

        soup = BeautifulSoup(html, "lxml")

        articles = soup.find_all("article")

        tenders = []

        for article in articles:

            title = ""
            title_link = article.find("h2")

            if title_link:
                a = title_link.find("a")
                if a:
                    title = a.get_text(" ", strip=True)

            content = article.find("div", class_="entry-content")

            if not content:
                continue

            values = {}

            for p in content.find_all("p"):

                text = p.get_text(" ", strip=True)

                if ":" not in text:
                    continue

                key, value = text.split(":", 1)

                values[key.strip()] = value.strip()

            # Download link
            tender_doc = ""
            tender_doc_url = ""

            downloads = content.find("div")

            if downloads:
                a = downloads.find("a")

                if a:
                    tender_doc = a.get_text(" ", strip=True)
                    tender_doc_url = urljoin(site["url"], a.get("href", ""))

            # Corrigendum
            corr_text = ""
            corr_url = ""

            corr_div = None

            for div in content.find_all("div"):

                if "Corrigendum" in div.get_text():

                    corr_div = div
                    break

            if corr_div:

                a = corr_div.find("a")

                if a:
                    corr_text = a.get_text(" ", strip=True)
                    corr_url = urljoin(site["url"], a.get("href", ""))

            tender = {

                "Source": site["name"],

                "Source URL": site["url"],

                "Unit Name": values.get("Unit", ""),

                "Tender Number": values.get("Tender Number", ""),

                "Tender Title": values.get("Tender Ttile", values.get("Tender Title", title)),

                "Publishing Date": normalize_tender_date(values.get("Publishing Date", "")),

                "Closing Date": normalize_tender_date(values.get("Closing Date", "")),

                "Tender": tender_doc,

                "Tender URL": tender_doc_url,

                "Corrigendum": corr_text,

                "Corrigendum URL": corr_url
            }

            if tender["Tender Number"]:
                tenders.append(tender)

        logger.info(f"{site['name']} -> Parsed {len(tenders)} tenders")

        return tenders
 