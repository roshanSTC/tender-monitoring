from datetime import datetime
import re
from urllib.parse import urljoin
from config import logger

from bs4 import BeautifulSoup
import requests


def parse_bnpm(site):
    
        tenders = []

        response = requests.get(
            site["url"],
            timeout=30,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/150.0.0.0 Safari/537.36"
                )
            }
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # --------------------------------------------------
        # Find BNPM tender table
        # --------------------------------------------------

        table = soup.find(
            "table",
            id="myTable"
        )

        if not table:

            print("BNPM table #myTable not found.")

            return tenders

        # --------------------------------------------------
        # Get ALL TD elements
        # --------------------------------------------------

        cells = table.find_all("td")


        if not cells:

            print("BNPM table contains no TD cells.")

            return tenders

        # --------------------------------------------------
        # BNPM structure
        #
        # 0 = S.No
        # 1 = Tender Details
        # 2 = Tender Fee
        # 3 = Opening Date
        # 4 = Closing Date
        # 5 = EMD
        # 6 = Type
        # 7 = Remarks
        #
        # So every tender = 8 TD cells
        # --------------------------------------------------

        columns_per_tender = 8

        total_tenders = len(cells) // columns_per_tender


        # --------------------------------------------------
        # Process every 8 cells
        # --------------------------------------------------

        for i in range(
            0,
            len(cells),
            columns_per_tender
        ):

            group = cells[
                i:i + columns_per_tender
            ]

            # Ignore incomplete group
            if len(group) < columns_per_tender:

                print(
                    f"BNPM incomplete group at "
                    f"cell {i}"
                )

                continue

            try:

                # --------------------------------------------------
                # Columns
                # --------------------------------------------------

                serial_no = group[0].get_text(
                    " ",
                    strip=True
                )

                details_col = group[1]

                tender_fee = group[2].get_text(
                    " ",
                    strip=True
                )

                opening_date = group[3].get_text(
                    " ",
                    strip=True
                )

                closing_date = group[4].get_text(
                    " ",
                    strip=True
                )

                emd = group[5].get_text(
                    " ",
                    strip=True
                )

                tender_type = group[6].get_text(
                    " ",
                    strip=True
                )

                remarks = group[7].get_text(
                    " ",
                    strip=True
                )

                # --------------------------------------------------
                # Get complete details text
                # --------------------------------------------------

                detail_text = details_col.get_text(
                    " ",
                    strip=True
                )

                # --------------------------------------------------
                # Extract Tender Number
                # --------------------------------------------------

                tender_no = ""

                # Supports:
                #
                # BNPM/LTE/160/2026-27
                # BNPM/OTE/159/2026-27
                # BNPM/GTE/498/2025-26
                # GEM/2026/B/7813208

                match = re.search(
                    r'\b(?:BNPM|GEM)/[A-Za-z0-9./-]+',
                    detail_text,
                    re.IGNORECASE
                )

                if match:

                    tender_no = match.group(0).strip()

                # --------------------------------------------------
                # Find all links
                # --------------------------------------------------

                links = details_col.find_all("a")

                tender_url = ""

                corrigendum_url = ""

                # --------------------------------------------------
                # Extract title
                # --------------------------------------------------

                title = ""

                if links:

                    # First normal anchor is generally the
                    # tender document and its text is the title.

                    title = links[0].get_text(
                        " ",
                        strip=True
                    )

                # --------------------------------------------------
                # Clean title
                # --------------------------------------------------

                # Remove PDF size such as:
                #
                # 3510.31KB
                # 6856.68KB

                title = re.sub(
                    r'\s*\d+(?:\.\d+)?\s*KB\b',
                    '',
                    title,
                    flags=re.IGNORECASE
                ).strip()

                # Remove accidental image text

                title = re.sub(
                    r'\s*imgsrc\s*=.*',
                    '',
                    title,
                    flags=re.IGNORECASE
                ).strip()

                # --------------------------------------------------
                # Extract URLs
                # --------------------------------------------------

                for link in links:

                    href = link.get("href")

                    if not href:

                        continue

                    full_url = urljoin(
                        site["url"],
                        href
                    )

                    link_text = link.get_text(
                        " ",
                        strip=True
                    ).lower()

                    href_lower = href.lower()

                    # Corrigendum

                    if (
                        "corrigendum" in link_text
                        or "corrigendum" in href_lower
                    ):

                        if not corrigendum_url:

                            corrigendum_url = full_url

                    else:

                        if not tender_url:

                            tender_url = full_url

                # --------------------------------------------------
                # Validate tender number
                # --------------------------------------------------

                if not tender_no:

                    print(
                        f"BNPM [{serial_no}] "
                        f"Could not identify tender number."
                    )

                    continue

                # --------------------------------------------------
                # Fallback title
                # --------------------------------------------------

                if not title:

                    title = detail_text

                    title = re.sub(
                        re.escape(tender_no),
                        "",
                        title,
                        flags=re.IGNORECASE
                    ).strip()

                # --------------------------------------------------
                # Create tender
                # --------------------------------------------------

                tender = {

                    "Source": "BNPM India",

                    "Source URL": site["url"],

                    "Unit Name": "BNPM India",

                    "Tender Number": tender_no,

                    "Tender Title": title,

                    "Publishing Date": opening_date,

                    "Closing Date": closing_date,

                    "Tender Document": (
                        "Download"
                        if tender_url
                        else ""
                    ),

                    "Tender Document URL": tender_url,

                    "Corrigendum": (
                        "Corrigendum"
                        if corrigendum_url
                        else ""
                    ),

                    "Corrigendum URL": corrigendum_url,

                    "Scraped At": datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                }

                tenders.append(tender)

            except Exception as e:

                print(
                    f"BNPM parsing failed at "
                    f"cell group {i}: {e}"
                )

                logger.exception(
                    f"BNPM parser error at group {i}"
                )

                continue

        # --------------------------------------------------
        # Remove duplicates
        # --------------------------------------------------

        unique_tenders = []

        seen = set()

        for tender in tenders:

            key = (
                f"{tender['Source']}|"
                f"{tender['Tender Number']}"
            )

            if key in seen:

                print(
                    f"DUPLICATE FROM BNPM PARSER: "
                    f"{key}"
                )

                continue

            seen.add(key)

            unique_tenders.append(tender)
   

        return unique_tenders

 