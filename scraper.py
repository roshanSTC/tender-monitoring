"""
scraper.py

Scrapes SPMCIL tenders and stores them in an Excel file.
"""

from datetime import datetime
from gc import get_stats
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin
from config import TENDER_SITES, logger


from datetime import datetime


def get_status(closing_date):

    try:
        closing = datetime.strptime(
            closing_date[:10],
            "%Y-%m-%d"
        ).date()

        today = datetime.today().date()

        days_left = (closing - today).days

        if days_left < 0:
            return "Expired", 0

        return "Active", days_left

    except Exception:
        return "Unknown", 0
    
    

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
    
    

#-----------------------------------------------------

    from urllib.parse import urljoin


    def  parse_corporate_table(self, html):

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

                "Tender Number": cols[2].get_text(strip=True),

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

            tenders.append(tender)

        logger.info(f"Fetched {len(tenders)} tenders")

        return tenders


    def parse_unit_table(self, html, site):

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

    # --------------------------------------------------------
    
    
    def parse_noida_page(self, html, site):

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

                "Publishing Date": values.get("Publishing Date", ""),

                "Closing Date": values.get("Closing Date", ""),

                "Tender Document": tender_doc,

                "Tender Document URL": tender_doc_url,

                "Corrigendum": corr_text,

                "Corrigendum URL": corr_url,

                "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            if tender["Tender Number"]:
                tenders.append(tender)

        logger.info(f"{site['name']} -> Parsed {len(tenders)} tenders")

        return tenders
    
    
    # --------------------------------------------------------

    def parse_brbnmpl(self, site):

        tenders = []
        seen = set()

        response = requests.get(site["url"], timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")


        for table in tables:

            rows = table.find_all("tr")

            if len(rows) < 2:
                continue

            header_text = rows[0].get_text(" ", strip=True).lower()

            if "tender no" not in header_text:
                continue


            for row in rows[1:]:

                cols = row.find_all(["td", "th"])

                if len(cols) < 5:
                    continue

                tender_no = cols[1].get_text(strip=True)

                if not tender_no:
                    continue

                key = f"BRBNMPL|{tender_no}"

                if key in seen:
                    continue

                seen.add(key)

                open_date = cols[2].get_text(strip=True)

                title_col = cols[3]

                closing_date = cols[4].get_text(strip=True)

                title = title_col.get_text(" ", strip=True)

                tender_url = ""

                link = title_col.find("a")

                if link and link.get("href"):
                    tender_url = urljoin(site["url"], link["href"])

                tenders.append({

                    "Source": "BRBNMPL",
                    "Source URL": site["url"],
                    "Unit Name": "BRBNMPL",
                    "Tender Number": tender_no,
                    "Tender Title": title,
                    "Publishing Date": open_date,
                    "Closing Date": closing_date,
                    "Tender Document": "Download" if tender_url else "",
                    "Tender Document URL": tender_url,
                    "Corrigendum": "",
                    "Corrigendum URL": "",
                    "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                })

            # Stop after parsing the first valid tender table
            break


        return tenders

    def parse_bnpm(self, site):

        tenders = []

        response = requests.get(site["url"], timeout=30)

        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        tables = soup.find_all("table")

        for table in tables:

            rows = table.find_all("tr")

            if len(rows) < 2:
                continue

            header_text = rows[0].get_text(" ", strip=True).lower()

            if "tender details" not in header_text:
                continue

            for row in rows[1:]:

                cols = row.find_all("td")

                if len(cols) < 3:
                    continue

                details_col = cols[0]

                opening_date = cols[1].get_text(strip=True)

                closing_date = cols[2].get_text(strip=True)

                detail_text = details_col.get_text(" ", strip=True)

                # First line is usually tender number/title
                lines = [l.strip() for l in detail_text.splitlines() if l.strip()]

                tender_no = lines[0] if lines else ""

                title = " ".join(lines[1:]) if len(lines) > 1 else tender_no

                tender_url = ""

                corrigendum_url = ""

                links = details_col.find_all("a")

                for a in links:

                    href = a.get("href")

                    if not href:
                        continue

                    full_url = urljoin(site["url"], href)

                    text = a.get_text(strip=True).lower()

                    if "corrigendum" in text:

                        corrigendum_url = full_url

                    else:

                        tender_url = full_url

                tenders.append({

                    "Source": "BNPM India",
                    "Source URL": site["url"],
                    "Unit Name": "BNPM India",
                    "Tender Number": tender_no,
                    "Tender Title": title,
                    "Publishing Date": opening_date,
                    "Closing Date": closing_date,
                    "Tender Document": "Download" if tender_url else "",
                    "Tender Document URL": tender_url,
                    "Corrigendum": "Corrigendum" if corrigendum_url else "",
                    "Corrigendum URL": corrigendum_url,
                    "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                })

        return tenders

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
            tenders = self.parse_corporate_table(html)

        elif site["name"] == "IGM Noida":
            tenders = self.parse_noida_page(html, site)
        
        elif site["type"] == "brbnmpl":
            return self.parse_brbnmpl(site)

        elif site["type"] == "bnpm":
            return self.parse_bnpm(site)

        else:
            tenders = self.parse_unit_table(html, site)

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