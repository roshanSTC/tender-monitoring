"""
filter.py

Filters tenders based on keywords using exact word/phrase boundary matching.
"""

import re
from config import KEYWORDS, logger


class TenderFilter:

    def __init__(self):
        # Precompile exact word-boundary regex for each keyword in KEYWORDS
        self.compiled_keywords = []
        for kw in KEYWORDS:
            cleaned = kw.strip()
            if not cleaned:
                continue
            tokens = [re.escape(w) for w in cleaned.split()]
            # \b matches word boundary (spaces, punctuation, start/end of string)
            pattern = r"\b" + r"\s+".join(tokens) + r"\b"
            self.compiled_keywords.append((re.compile(pattern, re.IGNORECASE), cleaned))

    def filter_by_title(self, tenders):
        matched = []

        for tender in tenders:
            title = tender.get("Tender Title", "")
            if not title:
                continue

            for regex, orig_kw in self.compiled_keywords:
                if regex.search(title):
                    tender["Matched Keyword"] = orig_kw.upper()
                    matched.append(tender)
                    logger.info(
                        f"Exact Match '{orig_kw}' -> {tender.get('Tender Number')}"
                    )
                    break

        logger.info(
            f"{len(matched)} tenders matched keywords with exact word boundaries."
        )
        return matched
