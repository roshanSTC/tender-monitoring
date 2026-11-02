"""
compare.py

Compares scraped tenders with existing tenders to detect:
1. Brand new tenders.
2. Corrigenda and date extensions on existing tenders.
"""

from config import logger
from utils.status import parse_date


class TenderComparer:

    def __init__(self, existing_tenders):
        self.existing_tenders = existing_tenders

    def get_new_tenders(self, scraped_tenders):
        new_tenders = []

        for tender in scraped_tenders:
            source = tender.get("Source", "").strip()
            tender_no = tender.get("Tender Number", "").strip()

            if not tender_no:
                logger.warning("Tender Number missing.")
                continue

            unique_key = f"{source}|{tender_no}"

            if unique_key in self.existing_tenders:
                logger.info(f"Already exists : {unique_key}")
                continue

            new_tenders.append(tender)

        logger.info(f"New Tenders : {len(new_tenders)}")
        return new_tenders

    def get_corrigendum_tenders(self, scraped_tenders):
        """
        Identify existing tenders that have newly issued corrigenda or date extensions.
        Returns a list of updated tender dictionaries with delta details attached.
        """
        corrigendum_tenders = []
        if not isinstance(self.existing_tenders, dict):
            return corrigendum_tenders

        for tender in scraped_tenders:
            source = tender.get("Source", "").strip()
            tender_no = tender.get("Tender Number", "").strip()
            if not tender_no:
                continue

            unique_key = f"{source}|{tender_no}"
            if unique_key not in self.existing_tenders:
                continue  # New tender, handled by get_new_tenders

            prev = self.existing_tenders[unique_key]
            prev_close = (prev.get("closing_date") or "").strip()
            new_close = (tender.get("Closing Date") or "").strip()

            prev_corr_url = (prev.get("corrigendum_url") or "").strip()
            new_corr_url = (tender.get("Corrigendum URL") or "").strip()

            prev_corr_text = (prev.get("corrigendum") or "").strip()
            new_corr_text = (tender.get("Corrigendum") or "").strip()

            is_changed = False
            change_reasons = []

            # Check 1: New or changed Corrigendum URL / Document
            if new_corr_url and new_corr_url != prev_corr_url:
                is_changed = True
                change_reasons.append("New Corrigendum Document Published")
            elif new_corr_text and new_corr_text != prev_corr_text:
                is_changed = True
                change_reasons.append(f"Corrigendum Updated: {new_corr_text}")

            # Check 2: Closing Date Extension
            if prev_close and new_close and prev_close != new_close:
                dt_prev = parse_date(prev_close)
                dt_new = parse_date(new_close)
                if dt_prev and dt_new:
                    if dt_new > dt_prev:
                        diff_days = (dt_new.date() - dt_prev.date()).days
                        is_changed = True
                        change_reasons.append(f"Closing Date Extended (+{diff_days} days)")
                    elif dt_new < dt_prev:
                        is_changed = True
                        change_reasons.append("Closing Date Revised")
                else:
                    is_changed = True
                    change_reasons.append("Closing Date Revised")

            if is_changed:
                updated_tender = dict(tender)
                updated_tender["Is Corrigendum"] = True
                updated_tender["Change Details"] = " | ".join(change_reasons)
                updated_tender["Previous Closing Date"] = prev_close
                updated_tender["New Closing Date"] = new_close
                updated_tender["Previous Corrigendum URL"] = prev_corr_url
                corrigendum_tenders.append(updated_tender)
                logger.info(f"Corrigendum detected for {unique_key}: {' | '.join(change_reasons)}")

        logger.info(f"Corrigendum Tenders Detected: {len(corrigendum_tenders)}")
        return corrigendum_tenders
