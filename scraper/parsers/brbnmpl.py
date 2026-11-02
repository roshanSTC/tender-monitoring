from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests


def parse_brbnmpl(site):

        tenders = []
        seen = set()

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        response = requests.get(site["url"], headers=headers, timeout=30)
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

                corr_url = ""
                corr_text = ""
                all_links = title_col.find_all("a")
                for l in all_links:
                    href = l.get("href", "")
                    ltxt = l.get_text(" ", strip=True).lower()
                    full_link = urljoin(site["url"], href) if href else ""
                    if "corrigendum" in ltxt or "corrigendum" in href.lower() or "extension" in ltxt:
                        corr_url = full_link
                        corr_text = l.get_text(" ", strip=True) or "Corrigendum"
                    elif not tender_url and href:
                        tender_url = full_link
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
                    "Corrigendum": corr_text,
                    "Corrigendum URL": corr_url,
                    "Scraped At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                })

            # Stop after parsing the first valid tender table
            break


        return tenders

