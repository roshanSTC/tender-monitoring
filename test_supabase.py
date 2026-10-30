"""
test_supabase.py

Quick verification script to test Supabase connectivity, credentials, and table access.
Run:
    python test_supabase.py
"""

from storage.supabase_storage import SupabaseStorage
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE


def main():
    print("=" * 60)
    print("           Supabase Connection Tester")
    print("=" * 60)

    masked_key = "(not set)"
    if SUPABASE_KEY:
        masked_key = f"...{SUPABASE_KEY[-8:]}" if len(SUPABASE_KEY) > 8 else "********"

    print(f"SUPABASE_URL   : {SUPABASE_URL or '(not set)'}")
    print(f"SUPABASE_KEY   : {masked_key}")
    print(f"SUPABASE_TABLE : {SUPABASE_TABLE}")
    print("-" * 60)

    storage = SupabaseStorage()

    if not storage.is_configured():
        print("[ERROR] Supabase is NOT configured. Please add SUPABASE_URL and SUPABASE_KEY to your .env file.")
        return

    print("Attempting to connect to Supabase...")
    success = storage.test_connection()

    if success:
        existing = storage.get_existing_tenders()
        print(f"[SUCCESS] Found {len(existing)} existing tenders in Supabase.")
        print("[SUCCESS] Supabase integration is ready for use!")
    else:
        print("[WARN] Could not connect. Ensure:")
        print("   1. You ran the SQL in 'supabase_schema.sql' in your Supabase SQL Editor.")
        print("   2. Your SUPABASE_URL and SUPABASE_KEY are correct.")
        print("   3. Your table name matches SUPABASE_TABLE ('tenders').")


if __name__ == "__main__":
    main()

