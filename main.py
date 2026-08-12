"""
main.py

Main entry point for the SPMCIL Tender Monitoring System.
"""


from database.connection import SessionLocal
from services.active_tenders import count_active_tenders
from scraper.scraper import TenderScraper
from services.compare import TenderComparer
from services.filter import TenderFilter
from notifications.mailer import TenderMailer
from services.tender_repository import TenderRepository
from services.tender_sync_service import TenderSyncService
from storage.google_sheet import GoogleSheet
from services.tender_service import save_new_tenders
from services.notification_service import (
    prepare_batch_notifications,
    create_batch_in_app_notifications,
    send_batch_emails,
)
from config import logger, TENDER_SITES
sheet = GoogleSheet()
db = SessionLocal()


def main():

    print("=" * 70)
    print("        Tender Monitoring System")
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
                
                # Debug only for BRBNMPL
                if site["name"] == "BRBNMPL":

                    seen = set()

                    for tender in tenders:

                        key = f"{tender['Source']}|{tender['Tender Number']}"

                        if key in seen:
                            print(f"DUPLICATE FROM PARSER: {key}")

                        seen.add(key)

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
        # Create Excel if not exists
        # ---------------------------------------------------

        # sheet.create_sheet()

        # ---------------------------------------------------
        # Existing tenders
        # ---------------------------------------------------

        # existing = TenderRepository.get_existing_tenders(db)

        # print(f"Existing Tenders : {len(existing)}")

        # ---------------------------------------------------
        # Compare
        # ---------------------------------------------------

        # comparer = TenderComparer(existing)

        # new_tenders = comparer.get_new_tenders(all_tenders)

        # print(f"New Tenders : {len(new_tenders)}")
        
        # print("\nSaving tenders to PostgreSQL...")

        # new_tenders = save_new_tenders(all_tenders)
        
        # print("DEBUG first new tender:")
        # print(new_tenders[0] if new_tenders else "No new tenders")

        # print(f"New Tenders : {len(new_tenders)}")
        
        print("\nSynchronizing tenders...\n")

        sync_result = TenderSyncService.sync(
            db=db,
            scraped_tenders=all_tenders,
        )

        sync_summary = sync_result["summary"]

        new_tenders = sync_result["inserted"]

        updated_tenders = sync_result["updated"]

        corrigendums = sync_result["corrigendums"]

        print("=" * 60)
        print("Synchronization Summary")
        print("=" * 60)
        print(f"New Tenders     : {sync_summary['new_tenders']}")
        print(f"Updated Tenders : {sync_summary['updated_tenders']}")
        print(f"Corrigendums    : {sync_summary['corrigendums']}")
        print(f"Unchanged       : {sync_summary['unchanged']}")
        print("=" * 60)
        
        
        # ---------------------------------------------------
        # Batch Notifications
        # ---------------------------------------------------

        if new_tenders:

            print("\nProcessing batch notifications...")

            try:

                # ---------------------------------------------
                # Find users matching the new tenders
                # ---------------------------------------------

                from services.matching_service import (
                    get_matching_users_for_tenders
                )

                matched_users = get_matching_users_for_tenders(
                    new_tenders
                )

                print(
                    f"Matched Users : {len(matched_users)}"
                )

                # ---------------------------------------------
                # Prepare notification batches
                # ---------------------------------------------

                batches = prepare_batch_notifications(
                    matched_users,
                    new_tenders
                )

                print(
                    f"Notification Batches : {len(batches)}"
                )

                # ---------------------------------------------
                # Create in-app notifications
                # ---------------------------------------------

                in_app_results = (
                    create_batch_in_app_notifications(
                        batches
                    )
                )

                print(
                    f"In-App Notifications : "
                    f"{len(in_app_results)}"
                )

                # ---------------------------------------------
                # Send batch emails
                # ---------------------------------------------

                email_results = send_batch_emails(
                    batches, in_app_results
                )

                print(
                    f"Batch Emails Processed : "
                    f"{len(email_results)}"
                )

                # ---------------------------------------------
                # Print results
                # ---------------------------------------------

                for result in email_results:

                    print(
                        f"Email notification for user "
                        f"{result['user_id']} : "
                        f"{result['email_sent']}"
                    )

            except Exception as notification_error:

                logger.exception(
                    f"Batch notification processing failed: "
                    f"{notification_error}"
                )

                print(
                    f"Batch notification processing failed: "
                    f"{notification_error}"
                )

        else:

            print(
                "\nNo new tenders. "
                "No notifications needed."
            )

        

        # ---------------------------------------------------
        # Filter
        # ---------------------------------------------------

        filtered_tenders = filter_obj.filter_by_title(new_tenders)

        print(
            f"Keyword Matched Tenders : {len(filtered_tenders)}"
        )
        
        
                
        
        # ---------------------------------------------------
        # Save new tenders
        # ---------------------------------------------------

        if new_tenders:

            # sheet.save_to_sheet(new_tenders, [])

            print("stored in sheet")

        else:

            print("No new tenders found.")
            
            
            
        #active tenders-------------------- 
        
        active_tenders, expired_tenders = count_active_tenders(
                all_tenders
            )   
        # symmary---------------------------
        
        summary = {
                "status": "SUCCESS",
                "total_websites": len(TENDER_SITES),
                "total_scraped": len(all_tenders),
                "active_tenders": active_tenders,
                "existing_tenders": 0,
                "new_tenders": len(new_tenders),
                "keyword_matches": len(filtered_tenders)
            }


        # ---------------------------------------------------
        # Email
        # ---------------------------------------------------

        if filtered_tenders:

            # mailer.send_email(filtered_tenders, summary)

            print("Email sent successfully.")

        else:

            # mailer.send_health_report(summary)

            print("Health report sent successfully.")

        logger.info("Application Finished Successfully")

        print("\nCompleted Successfully.")

        return {
            "success": True,
            "total_scraped": len(all_tenders),
            "new_tenders": len(new_tenders),
            "matched_tenders": len(filtered_tenders)
        }

    except Exception as e:

        logger.exception(
            "Application Failed",
            exc_info=True
        )

        print("\nApplication Failed")
        print("=" * 70)

        import traceback
        traceback.print_exc()

        print("=" * 70)

        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    main()