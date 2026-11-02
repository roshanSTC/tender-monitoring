"""
main.py

Main entry point for the SPMCIL Tender Monitoring System with Supabase Storage.
"""

from services.active_tenders import count_active_tenders
from scraper.scraper import TenderScraper
from services.compare import TenderComparer
from services.filter import TenderFilter
from notifications.mailer import TenderMailer
from storage.supabase_storage import SupabaseStorage
from config import logger, TENDER_SITES

db = SupabaseStorage()


def main():

    print("=" * 70)
    print("        Tender Monitoring System (Supabase Enabled)")
    print("=" * 70)

    logger.info("Application Started")

    scraper = TenderScraper()
    mailer = TenderMailer()
    filter_obj = TenderFilter()

    try:

        # ---------------------------------------------------
        # Scrape all websites
        # ---------------------------------------------------

        all_tenders = []

        print("\nScraping Websites...\n")

        for site in TENDER_SITES:

            try:

                print(f"Scraping : {site['name']}")

                tenders = scraper.scrape(site)

                print(f"Found {len(tenders)} tenders")

                logger.info(
                    f"{site['name']} -> {len(tenders)} tenders scraped"
                )

                all_tenders.extend(tenders)

            except Exception as e:

                logger.exception(
                    f"Failed to scrape {site['name']} : {e}"
                )

                print(f"Failed : {site['name']}")
                print(f"Error Type : {type(e).__name__}")
                print(f"Error      : {e}")

        print("\n---------------------------------------")
        print(f"Total Scraped : {len(all_tenders)}")
        print("---------------------------------------")

        # ---------------------------------------------------
        # Initialize Supabase Storage
        # ---------------------------------------------------

        db.init_storage()

        # ---------------------------------------------------
        # Existing tenders from Supabase
        # ---------------------------------------------------

        existing = db.get_existing_tenders()

        print(f"Existing Tenders in Database : {len(existing)}")

        # ---------------------------------------------------
        # Compare (Deduplicate & Corrigendum Detection)
        # ---------------------------------------------------

        comparer = TenderComparer(existing)

        new_tenders = comparer.get_new_tenders(all_tenders)
        corrigendum_tenders = comparer.get_corrigendum_tenders(all_tenders)

        print(f"New Tenders : {len(new_tenders)}")
        print(f"Corrigenda / Extended Tenders : {len(corrigendum_tenders)}")

        # ---------------------------------------------------
        # Filter by Keywords
        # ---------------------------------------------------

        filtered_tenders = filter_obj.filter_by_title(new_tenders)
        filtered_corrigenda = filter_obj.filter_by_title(corrigendum_tenders)

        print(
            f"Keyword Matched New Tenders : {len(filtered_tenders)}"
        )
        print(
            f"Keyword Matched Corrigenda : {len(filtered_corrigenda)}"
        )

        # ---------------------------------------------------
        # Save new tenders and update corrigenda in Supabase
        # ---------------------------------------------------

        if new_tenders:

            saved_count = db.save_tenders(new_tenders, existing)

            print(f"Database updated successfully. ({saved_count} tenders stored)")

        else:

            print("No new tenders to store in database.")

        if corrigendum_tenders:

            updated_count = db.upsert_tenders(corrigendum_tenders)

            print(f"Database corrigenda updated. ({updated_count} tender records refreshed)")

        # ---------------------------------------------------
        # Active tenders
        # ---------------------------------------------------

        active_tenders, expired_tenders = count_active_tenders(
            all_tenders
        )

        # ---------------------------------------------------
        # Summary
        # ---------------------------------------------------

        summary = {
            "status": "SUCCESS",
            "total_websites": len(TENDER_SITES),
            "total_scraped": len(all_tenders),
            "active_tenders": active_tenders,
            "existing_tenders": len(existing),
            "new_tenders": len(new_tenders),
            "corrigenda_count": len(filtered_corrigenda),
            "keyword_matches": len(filtered_tenders) + len(filtered_corrigenda)
        }

        # ---------------------------------------------------
        # Email Notifications
        # ---------------------------------------------------

        if filtered_tenders or filtered_corrigenda:

            mailer.send_email(filtered_tenders, summary, corrigenda=filtered_corrigenda)

            print("Email alert sent successfully.")

        else:

            mailer.send_health_report(summary)

            print("Daily health report sent successfully.")

        logger.info("Application Finished Successfully")

        print("\nCompleted Successfully.")

        return {
            "success": True,
            "total_scraped": len(all_tenders),
            "new_tenders": len(new_tenders),
            "matched_tenders": len(filtered_tenders)
        }

    except Exception as e:

        logger.exception(e)

        print(f"\nApplication Failed : {e}")

        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    main()
