"""
supabase_storage.py

Supabase database storage layer for the Tender Monitoring System.
Interacts with Supabase using the official Supabase Python Client (PostgREST API).
"""

from datetime import datetime
from typing import List, Dict, Set, Optional
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE, logger


class SupabaseStorage:
    """Manages reading and storing tenders in a Supabase table."""

    def __init__(self, url: Optional[str] = None, key: Optional[str] = None, table_name: Optional[str] = None):
        self.url = url or SUPABASE_URL
        self.key = key or SUPABASE_KEY
        self.table_name = table_name or SUPABASE_TABLE or "tenders"

        if not self.url or not self.key:
            logger.warning(
                "Supabase URL or Key is missing. Please set SUPABASE_URL and SUPABASE_KEY in .env"
            )
            self.client: Optional[Client] = None
        else:
            try:
                self.client = create_client(self.url, self.key)
                logger.info(f"Supabase client initialized for table '{self.table_name}'")
            except Exception as e:
                logger.exception(f"Failed to initialize Supabase client: {e}")
                self.client = None

    def is_configured(self) -> bool:
        """Check if Supabase credentials are configured."""
        return self.client is not None

    def test_connection(self) -> bool:
        """Test whether the Supabase connection and table access are working."""
        if not self.is_configured():
            print("[ERROR] Supabase is not configured. Check SUPABASE_URL and SUPABASE_KEY in .env.")
            return False

        try:
            # Query at most 1 row to verify table access
            response = self.client.table(self.table_name).select("id", count="exact").limit(1).execute()
            count = response.count if hasattr(response, "count") else len(response.data)
            print(f"[SUCCESS] Connected to Supabase table '{self.table_name}'. Existing records: {count}")
            logger.info(f"Supabase connection successful. Table: {self.table_name}")
            return True
        except Exception as e:
            print(f"[ERROR] Supabase connection test failed: {e}")
            logger.exception(f"Supabase connection test failed: {e}")
            return False

    def init_storage(self) -> None:
        """Verify table connectivity on startup."""
        if self.is_configured():
            self.test_connection()
        else:
            print("[WARN] Supabase credentials not found in .env. Falling back or pausing database sync.")

    def get_existing_tenders(self) -> Dict[str, Dict]:
        """
        Fetch all existing tender records from Supabase keyed by (Source|Tender Number).
        Returns a dictionary mapping 'Source|Tender Number' -> record dict.
        Allows O(1) membership checks ('key in existing') and state delta comparison.
        """
        existing: Dict[str, Dict] = {}

        if not self.is_configured():
            logger.warning("Supabase client not configured; returning empty existing map.")
            return existing

        page_size = 1000
        start = 0

        try:
            while True:
                response = (
                    self.client.table(self.table_name)
                    .select("source, tender_number, closing_date, corrigendum, corrigendum_url, days_left")
                    .range(start, start + page_size - 1)
                    .execute()
                )

                rows = response.data or []
                for row in rows:
                    source = (row.get("source") or "").strip()
                    tender_no = (row.get("tender_number") or "").strip()
                    if source and tender_no:
                        existing[f"{source}|{tender_no}"] = row

                if len(rows) < page_size:
                    break

                start += page_size

            print(f"Loaded {len(existing)} existing tenders from Supabase.")
            logger.info(f"Loaded {len(existing)} existing tenders from Supabase.")
            return existing

        except Exception as e:
            logger.exception(f"Failed to fetch existing tenders from Supabase: {e}")
            print(f"Error reading existing tenders from Supabase: {e}")
            return existing
            return existing

    def _format_record(self, tender: Dict) -> Dict:
        """Normalize a scraper tender dictionary into Supabase table columns."""
        return {
            "source": tender.get("Source") or tender.get("source") or "",
            "source_url": tender.get("Source URL") or tender.get("source_url") or "",
            "unit_name": tender.get("Unit Name") or tender.get("unit_name") or "",
            "tender_number": tender.get("Tender Number") or tender.get("tender_number") or "",
            "tender_title": tender.get("Tender Title") or tender.get("tender_title") or tender.get("title") or "",
            "matched_keyword": tender.get("Matched Keyword") or tender.get("matched_keyword") or "-",
            "publishing_date": tender.get("Publishing Date") or tender.get("publishing_date") or "",
            "closing_date": tender.get("Closing Date") or tender.get("closing_date") or "",
            "status": tender.get("Status") or tender.get("status") or "Active",
            "days_left": tender.get("Days Left") if tender.get("Days Left") is not None else tender.get("days_left"),
            "tender_document": tender.get("Tender Document") or tender.get("tender_document") or "",
            "tender_document_url": tender.get("Tender Document URL") or tender.get("tender_document_url") or "",
            "corrigendum": tender.get("Corrigendum") or tender.get("corrigendum") or "",
            "corrigendum_url": tender.get("Corrigendum URL") or tender.get("corrigendum_url") or "",
            "scraped_at": tender.get("Scraped At") or tender.get("scraped_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": datetime.utcnow().isoformat(),
        }

    def save_tenders(self, tenders: List[Dict], existing: Optional[Set[str]] = None) -> int:
        """
        Save/Upsert new tenders into the Supabase table in batches.
        Updates the `existing` set in place.
        """
        if not self.is_configured():
            logger.error("Cannot save to Supabase: client is not configured.")
            print("Cannot save to Supabase: client is not configured.")
            return 0

        if not tenders:
            print("No tenders to save.")
            return 0

        records_to_insert = []
        for tender in tenders:
            source = tender.get("Source") or tender.get("source") or ""
            tender_no = tender.get("Tender Number") or tender.get("tender_number") or ""
            key = f"{source}|{tender_no}"

            if existing is not None and key in existing:
                continue

            records_to_insert.append(self._format_record(tender))
            if existing is not None:
                existing.add(key)

        if not records_to_insert:
            print("All provided tenders already exist in database.")
            return 0

        batch_size = 100
        inserted_count = 0

        for i in range(0, len(records_to_insert), batch_size):
            batch = records_to_insert[i : i + batch_size]
            try:
                # Upsert on (source, tender_number) conflict to prevent duplicate primary keys
                self.client.table(self.table_name).upsert(
                    batch,
                    on_conflict="source,tender_number"
                ).execute()
                inserted_count += len(batch)
                logger.info(f"Saved batch of {len(batch)} tenders to Supabase.")
            except Exception as e:
                logger.exception(f"Failed to insert batch {i // batch_size + 1} into Supabase: {e}")
                print(f"Error inserting batch into Supabase: {e}")

        print(f"Successfully saved {inserted_count} tenders to Supabase.")
        return inserted_count

    def upsert_tenders(self, tenders: List[Dict]) -> int:
        """
        Upsert updated tenders (e.g. with new corrigenda or date extensions) into Supabase.
        """
        if not self.is_configured():
            logger.error("Cannot upsert to Supabase: client is not configured.")
            return 0

        if not tenders:
            return 0

        records_to_upsert = [self._format_record(t) for t in tenders]
        batch_size = 100
        updated_count = 0

        for i in range(0, len(records_to_upsert), batch_size):
            batch = records_to_upsert[i : i + batch_size]
            try:
                self.client.table(self.table_name).upsert(
                    batch,
                    on_conflict="source,tender_number"
                ).execute()
                updated_count += len(batch)
                logger.info(f"Upserted batch of {len(batch)} updated tenders to Supabase.")
            except Exception as e:
                logger.exception(f"Failed to upsert batch {i // batch_size + 1} into Supabase: {e}")
                print(f"Error upserting batch into Supabase: {e}")

        print(f"Successfully updated {updated_count} tender records in Supabase.")
        return updated_count

    # Backwards-compatible alias for existing code calling save_to_sheet
    def save_to_sheet(self, tenders: List[Dict], existing: Optional[Set[str]] = None) -> int:
        """Alias for save_tenders to provide drop-in compatibility with GoogleSheet."""
        return self.save_tenders(tenders, existing)

    def create_sheet(self) -> None:
        """Alias for init_storage to provide drop-in compatibility with GoogleSheet."""
        self.init_storage()
